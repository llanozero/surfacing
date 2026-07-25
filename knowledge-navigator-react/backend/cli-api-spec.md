# Knowledge Navigator Backend — CLI & API 规范

## 版本

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| 1.0 | 2026-07-25 | — | 初始规范：为 Python 后端所有功能建立 CLI 和 API 接口定义 |

---

## 一、概述

### 1.1 目标

为 **Knowledge Navigator Backend**（Python FastAPI）的所有功能提供两套程序化接口：

- **CLI（`kn-backend`）**：命令行工具，支持在终端中直接调用后端所有 API，适合调试、运维、批量操作
- **API（RESTful）**：后端已实现的 48 个 REST 端点，按照资源域组织，供前端或其他服务调用

### 1.2 设计原则

- **CLI = API 的 shell 封装**：每条 CLI 命令对应一个 REST API 调用，无额外业务逻辑
- **输出可解析**：CLI 默认输出格式化为易读文本，支持 `--json` 标志输出原始 JSON
- **无状态**：CLI 每次调用独立，不维护持久化连接（但服务端会话态如 Browse/Plan 在多次 CLI 调用间保持）
- **错误可处理**：所有操作以 HTTP 状态码 + JSON body 返回错误信息

### 1.3 项目结构

```
backend/
├── cli.py                          # CLI 入口（可选，独立脚本）
├── app/
│   ├── main.py                     # FastAPI 应用入口（已有）
│   ├── domain.py                   # 领域逻辑（已有）
│   ├── store.py                    # 数据存储层（已有）
│   └── routers/                    # API 路由（已有，10 个模块）
└── kn-backend/                     # 或独立为 pip 包
    ├── __init__.py
    ├── client.py                   # API 客户端封装
    └── cli.py                      # CLI 命令处理器
```

---

## 二、API 总览

后端当前提供 **48 个 REST 端点**，分布在 10 个路由模块：

| 模块 | 端点数 | 前缀 |
|------|--------|------|
| 认知卡片 | 10 | `/api/cards` |
| 导航节点 | 13 | `/api/nodes` |
| 导航图 | 3 | `/api/graph` |
| 路线规划 | 5 | `/api/plan` |
| 浏览 | 6 | `/api/browse` |
| 搜索 | 2 | `/api/search` |
| AI 生成 | 1 | `/api/ai/generate/{endpoint}` |
| 快捷连接 | 5 | `/api/connections` |
| YAML | 4 | `/api/yaml` |
| 视图 | 2 | `/api/view` |
| 健康 | 1 | `/api/health` |

---

## 三、API 详细规范

> `{card_id:path}` 表示该路径参数可包含斜杠（如 `root/1/2`），路径转换器为 `:path`

### 3.1 健康检查

```
GET /api/health
```

**响应 200：**
```json
{
  "status": "ok",
  "service": "Knowledge Navigator Backend",
  "version": "0.1.0",
  "node_count": 17,
  "card_count": 18
}
```

---

### 3.2 认知卡片 (Cards)

#### 3.2.1 获取所有卡片

```
GET /api/cards
```

**响应 200：** `list[Card]`

#### 3.2.2 获取单张卡片

