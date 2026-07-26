# 后端架构与前后端切换方案

## 版本

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| 1.0 | 2026-07-25 | — | 初始规范：定义前端轻量/后端完整切换机制、多项目后端服务分配 |

---

## 一、生态位映射

根据 `协作关系.md` 的三层工具链架构，当前各项目的生态位关系如下：

```
               他者的代价               个体的边界
             (沉默的墓地)             (界限体验·濒死)
                  │                         │
                  ▼                         ▼
             ┌──────────┐           ┌──────────────────┐
             │   card   │           │knowledge-navigator│
             │ 幸存者    │           │-react            │
             │ 航标信号   │           │(替代 cognitive-  │
             │           │           │ cards 生态位)     │
             └────┬─────┘           └───────┬──────────┘
                  │                         │
                  │    共享 Python 后端       │
                  └───────────┬─────────────┘
                              │
                              ▼
                   ┌──────────────────────┐
                   │     card & kn-react   │
                   │    Python Backend     │
                   │ (FastAPI, 统一数据层)  │
                   └──────────────────────┘

                              │
                              │  简化信号 + 注意力线索
                              ▼
                   ┌──────────────────────┐
                   │     coze-studio       │
                   │    Go Backend (暂用)   │
                   │ 沉浸润色工作流编排       │
                   └──────────────────────┘
```

### 关键说明

| 项目 | 生态位 | 后端方案 | 状态 |
|------|--------|----------|------|
| `knowledge-navigator-react` | 替代 `cognitive-cards` 的边界手感直觉路径 | Python FastAPI（规划中） | 当前纯前端，逐步迁移 |
| `card` | 幸存者航标信号路径 | Python FastAPI（规划中） | 与 kn-react 共享 |
| `coze-studio` | 沉浸润色工作流编排 | Go（现有） | 暂不变动 |

---

## 二、前端开关机制

### 2.1 概述

`knowledge-navigator-react` 作为纯前端子项目，所有功能当前均在前端内存中完成（Zustand Store + Utils 层）。引入后端后，需要一个**全局开关**，让前端可以自由切换：

- **轻量模式（lite）**：沿用当前的前端实现，所有操作在浏览器内存中完成
- **完整模式（pro）**：通过 HTTP 请求调用 Python 后端 API 完成操作

### 2.2 配置定义

```typescript
// src/config/backend.ts

export type BackendMode = 'lite' | 'pro'

export interface BackendConfig {
  /** 当前运行模式 */
  mode: BackendMode

  /** 完整后端的基础 URL（仅 pro 模式需要） */
  baseUrl: string

  /** 请求超时时间（毫秒，默认 10000） */
  timeout: number

  /** 请求重试次数（默认 1） */
  retryCount: number
}

export const defaultBackendConfig: BackendConfig = {
  mode: 'lite',
  baseUrl: 'http://localhost:8171',  // Python 后端端口
  timeout: 10000,
  retryCount: 1,
}
```

### 2.3 运行时开关

通过 URL 查询参数或 localStorage 覆盖模式：

```typescript
// src/config/backend.ts（续）

let _config: BackendConfig = { ...defaultBackendConfig }

export function getBackendConfig(): BackendConfig {
  return { ..._config }
}

export function setBackendConfig(partial: Partial<BackendConfig>): void {
  _config = { ..._config, ...partial }
  // 持久化到 localStorage
  localStorage.setItem('kn_backend_config', JSON.stringify(_config))
}

export function isProMode(): boolean {
  return _config.mode === 'pro'
}

/**
 * 初始化配置：优先级 localStorage > URL 参数 > 默认值
 */
export function initBackendConfig(): void {
  // 1. 尝试从 localStorage 恢复
  const saved = localStorage.getItem('kn_backend_config')
  if (saved) {
    try {
      const parsed = JSON.parse(saved)
      _config = { ..._config, ...parsed }
    } catch { /* 忽略 */ }
  }

  // 2. URL 参数覆盖（最高优先级）
  const params = new URLSearchParams(window.location.search)
  const modeParam = params.get('backend_mode')
  if (modeParam === 'lite' || modeParam === 'pro') {
    _config.mode = modeParam
  }
  const baseUrl = params.get('backend_url')
  if (baseUrl) {
    _config.baseUrl = baseUrl
  }
}
```

### 2.4 UI 切换入口

在**树形管理视图（TreeView）** 或**全局设置**中增加后端模式切换控件：

