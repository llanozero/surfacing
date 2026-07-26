# 认知导航 Knowledge Navigator（React + FastAPI）

以「认知卡片 + 导航节点」双数据模型驱动的知识导航应用。五个视图：
**搜索**（关键词 / 向量语义匹配卡片并定位节点）、**导航**（力导向画布漫游节点）、
**规划**（途经点生成候选路线）、**浏览**（按路线逐站翻阅卡片）、
**管理**（卡片 / 节点的增删改与 YAML 导入导出）。

## 快速开始

```powershell
# 一键启动（自动清理 8171/7100 端口占用 → 起后端 → 健康检查 → 起前端）
powershell -ExecutionPolicy Bypass -File .\start-dev.ps1
```

或手动：

```bash
python backend/run.py          # 后端 http://localhost:8171（FastAPI + YAML 持久化）
npm run dev                    # 前端 http://localhost:7100（Vite）
```

打开方式：

- 轻量模式（lite）（默认）：`http://localhost:7100/` —— 全部数据在前端内存，刷新还原
- 完整模式（pro）：`http://localhost:7100/?backend_mode=pro` —— 数据来自后端，编辑写回 YAML
- 也可在「管理 → ⚙ 后端设置」中切换并保存（URL 参数优先级最高）

模式判定优先级：**URL 参数 > localStorage > 默认 lite**（CLI 环境再叠加 `KN_BACKEND_MODE` / `KN_BACKEND_URL` 环境变量）。

## 架构

```
┌──────────────────────────── 前端（React 19 + Zustand + Vite）────────────────────────────┐
│  views/          五个视图组件                                                            │
│  store/          Zustand 状态（card / navNode / tree / nav / plan / browse / search）    │
│  data/           共享数据源（cognitiveCards / allNavNodes，const 数组原地变更）          │
│  api/            BackendAdapter（超时+重试）· syncFromBackend（水合）· writeThrough     │
│  config/backend  模式配置（lite / pro）                                              │
└──────────────────────────────┬─────────────────────────────────────────────────────────┘
│                               │ HTTP（仅完整模式（pro））
┌──────────────────────────────┴─────────────────────────────────────────────────────────┐
│  后端（FastAPI，端口 8171）                                                            │
│  routers/  cards · nodes · connections · plan · browse · search · ai · graph · yaml   │
│  store.py  YAML 数据存取（backend/data.yaml，gitignored）                              │
│  cli.py    命令行客户端（与前端 CLI API 同构）                                         │
└──────────────────────────────┬─────────────────────────────────────────────────────────┘
                               │ OpenAI 兼容接口
                    LM Studio http://localhost:1234（嵌入 + 生成，均可降级）
```

## 双模式设计

每条链路都同时具备**轻量计算**与**后端计算**两条路径，完整链路失败时自动回退轻量，界面永远可用：

| 链路 | 轻量模式（lite） | 完整模式（pro） | 完整模式（pro）失败回退 |
|---|---|---|---|
| 启动数据读取 | 内置静态数据（18 卡 / 17 节点） | `GET /api/cards` + `GET /api/nodes` 水合全部 store | 保留静态数据 |
| 卡片 / 节点增删改 | 内存变更 | 写透传 `POST/PUT/DELETE /api/cards|nodes`（火忘） | `console.warn`，下次水合对齐 |
| 路线规划 | `routePlanner.ts`（排列/贪心/衔接/子路径拼接） | `/api/plan/generate` · `/replan`（Python 镜像算法） | 轻量算法重算 |
| 浏览会话 | `bound_cards` 轻量派生，翻页钳位 | `/api/browse/start|next|prev|waypoint`，到底循环 | 轻量派生 |
| 关键词搜索 | 轻量加权子串评分 | 同左（卡片已水合，同一份数据） | — |
| 向量语义搜索 | 轻量词袋重叠率近似 | `/api/search/vector-match`：LM Studio 嵌入余弦 Top-8 | 轻量词袋 |
| AI 辅助生成 | —（仅完整模式（pro）可用） | `/api/ai/generate/*`：LM Studio qwen，失败模板降级 | 模板文案 |

已知语义差异（如实记录）：