```
GET /api/cards/{card_id:path}
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `card_id` | path | 卡片 ID，如 `root/1`、`root/1/2` |

**响应 200：** `Card` 对象
**响应 404：** `{"detail": "卡片 xxx 不存在"}`

#### 3.2.3 创建卡片

```
POST /api/cards
```

**请求体：**
```json
{
  "parent_id": "root/1"    // 可选，不传则创建根级卡片
}
```

**响应 201：** `Card` 对象（自动生成 `id`、`type='leaf'`、空 `corpus`、空 `bound_nodes`）
**响应 400：** `{"detail": "父卡片 root/xxx 不存在"}`

#### 3.2.4 更新卡片字段

```
PUT /api/cards/{card_id:path}
```

**请求体：** 任意字段（`id` 只读，静默忽略）
```json
{
  "title": "新标题",
  "description": "新描述",
  "tag": "new-tag"
}
```

**响应 200：** `Card` 对象（更新后）

#### 3.2.5 删除卡片

```
DELETE /api/cards/{card_id:path}
```

**响应 200：** `{"ok": true, "message": "卡片 xxx 已删除"}`
**响应 409：** `{"detail": "文件夹 root/1 不为空，请先删除子卡片"}`（文件夹类型且含子卡片时）

#### 3.2.6 获取子卡片

```
GET /api/cards/{card_id:path}/children
```

**响应 200：** `list[Card]`

#### 3.2.7 获取卡片语料

```
GET /api/cards/{card_id:path}/corpus
```

**响应 200：** `list[str]`

#### 3.2.8 添加语料

```
POST /api/cards/{card_id:path}/corpus
```

**请求体：** `{"text": "新语料内容"}`
**响应 201：** `{"ok": true, "card_id": "xxx", "corpus": [...]}`

#### 3.2.9 更新语料

```
PUT /api/cards/{card_id:path}/corpus/{index}
```

**请求体：** `{"text": "更新后的语料内容"}`
**响应 200：** `{"ok": true, "card_id": "xxx", "corpus": [...]}`
**响应 404：** `{"detail": "索引 {index} 超出语料库范围"}`

#### 3.2.10 删除语料

```
DELETE /api/cards/{card_id:path}/corpus/{index}
```

**响应 200：** `{"ok": true, "card_id": "xxx", "corpus": [...]}`
**响应 404：** `{"detail": "索引 {index} 超出语料库范围"}`

---

### 3.3 导航节点 (Nodes)

#### 3.3.1 获取所有节点

```
GET /api/nodes?q=机器学习
```

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `q` | query | 无 | 按 id/label/description 模糊搜索 |

**响应 200：** `list[Node]`

#### 3.3.2 获取单个节点

```
GET /api/nodes/{node_id}
```

**响应 200：** `Node` 对象
**响应 404：** `{"detail": "节点 xxx 不存在"}`

#### 3.3.3 创建节点

```
POST /api/nodes
```

**请求体：** 无（或可选 `{"label": "..."}`）
**响应 201：** `Node` 对象（自动生成 `id` 如 `node-custom-5`，空 `next_nodes`、空 `bound_cards`）

#### 3.3.4 更新节点字段

```
PUT /api/nodes/{node_id}
```

**请求体：** 任意字段（`id` 只读）
```json
{
  "label": "新标签",
  "description": "新描述"
}
```

**响应 200：** `Node` 对象（更新后）

#### 3.3.5 删除节点（级联清理）

```
DELETE /api/nodes/{node_id}
```

级联操作：
- 从其他节点的 `next_nodes` 中移除对该节点的引用
- 从所有卡片的 `bound_nodes` 中移除该节点
- 同步 `data.yaml`

**响应 200：** `{"ok": true, "message": "节点 xxx 已删除，已清理 X 处引用"}`

#### 3.3.6 绑定卡片到节点

```
POST /api/nodes/{node_id}/bind-card
```

**请求体：** `{"card_id": "root/1"}`
**响应 200：** `{"ok": true}`
**副作用：** 同时将节点 id 追加到卡片的 `bound_nodes` 中

#### 3.3.7 解绑卡片

```
DELETE /api/nodes/{node_id}/bind-card/{card_id:path}
```

**响应 200：** `{"ok": true}`
**副作用：** 同时从卡片的 `bound_nodes` 中移除节点 id

#### 3.3.8 获取出向连接（按合成权重排序）

```
GET /api/nodes/{node_id}/next
```

**响应 200：** `list[NextNodeItem]`
```json
[
  {
    "target_id": "node-id",
    "preset_priority": 1,
    "connection_type": "preset",
    "composite_weight": 0.95,
    "target_label": "目标节点标签"
  }
]
```

#### 3.3.9 添加出向连接

```
POST /api/nodes/{node_id}/next
```

**请求体：**
```json
{
  "target_id": "node-id",
  "preset_priority": 1,
  "browse_priority": 0,
  "connection_type": "user_added"
}
```

**响应 201：** `{"ok": true}`
**响应 400：** `{"detail": "禁止自环连接"}` 或 `{"detail": "连接已存在"}`

#### 3.3.10 更新出向连接

```
PUT /api/nodes/{node_id}/next/{target_id}
```

**请求体：** `{"preset_priority": 2, "connection_type": "preset"}`
**响应 200：** `{"ok": true}`

#### 3.3.11 删除出向连接

```
DELETE /api/nodes/{node_id}/next/{target_id}
```

**响应 200：** `{"ok": true}`

#### 3.3.12 获取入向连接（前驱节点）

```
GET /api/nodes/{node_id}/prev
```

**响应 200：** `list[dict]`（含 `source_id`、`source_label`、`connection_type`、`preset_priority`）

#### 3.3.13 获取浏览历史

```
GET /api/nodes/{node_id}/browse-history
```

**响应 200：** `list[BrowseRecord]`（含 `target_id`、`count`、`last_browsed_at`）

---

### 3.4 导航图 (Graph)

#### 3.4.1 获取所有图节点

```
GET /api/graph/nodes
```

**响应 200：** `list[Node]`

#### 3.4.2 获取所有有向边

```
GET /api/graph/edges
```

**响应 200：** `list[GraphEdge]`
```json
[
  {"source": "node-a", "target": "node-b", "weight": 0.85}
]
```
边由所有节点的 `next_nodes` 实时推导，`weight` 取 `preset_weight`（若存在）或默认 0.5。

#### 3.4.3 同步数据

```
POST /api/graph/sync
```

从 `data.yaml` 重新加载数据到内存。

**响应 200：** `{"ok": true, "cards": 18, "nodes": 17}`

---

### 3.5 路线规划 (Plan)

服务端维护会话态（`PlanState`），保存途经点和当前计划列表。

#### 3.5.1 生成路线计划

```
POST /api/plan/generate
```

**请求体：**
```json
{
  "waypoint_ids": ["node-a", "node-b", "node-c"],
  "waypoint_mode": "ordered",
  "weight_mode": "mixed"
}
```

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `waypoint_ids` | string[] | 无 | 途经点 ID 列表，不传则用上次生成的 |
| `waypoint_mode` | string | `ordered` | `ordered`（有序）或 `unordered`（无序） |
| `weight_mode` | string | `mixed` | `mixed`（混合）或 `user_only`（纯用户） |

**响应 200：** `list[RoutePlan]`
```json
[
  {
    "id": "plan-1",
    "label": "全排列最优方案",
    "sequence": ["node-a", "node-b", "node-c"],
    "total_weight": 2.45,
    "algorithm": "permutation_optimal",
    "is_recommended": true
  }
]
```

#### 3.5.2 获取所有计划

```
GET /api/plan/plans
```

**响应 200：** `list[RoutePlan]`

#### 3.5.3 获取计划详情

```
GET /api/plan/plans/{plan_id}
```

**响应 200：** `RoutePlan` 对象
**响应 404：** `{"detail": "计划 xxx 不存在"}`

#### 3.5.4 选中计划

```
POST /api/plan/plans/{plan_id}/select
```

**响应 200：** `{"ok": true, "plan_id": "xxx"}`
**响应 404：** `{"detail": "计划 xxx 不存在"}`

#### 3.5.5 重新规划

```
POST /api/plan/replan
```

沿用上次的 `waypoint_ids` 和模式重新生成计划。

**响应 200：** `list[RoutePlan]`
**响应 400：** `{"detail": "没有上次的途经点数据，请先调用 generate"}`

---

### 3.6 浏览 (Browse)

服务端维护会话态（`BrowseState`），保存当前浏览进度。

#### 3.6.1 开始浏览

```
POST /api/browse/start
```

**请求体（二选一）：**
```json
// 方案 A：从计划开始
{"plan_id": "plan-1"}