```
┌─────────────────────────────────────────────┐
│  后端模式                                    │
│                                             │
│  ○ 轻量模式（lite）（当前）   ● 完整模式（pro）             │
│    前端内存操作         请求 Python 后端       │
│                                             │
│  [后端地址] http://localhost:8171 ────────── │
│                                             │
│  [测试连接]  [保存设置]                       │
└─────────────────────────────────────────────┘
```

| 控件 | 说明 |
|------|------|
| 模式切换 Radio | `lite` / `pro` 二选一 |
| 后端地址输入框 | 仅 pro 模式可用，默认 `http://localhost:8171` |
| 测试连接按钮 | 发送 `GET /api/health` 验证连通性 |
| 保存设置按钮 | 写入 localStorage，下次启动自动恢复 |

---

## 三、适配层设计

### 3.1 架构

```
UI 组件 (React)
    │
    ▼
Store (Zustand)
    │
    ├── 轻量模式（lite）→ 直接操作 Utils / 共享数据源
    │
    └── 完整模式（pro）→ 通过 BackendAdapter 调用 REST API
                       │
                       ▼
                Python Backend (FastAPI)
                       │
                       ▼
                数据库 / 持久化存储
```

### 3.2 BackendAdapter 类

```typescript
// src/api/BackendAdapter.ts

import { getBackendConfig, isProMode } from '../config/backend'

export class BackendAdapter {
  private static instance: BackendAdapter

  static getInstance(): BackendAdapter {
    if (!this.instance) {
      this.instance = new BackendAdapter()
    }
    return this.instance
  }

  private get baseUrl(): string {
    return getBackendConfig().baseUrl
  }

  private get timeout(): number {
    return getBackendConfig().timeout
  }

  // ── 通用请求方法 ──

  async get<T>(path: string): Promise<T> {
    const url = `${this.baseUrl}${path}`
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), this.timeout)

    try {
      const resp = await fetch(url, {
        signal: controller.signal,
        headers: { 'Accept': 'application/json' },
      })
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}))
        throw new ApiError(resp.status, err.detail || resp.statusText)
      }
      return resp.json()
    } finally {
      clearTimeout(timer)
    }
  }

  async post<T>(path: string, body: unknown): Promise<T> {
    const url = `${this.baseUrl}${path}`
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), this.timeout)

    try {
      const resp = await fetch(url, {
        method: 'POST',
        signal: controller.signal,
        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}))
        throw new ApiError(resp.status, err.detail || resp.statusText)
      }
      return resp.json()
    } finally {
      clearTimeout(timer)
    }
  }

  async put<T>(path: string, body: unknown): Promise<T> { /* 同 post 但 method: PUT */ }
  async delete<T>(path: string): Promise<T> { /* 同 get 但 method: DELETE */ }
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}
```

### 3.3 Adapter 与 API 层集成

在已有的 `KnowledgeNavigatorAPI` 类中增加模式判断：

```typescript
// src/api/index.ts（增强）

import { BackendAdapter } from './BackendAdapter'
import { isProMode } from '../config/backend'

export class KnowledgeNavigatorAPI {
  private adapter = BackendAdapter.getInstance()

  // ── 示例：获取全部卡片 ──

  async getAllCards(): Promise<CognitiveCard[]> {
    if (isProMode()) {
      return this.adapter.get<CognitiveCard[]>('/api/cards')
    }
    // 轻量模式（lite）：直接操作 Store
    return useCardStore.getState().allCards
  }

  // ── 示例：创建卡片 ──

  async createCard(parentId?: string): Promise<ApiResult<CognitiveCard>> {
    if (isProMode()) {
      try {
        const card = await this.adapter.post<CognitiveCard>('/api/cards', { parent_id: parentId })
        return { ok: true, data: card }
      } catch (e) {
        return { ok: false, error: (e as Error).message }
      }
    }
    try {
      const card = useCardStore.getState().createCard(parentId)
      return { ok: true, data: card }
    } catch (e) {
      return { ok: false, error: (e as Error).message }
    }
  }

  // ── 示例：搜索（异步操作，完整模式（pro）自然适用） ──

  async search(query: string, mode?: MatchMode): Promise<MatchedCard[]> {
    if (isProMode()) {
      return this.adapter.post<MatchedCard[]>('/api/search', { query, mode })
    }
    // 轻量模式（lite）：调用 searchStore
    useSearchStore.getState().setQuery(query)
    if (mode) useSearchStore.getState().setMatchMode(mode)
    return useSearchStore.getState().matchedCards
  }
}
```