- 浏览翻页 / 切站：完整**循环**，轻量**钳位**停住
- 浏览卡片 weight：完整为连接权重求和，轻量为递减启发式
- 轻量词袋对无空格中文长句匹配能力弱（近似算法的固有局限）

## 后端 API 一览

| 分组 | 端点 | 说明 |
|---|---|---|
| 健康 | `GET /api/health` | 状态 + 卡片/节点计数 |
| 卡片 | `GET/POST /api/cards`，`GET/PUT/DELETE /api/cards/{id}`，`…/corpus` 系列 | id 为层级路径（`root/6/1`），删除级联清理节点绑定 |
| 节点 | `GET/POST /api/nodes`，`GET/PUT/DELETE /api/nodes/{id}`，`…/bind-card`、`…/next` 系列 | 删除级联清理连接与卡片绑定 |
| 连接 | `GET /api/connections/status/{from}/{to}`，`POST /ensure`、`POST /fill-all`，`PUT/DELETE /{from}/{to}` | 快速途经点连接补齐 |
| 规划 | `POST /api/plan/generate`，`GET /api/plan/plans[/{id}]`，`POST …/select`，`POST /replan` | 会话态存服务端内存 |
| 浏览 | `POST /api/browse/start`，`GET /status`、`GET /cards`，`POST /next|prev|waypoint` | 会话态存服务端内存 |
| 搜索 | `POST /api/search/query`，`POST /api/search/vector-match` | 向量 = LM Studio 嵌入，降级关键词 |
| AI | `POST /api/ai/generate/{card-title|card-desc|node-label|node-desc}` | LM Studio qwen，模板降级 |
| 图 | `GET /api/graph/nodes`、`GET /api/graph/edges`、`POST /api/graph/sync` | 导航图查询与同步 |
| YAML | `GET /api/yaml/export`，`POST /api/yaml/validate|preview|import` | 导入校验 / 预览 / 导出 |
| 视图 | `GET /api/view/current`，`POST /api/view/switch` | CLI 场景视图状态 |

LM Studio 配置（`routers/search.py` / `routers/ai.py` 顶部常量）：

- 嵌入候选：`text-embedding-qwen3-embedding-0.6b` → `text-embedding-nomic-embed-text-v1.5`（按序尝试）
- 生成：`local-model`（qwen3.5-9b 等已加载模型）

## 数据

- `backend/data.yaml`：唯一持久化文件（卡片 37 / 节点 25，含心智工具箱 8 节点环路），gitignored
- `scripts/generate-mind-toolbox-yaml.py`：从 `cognitive-cards` 目录的认知卡片与「锦囊」生成导航节点 YAML 并导入后端

## 开发验证

```bash
npx tsc --noEmit && npx vite build   # 前端类型检查 + 构建
python backend/cli.py --help         # 后端 CLI（与 API 同构）
curl http://localhost:8171/api/health
```

## 文档索引

- 总览：[项目理解总览.md](项目理解总览.md) · 数据模型：[data-model.md](data-model.md)
- 后端：[backend-architecture.md](backend-architecture.md) · [backend-implementation.md](backend-implementation.md) · [backend-cli-api.md](backend-cli-api.md)
- 视图：[five-tab-layout.md](five-tab-layout.md) · [search-match-mode.md](search-match-mode.md) · [canvas-navigation-design.md](canvas-navigation-design.md) · [route-planning-view.md](route-planning-view.md) · [nav-node-manager.md](nav-node-manager.md) · [card-editor.md](card-editor.md)
- 功能：[nav-canvas-node-interaction.md](nav-canvas-node-interaction.md) · [quick-waypoint-connection.md](quick-waypoint-connection.md) · [nav-data-import-export.md](nav-data-import-export.md) · [ai-assisted-generation.md](ai-assisted-generation.md) · [mind-toolbox-import.md](mind-toolbox-import.md)
- 运维：[dev-startup-scripts.md](dev-startup-scripts.md) · 规范：[design.md](design.md) · [feature-spec-react.md](feature-spec-react.md) · [react-migration-plan.md](react-migration-plan.md) · [cli-api-spec.md](cli-api-spec.md)