// 方案 B：直接指定序列
{"sequence": ["node-a", "node-b", "node-c"]}
```

**响应 200：** `{"ok": true, "sequence": [...], "total_waypoints": 3}`
**响应 400：** `{"detail": "必须提供 plan_id 或 sequence"}`

#### 3.6.2 获取浏览进度

```
GET /api/browse/status
```

**响应 200：**
```json
{
  "waypoint_index": 0,
  "total_waypoints": 3,
  "card_index": 0,
  "total_cards": 2,
  "current_waypoint_id": "node-a",
  "current_waypoint_label": "机器学习基础"
}
```

#### 3.6.3 获取当前浏览卡片

```
GET /api/browse/cards
```

**响应 200：** `list[BrowseCard]`
```json
[
  {
    "title": "机器学习基础",
    "desc": "机器学习是人工智能的核心...",
    "tag": "ml",
    "weight": 0.85,
    "cards": [...],
    "corpus": [...],
    "related": [{"name": "监督学习", "pos": "后置"}]
  }
]
```

#### 3.6.4 下一张卡片

```
POST /api/browse/next
```

**响应 200：** `{"ok": true, "card_index": 1}`
**响应 400：** `{"detail": "已经是最后一张卡片"}`

#### 3.6.5 上一张卡片

```
POST /api/browse/prev
```

**响应 200：** `{"ok": true, "card_index": 0}`
**响应 400：** `{"detail": "已经是第一张卡片"}`

#### 3.6.6 下一站

```
POST /api/browse/waypoint
```

**响应 200：** `{"ok": true, "waypoint_index": 1, "waypoint_label": "监督学习"}`
**响应 400：** `{"detail": "已经是最后一站"}`

---

### 3.7 搜索 (Search)

#### 3.7.1 关键词搜索

```
POST /api/search/query
```

**请求体：** `{"query": "神经网络", "mode": "keyword"}`

**评分算法：** 标题命中 0.5-0.6、标签 0.2、描述 0.15、语料 0.1，多词额外加分。

**响应 200：** `list[MatchedCard]`
```json
[
  {
    "card": {"id": "root/3", "title": "神经网络基础", ...},
    "score": 0.85
  }
]
```

#### 3.7.2 向量匹配

```
POST /api/search/vector-match
```

**请求体：** `{"query": "神经网络", "mode": "vector"}`

当前降级为关键词搜索（与 `query` 相同逻辑），后续接入向量数据库后升级。

**响应 200：** `list[MatchedCard]`

---

### 3.8 AI 辅助生成

```
POST /api/ai/generate/{endpoint}
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `endpoint` | path | `card-title`、`card-desc`、`node-label`、`node-desc` 之一 |