> **注意**：API 方法签名从同步改为 `async` 以兼容完整模式（pro）的异步请求。轻量模式（lite）下的同步操作包装为 `Promise.resolve()` 以统一调用方。

---

## 四、Python 后端 API 规划

### 4.1 定位

Python 后端为 `knowledge-navigator-react` 和 `card` 两个前端项目提供统一数据服务，使用 **FastAPI** 框架，端口 `8171`（与 cognitive-cards 原有端口 `8170` 错开）。

### 4.2 后端路由结构

```
Python Backend (FastAPI, port 8171)
│
├── /api/health                         健康检查
│
├── /api/cards                          认知卡片 CRUD
│   ├── GET    /                        list all
│   ├── POST   /                        create
│   ├── GET    /{id}                    get by id
│   ├── PUT    /{id}                    update fields
│   ├── DELETE /{id}                    delete (cascade)
│   ├── GET    /{id}/children           get children
│   ├── GET    /{id}/corpus             get corpus entries
│   ├── POST   /{id}/corpus             add corpus entry
│   ├── PUT    /{id}/corpus/{index}     update corpus entry
│   └── DELETE /{id}/corpus/{index}     remove corpus entry
│
├── /api/nodes                          导航节点 CRUD
│   ├── GET    /                        list all (with search: ?q=)
│   ├── POST   /                        create
│   ├── GET    /{id}                    get by id
│   ├── PUT    /{id}                    update fields
│   ├── DELETE /{id}                    delete (cascade)
│   ├── POST   /{id}/bind-card          bind card
│   ├── DELETE /{id}/bind-card/{cardId}  unbind card
│   ├── GET    /{id}/next               get next nodes (sorted)
│   ├── POST   /{id}/next               add next node ref
│   ├── PUT    /{id}/next/{targetId}    update next node ref
│   ├── DELETE /{id}/next/{targetId}    remove next node ref
│   ├── GET    /{id}/prev               get prev nodes
│   └── GET    /{id}/browse-history     get browse history
│
├── /api/graph                          导航图
│   ├── GET    /nodes                   all graph nodes
│   ├── GET    /edges                   all edges
│   └── POST   /sync                    sync from data source
│
├── /api/plan                           路线规划
│   ├── POST   /generate                generate plans
│   ├── GET    /plans                   list plans
│   ├── GET    /plans/{id}              get plan detail
│   ├── POST   /plans/{id}/select       select plan
│   └── POST   /replan                  replan
│
├── /api/browse                         浏览
│   ├── POST   /start                   start browsing
│   ├── GET    /status                  get progress
│   ├── GET    /cards                   current cards
│   ├── POST   /next                    next card
│   ├── POST   /prev                    prev card
│   └── POST   /waypoint                next waypoint
│
├── /api/search                         搜索
│   ├── POST   /query                   execute search
│   └── POST   /vector-match            vector matching only
│
├── /api/yaml                           YAML 导入导出
│   ├── GET    /export                  export all data
│   ├── POST   /preview                 preview import
│   ├── POST   /import                  execute import
│   └── POST   /validate                validate yaml
│
├── /api/ai                              AI 辅助生成
│   ├── POST   /generate/card-title      generate card title
│   ├── POST   /generate/card-desc       generate card description
│   ├── POST   /generate/node-label      generate node label
│   └── POST   /generate/node-desc       generate node description
│
├── /api/connections                     快捷连接
│   ├── GET    /status/{fromId}/{toId}   query connection status
│   ├── POST   /ensure                   ensure quick connection
│   ├── PUT    /{fromId}/{toId}          update connection
│   ├── DELETE /{fromId}/{toId}          remove connection
│   └── POST   /fill-all                 batch fill missing
│
└── /api/view                            视图/面板
    ├── GET    /current                  get current view
    └── POST   /switch                   switch view
```

### 4.3 数据持久化

- **开发阶段**：JSON 文件存储（类似 `cognitive-cards/server.py` 的 `DataService`）
- **生产阶段**：SQLite / PostgreSQL

---

## 五、切换模式的影响范围

### 5.1 功能覆盖矩阵