**请求体：**
```json
{
  "id": "root/5"
}
```

**处理流程：**
1. 根据 `id` 加载对应卡片或节点
2. 收集上下文（子卡片、语料库、绑定卡片、前驱/后继节点）
3. 调用 LM Studio（`http://localhost:1234/v1/chat/completions`）
4. LM Studio 不可用时降级为本地模板

**响应 200：** `{"result": "生成的标题/描述内容"}`
**响应 404：** `{"detail": "资源 xxx 不存在"}`

---

### 3.9 快捷连接 (Connections)

#### 3.9.1 查询连接状态

```
GET /api/connections/status/{from_id}/{to_id}
```

**响应 200：**
```json
// 已连接
{"status": "connected", "ref": {"target_id": "...", "preset_priority": 1}}
// 无连接（可新建）
{"status": "missing"}
// 起始节点不存在
{"status": "unavailable"}
```

#### 3.9.2 确保连接存在

```
POST /api/connections/ensure
```

**请求体：** `{"from_id": "node-a", "to_id": "node-b"}`
**响应 200：** `{"ok": true, "created": true}`（`created` 表示是否新建）
**响应 400：** `{"detail": "from_id 和 to_id 不能相同"}`

#### 3.9.3 更新连接

```
PUT /api/connections/{from_id}/{to_id}
```

**请求体：** `{"preset_priority": 2, "connection_type": "preset"}`
**响应 200：** `{"ok": true}`
**响应 404：** `{"detail": "连接不存在"}`

#### 3.9.4 删除连接

```
DELETE /api/connections/{from_id}/{to_id}
```

**响应 200：** `{"ok": true}`
**响应 404：** `{"detail": "连接不存在"}`

#### 3.9.5 批量补齐连接

```
POST /api/connections/fill-all
```

**请求体：** `{"waypoint_ids": ["node-a", "node-b", "node-c"]}`
**响应 200：** `{"ok": true, "created_count": 2}`

---

### 3.10 YAML 导入导出

#### 3.10.1 导出全部数据

```
GET /api/yaml/export
```

**响应 200：** `{"yaml": "...YAML字符串..."}`

#### 3.10.2 验证 YAML

```
POST /api/yaml/validate
```