| 功能域 | 轻量模式（lite） | 完整模式（pro） |
|--------|----------|----------|
| 认知卡片 CRUD | Zustand Store → data/cards.ts | `GET/POST/PUT/DELETE /api/cards` |
| 导航节点 CRUD | Zustand Store → data/allNavNodes.ts | `GET/POST/PUT/DELETE /api/nodes` |
| 出向连接管理 | quickConnectUtils.ts | `POST/PUT/DELETE /api/connections` |
| 导航图 | navStore + allEdges 推导 | `GET /api/graph/edges` |
| 路线规划 | routePlanner.ts | `POST /api/plan/generate` |
| 浏览 | browseStore | `POST /api/browse/start` |
| 搜索（关键词） | searchStore（前端过滤） | `POST /api/search/query` |
| 搜索（向量） | vectorMatchUtils.ts（轻量降级） | `POST /api/search/vector-match` |
| YAML 导入导出 | yamlIO.ts（浏览器文件操作） | `GET /api/yaml/export` + `POST /api/yaml/import` |
| AI 辅助生成 | aiFallback.ts（轻量降级） | `POST /api/ai/generate/*` |
| 树形管理 | treeStore + treeUtils.ts | 组合 `GET /api/cards` + `GET /api/nodes` |
| 视图切换 | viewStore | `POST /api/view/switch` |
| 面板控制 | panelStore | 轻量处理（纯 UI 状态） |

### 5.2 仅轻量模式（lite）保留的功能

以下功能**始终在轻量处理**，不依赖后端：

| 功能 | 原因 |
|------|------|
| UI 状态（面板展开/折叠、Tab 切换） | 纯前端交互状态，无需持久化 |
| Toast 提示 | 纯 UI 反馈 |
| 画布缩放/平移（useNavCanvas） | 纯前端交互，无需服务端 |
| 卡片滑动（useCardSwipe） | 纯前端手势处理 |
| 下拉面板拖拽（useDragPanel） | 纯前端手势处理 |
| localStorage 读写（后端配置等） | 浏览器本地存储 |

---

## 六、目录结构变更

```
src/
├── config/
│   └── backend.ts              ← 新增: 后端模式配置与初始化
│
├── api/
│   ├── index.ts                ← 修改: KnowledgeNavigatorAPI 增加模式判断
│   └── BackendAdapter.ts       ← 新增: HTTP 请求封装适配器
│
└── ... (现有代码结构不变)
```

---

## 七、验收标准

- [ ] `BackendConfig` 支持 `lite` / `pro` 两种模式
- [ ] 模式设置有三级优先级：URL 参数 > localStorage > 默认值
- [ ] 树形管理视图中可直观切换后端模式并配置后端地址
- [ ] 测试连接按钮可验证后端连通性
- [ ] 轻量模式（lite）下所有功能表现与当前一致
- [ ] 完整模式（pro）下认知卡片 CRUD 请求正确的 REST API
- [ ] 完整模式（pro）下导航节点 CRUD 请求正确的 REST API
- [ ] 完整模式（pro）下路线规划调用后端生成
- [ ] 完整模式（pro）下搜索（关键词+向量）调用后端
- [ ] 完整模式（pro）下 AI 辅助生成调用后端
- [ ] 完整模式（pro）下 YAML 导入导出调用后端
- [ ] 切换模式时 UI 即时响应，无需刷新页面
- [ ] 后端不可用时完整模式（pro）有友好的错误提示
- [ ] API 错误通过 Toast 组件显示给用户
- [ ] TypeScript 编译零错误
- [ ] Python 后端 API 路由与前端预期一致

---

## 八、边界情况

| 场景 | 行为 |
|------|------|
| 完整模式（pro）下后端不可用 | API 请求超时（10 秒）→ Toast "后端服务不可用，请检查连接" |
| 完整模式（pro）切换回轻量模式（lite） | 数据从后端拉取后合并到本地，继续以轻量方式运行 |
| 轻量模式（lite）下操作的数据未同步到后端 | 切换为完整模式（pro）时提示"本地数据尚未同步到后端" |
| 完整模式（pro）下某 API 返回 404 | 前端显示 "该功能后端暂未实现" |
| URL 参数指定了无效的后端地址 | 测试连接失败时红色提示，禁止保存 |
| 后端请求返回网络错误 | 自动重试 1 次后仍失败则显示错误 Toast |
| 浏览器不支持 `fetch` 或 `AbortController` | 降级为轻量模式（lite），Console 警告 |
| 同时存在 localStorage 保存的配置和 URL 参数 | URL 参数优先 |