**请求体：** `{"raw": "...YAML字符串..."}`
**响应 200：**
```json
{
  "ok": true,
  "data": {
    "cognitive_cards": [...],
    "navigation_nodes": [...]
  }
}
```
**响应 422：**
```json
{
  "ok": false,
  "errors": [
    {"type": "structure", "message": "缺少 cognitive_cards 字段"}
  ]
}
```

#### 3.10.3 预览导入

```
POST /api/yaml/preview
```

**请求体：** `{"raw": "...YAML字符串..."}`
**响应 200：**
```json
{
  "ok": true,
  "preview": {
    "cards": {"total": 18, "added": 2, "overwritten": 1, "unchanged": 15},
    "nodes": {"total": 17, "added": 0, "overwritten": 3, "unchanged": 14}
  }
}
```

#### 3.10.4 导入数据

```
POST /api/yaml/import
```

**请求体：** `{"raw": "...YAML字符串..."}`
**处理：** Upsert 合并，不删除现有数据
**响应 200：**
```json
{
  "ok": true,
  "result": {
    "cards": {"total": 18, "added": 2, "overwritten": 1},
    "nodes": {"total": 17, "added": 0, "overwritten": 3}
  }
}
```

---

### 3.11 视图 (View)

#### 3.11.1 获取当前视图

```
GET /api/view/current
```

**响应 200：** `{"view": "search"}`

#### 3.11.2 切换视图

```
POST /api/view/switch
```

**请求体：** `{"view": "plan"}`
**合法值：** `search`, `nav`, `plan`, `browse`, `tree`
**响应 200：** `{"ok": true, "view": "plan"}`

---

## 四、CLI 设计

### 4.1 基本用法

```
kn-backend <command> [subcommand] [options] [arguments]
```

**全局选项：**

| 选项 | 说明 |
|------|------|
| `--server <url>` | 后端地址（默认 `http://localhost:8171`） |
| `--json` | 输出 JSON 格式（默认输出易读文本） |
| `--help` | 显示帮助信息 |

**输出格式：**

```
# 文本模式（默认）
✓ 已获取 18 张卡片

# JSON 模式 (--json)
[{"id":"root/1","title":"机器学习基础",...}]
```

### 4.2 命令树

```
kn-backend
├── health                          # 健康检查
│
├── card                            # 认知卡片管理
│   ├── list                        # 列出所有卡片
│   ├── get <id>                    # 查看单张卡片
│   ├── create [--parent <id>]      # 新建卡片
│   ├── delete <id>                 # 删除卡片
│   ├── update <id> <field> <value> # 更新字段
│   ├── children <id>               # 列出子卡片
│   ├── corpus                      # 语料库管理
│   │   ├── list <id>               # 列出语料
│   │   ├── add <id> <text>         # 添加语料
│   │   ├── update <id> <index> <text>  # 更新语料
│   │   └── remove <id> <index>     # 删除语料
│   └── generate                    # AI 生成
│       ├── title <id>              # 生成标题
│       └── desc <id>               # 生成描述
│
├── node                            # 导航节点管理
│   ├── list [--query <q>]          # 列出节点
│   ├── get <id>                    # 查看单个节点
│   ├── create                      # 新建节点
│   ├── delete <id>                 # 删除节点
│   ├── update <id> <field> <value> # 更新字段
│   ├── bind                        # 绑定卡片管理
│   │   ├── list <id>               # 列出绑定卡片
│   │   ├── add <nodeId> <cardId>   # 绑定
│   │   └── remove <nodeId> <cardId> # 解绑
│   ├── next                        # 出向连接
│   │   ├── list <id>               # 列出出向连接
│   │   ├── add <fromId> <toId> [--priority <n>] [--type <t>]  # 添加
│   │   ├── update <fromId> <toId> <field> <value>  # 更新
│   │   └── remove <fromId> <toId>  # 删除
│   ├── prev <id>                   # 列出前驱
│   ├── history <id>                # 浏览历史
│   └── generate                    # AI 生成
│       ├── label <id>              # 生成标签
│       └── desc <id>               # 生成描述
│
├── graph                           # 导航图操作
│   ├── nodes                       # 列出图节点
│   ├── edges                       # 列出有向边
│   └── sync                        # 重新加载数据
│
├── plan                            # 路线规划
│   ├── generate <id1,id2,...>      # 生成计划
│   │   [--mode ordered|unordered]  # 途经点模式
│   │   [--weight mixed|user_only]  # 权重模式
│   ├── list                        # 列出所有计划
│   ├── get <id>                    # 查看计划详情
│   ├── select <id>                 # 选中计划
│   ├── recommend                   # 查看推荐计划
│   └── replan                      # 重新规划
│
├── browse                          # 浏览操作
│   ├── start                       # 开始浏览
│   │   [--plan <id>]               # 按计划
│   │   [--sequence <ids>]          # 或直接指定序列
│   ├── status                      # 浏览进度
│   ├── cards                       # 当前卡片
│   ├── next                        # 下一张卡片
│   ├── prev                        # 上一张卡片
│   └── waypoint                    # 下一站
│
├── search                          # 搜索
│   ├── query <text>                # 关键词搜索
│   │   [--mode keyword|vector]     # 匹配模式
│   └── vector <text>               # 向量搜索
│
├── connect                         # 快捷连接
│   ├── status <fromId> <toId>      # 查询状态
│   ├── ensure <fromId> <toId>      # 确保连接
│   ├── update <fromId> <toId> <field> <value>  # 更新
│   ├── remove <fromId> <toId>      # 删除
│   └── fill <id1,id2,...>          # 批量补齐
│
├── yaml                            # YAML 操作
│   ├── export [--file <path>]      # 导出到文件
│   ├── validate <file>             # 验证文件
│   ├── preview <file>              # 预览导入
│   └── import <file>               # 导入数据
│
├── view                            # 视图切换
│   ├── get                         # 当前视图
│   └── set <search|nav|plan|browse|tree>  # 切换
│
└── help [command]                  # 查看帮助
```

### 4.3 CLI 命令详细规范

#### 4.3.1 `kn-backend health`

```
kn-backend health [--json]
```

示例：
```
$ kn-backend health
✓ 服务运行中
  名称: Knowledge Navigator Backend
  版本: 0.1.0
  卡片: 18 张
  节点: 17 个
```

#### 4.3.2 `kn-backend card`

```
kn-backend card list [--json]
kn-backend card get <id> [--json]
kn-backend card create [--parent <parentId>] [--json]
kn-backend card delete <id>
kn-backend card update <id> <field> <value>
kn-backend card children <id> [--json]
kn-backend card corpus list <id>
kn-backend card corpus add <id> <text>
kn-backend card corpus update <id> <index> <text>
kn-backend card corpus remove <id> <index>
kn-backend card generate title <id>
kn-backend card generate desc <id>

示例:
  kn-backend card list --json
  kn-backend card get root/1
  kn-backend card create --parent root/1
  kn-backend card update root/5 title "机器学习进阶"
  kn-backend card corpus add root/5 "补充语料"
  kn-backend card generate title root/5
```

#### 4.3.3 `kn-backend node`

```
kn-backend node list [--query <q>] [--json]
kn-backend node get <id> [--json]
kn-backend node create [--json]
kn-backend node delete <id>
kn-backend node update <id> <field> <value>
kn-backend node bind list <id>
kn-backend node bind add <nodeId> <cardId>
kn-backend node bind remove <nodeId> <cardId>
kn-backend node next list <id> [--json]
kn-backend node next add <fromId> <toId> [--priority <n>] [--type <t>]
kn-backend node next update <fromId> <toId> <field> <value>
kn-backend node next remove <fromId> <toId>
kn-backend node prev <id> [--json]
kn-backend node history <id> [--json]
kn-backend node generate label <id>
kn-backend node generate desc <id>

示例:
  kn-backend node list --query "机器"
  kn-backend node get node-ml-foundation --json
  kn-backend node create
  kn-backend node next add node-1 node-2 --priority 1
  kn-backend node prev node-3
  kn-backend node history node-1
```

#### 4.3.4 `kn-backend graph`

```
kn-backend graph nodes [--json]
kn-backend graph edges [--json]
kn-backend graph sync

示例:
  kn-backend graph edges --json
  kn-backend graph sync
```

#### 4.3.5 `kn-backend plan`

```
kn-backend plan generate <id1,id2,...> [--mode ordered|unordered] [--weight mixed|user_only] [--json]
kn-backend plan list [--json]
kn-backend plan get <id> [--json]
kn-backend plan select <id>
kn-backend plan recommend [--json]
kn-backend plan replan [--json]

示例:
  kn-backend plan generate node-1,node-2,node-3
  kn-backend plan generate node-1,node-2 --mode unordered --weight user_only
  kn-backend plan select plan-1
  kn-backend plan recommend
```

#### 4.3.6 `kn-backend browse`

```
kn-backend browse start --plan <planId>
kn-backend browse start --sequence <id1,id2,...>
kn-backend browse status [--json]
kn-backend browse cards [--json]
kn-backend browse next
kn-backend browse prev
kn-backend browse waypoint

示例:
  kn-backend browse start --plan plan-1
  kn-backend browse status
  kn-backend browse next
  kn-backend browse waypoint
```

#### 4.3.7 `kn-backend search`

```
kn-backend search query <text> [--mode keyword|vector] [--json]
kn-backend search vector <text> [--json]

示例:
  kn-backend search query "神经网络" --json
  kn-backend search vector "注意力机制"
```

#### 4.3.8 `kn-backend connect`

```
kn-backend connect status <fromId> <toId> [--json]
kn-backend connect ensure <fromId> <toId>
kn-backend connect update <fromId> <toId> <field> <value>
kn-backend connect remove <fromId> <toId>
kn-backend connect fill <id1,id2,...>

示例:
  kn-backend connect status node-1 node-2
  kn-backend connect ensure node-1 node-2
  kn-backend connect fill node-1,node-2,node-3
```

#### 4.3.9 `kn-backend yaml`

```
kn-backend yaml export [--file <path>]
kn-backend yaml validate <file> [--json]
kn-backend yaml preview <file> [--json]
kn-backend yaml import <file>

示例:
  kn-backend yaml export --file ./backup.yaml
  kn-backend yaml validate ./data.yaml
  kn-backend yaml preview ./import.yaml
  kn-backend yaml import ./backup.yaml
```

#### 4.3.10 `kn-backend view`

```
kn-backend view get
kn-backend view set <search|nav|plan|browse|tree>

示例:
  kn-backend view get
  kn-backend view set plan
```

#### 4.3.11 `kn-backend help`

```
kn-backend help
kn-backend help card
kn-backend help plan
```

---

## 五、CLI 实现指南

### 5.1 架构

```
backend/cli.py                           ← 独立 CLI 入口（可选）
backend/kn-backend/
├── __init__.py
├── client.py                              ← ApiClient 类，封装 HTTP 请求
├── cli.py                                 ← CLI 入口与命令处理器
├── formatter.py                           ← 输出格式化
└── commands/
    ├── card.py
    ├── node.py
    ├── graph.py
    ├── plan.py
    ├── browse.py
    ├── search.py
    ├── connect.py
    ├── yaml_cmd.py
    ├── view.py
    └── health.py
```

### 5.2 API 客户端

```python
# kn-backend/client.py
import json
import urllib.request
import urllib.error
from typing import Any, Optional

DEFAULT_SERVER = "http://localhost:8171"
TIMEOUT = 10


class ApiClient:
    def __init__(self, server: str = DEFAULT_SERVER):
        self.server = server.rstrip("/")

    def _request(self, method: str, path: str, body: Any = None) -> Any:
        url = f"{self.server}{path}"
        data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Accept", "application/json")
        if body:
            req.add_header("Content-Type", "application/json; charset=utf-8")
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace")
            raise ApiError(e.code, detail)
        except urllib.error.URLError:
            raise ConnectionError(f"无法连接到 {self.server}")

    def get(self, path: str) -> Any:
        return self._request("GET", path)

    def post(self, path: str, body: Any = None) -> Any:
        return self._request("POST", path, body)

    def put(self, path: str, body: Any = None) -> Any:
        return self._request("PUT", path, body)

    def delete(self, path: str) -> Any:
        return self._request("DELETE", path)


class ApiError(Exception):
    def __init__(self, status: int, detail: str):
        self.status = status
        self.detail = detail
        super().__init__(f"HTTP {status}: {detail}")
```

### 5.3 命令处理器示例

```python
# kn-backend/commands/card.py
from ..client import ApiClient

def cmd_card_list(client: ApiClient, args):
    data = client.get("/api/cards")
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(f"  ✓ 共 {len(data)} 张卡片")
        for c in data:
            print(f"    {c['id']} · {c['title']} ({c.get('type', 'leaf')})")


def cmd_card_get(client: ApiClient, args):
    card = client.get(f"/api/cards/{args.id}")
    if args.json:
        print(json.dumps(card, ensure_ascii=False, indent=2))
    else:
        print(f"  ID: {card['id']}")
        print(f"  标题: {card['title']}")
        print(f"  类型: {card.get('type', 'leaf')}")
        print(f"  标签: {card.get('tag', '-')}")
        print(f"  语料: {len(card.get('corpus', []))} 条")
        print(f"  绑定节点: {card.get('bound_nodes', [])}")
```

### 5.4 入口

```python
# kn-backend/cli.py (或 backend/cli.py)
#!/usr/bin/env python3
import sys
from .client import ApiClient, DEFAULT_SERVER

def main():
    import argparse
    parser = argparse.ArgumentParser(prog="kn-backend")
    parser.add_argument("--server", default=DEFAULT_SERVER)
    parser.add_argument("--json", action="store_true")
    # ... 子命令注册
    args = parser.parse_args()
    client = ApiClient(args.server)
    # ... 分发到命令处理器

if __name__ == "__main__":
    main()
```

---

## 六、与前端 CLI 的关系

| 维度 | 前端 CLI (`kn-cli`) | 后端 CLI (`kn-backend`) |
|------|---------------------|------------------------|
| 运行位置 | 浏览器 / Node.js | 终端 / Python 环境 |
| 数据源 | 浏览器内存 (Zustand Store) | 后端 data.yaml |
| 状态 | 无状态（每命令独立） | 无状态（但服务端保持会话） |
| 主要用途 | 开发调试、本地快速验证 | 运维管理、批量操作、CI/CD |
| API 源 | 调用前端 `KnowledgeNavigatorAPI` | 调用后端 REST API |

两个 CLI 的命令结构保持一致，方便用户记忆切换：

```
kn-cli card list          → 前端本地数据
kn-backend card list      → 后端 data.yaml
```

---

## 七、验收标准

- [ ] CLI 所有命令可正常调用后端 API
- [ ] CLI `--json` 标志输出原始 JSON
- [ ] CLI `--server` 可指定后端地址
- [ ] 健康检查命令返回后端状态
- [ ] 认知卡片 CLI 覆盖所有 10 个端点
- [ ] 导航节点 CLI 覆盖所有 13 个端点
- [ ] 导航图 CLI 覆盖所有 3 个端点
- [ ] 路线规划 CLI 覆盖生成/列表/详情/选中/重规划
- [ ] 浏览 CLI 覆盖开始/进度/卡片/翻卡/下一站
- [ ] 搜索 CLI 支持关键词和向量两种模式
- [ ] 快捷连接 CLI 覆盖状态查询/确保/更新/删除/批量补齐
- [ ] YAML CLI 覆盖导出/验证/预览/导入
- [ ] 视图 CLI 覆盖查看和切换
- [ ] `kn-backend` 可注册为系统命令
- [ ] Python 语法无错误

---

## 八、边界情况

| 场景 | 行为 |
|------|------|
| 后端服务未启动 | CLI 显示 `无法连接到 http://localhost:8171` |
| 请求不存在的卡片/节点 | 显示 `HTTP 404: 卡片 xxx 不存在` |
| 删除非空文件夹卡片 | 显示 `HTTP 409: 文件夹不为空` |
| 添加已存在的出向连接 | 显示 `HTTP 400: 连接已存在` |
| 自环连接 | 显示 `HTTP 400: 禁止自环连接` |
| 浏览到终点后继续操作 | 显示 `HTTP 400: 已经是最后一张/最后一站` |
| 浏览未开始就操作 | 返回空状态或 400 |
| 导出时写入权限不足 | CLI 提示文件写入错误 |
| YAML 格式错误 | 显示详细的验证错误列表 |
| 搜索无结果 | 返回空数组 `[]` |
| 计划生成时途经点不足 | 显示 `HTTP 400: 途经点至少需要 2 个` |
| 重规划但无上次数据 | 显示 `HTTP 400: 没有上次的途经点数据` |
