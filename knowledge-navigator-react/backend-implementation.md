# 后端实现方案 · Python FastAPI 骨架

> 依据 `backend-architecture.md` §4.2 路由结构与 §4.3 持久化策略实现。
> 本文档记录骨架的落地方案、目录结构、数据流与验证方式。

## 一、目标

让前端「完整模式（pro）」真正可用：启动本地 FastAPI 服务（端口 8171）后，
前端管理界面切换到完整模式（pro）即可通过 HTTP 完成全部数据操作，
数据以 YAML 文件持久化在服务端，重启不丢失。

## 二、技术选型

| 项 | 选择 | 说明 |
|----|------|------|
| 框架 | FastAPI 0.115 + uvicorn | 与架构文档约定一致 |
| 数据格式 | YAML（与导入导出格式同源） | `backend/data.yaml` |
| 初始数据 | `backend/seed.yaml` | 由前端 CLI `yaml export` 生成，保证与内置数据完全一致 |
| 持久化时机 | 每次写操作后立即落盘 | 开发阶段简单可靠 |
| CORS | 放开全部来源 | 本地开发场景 |
| 运行环境 | 用户系统 Python（miniconda 3.13） | 已安装 fastapi / uvicorn / pyyaml |

## 三、目录结构

```
backend/
├── run.py              # 启动入口：uvicorn app.main:app --port 8171
├── requirements.txt    # fastapi / uvicorn / pyyaml
├── seed.yaml           # 初始数据（首次启动时复制为 data.yaml）
└── app/
    ├── main.py         # FastAPI 实例、CORS、路由挂载、/api/health
    ├── store.py        # DataStore：内存数据 + YAML 落盘 + 全局锁
    ├── domain.py       # 领域逻辑：权重合成、优先级映射、图边推导、路径派生
    └── routers/
        ├── cards.py        # /api/cards
        ├── nodes.py        # /api/nodes
        ├── graph.py        # /api/graph
        ├── plan.py         # /api/plan（排列 + 贪心 + 连接路径算法）
        ├── browse.py       # /api/browse（会话态保存在服务端内存）
        ├── search.py       # /api/search（关键词加权评分）
        ├── yaml_io.py      # /api/yaml（导出 / 校验 / 预览 / 导入）
        ├── ai.py           # /api/ai/generate/*（LM Studio 代理 + 本地降级）
        ├── connections.py  # /api/connections
        └── view.py         # /api/view
```

## 四、关键设计

### 4.1 路径参数中的斜杠

认知卡片 id 形如 `root/1/2`，前端以 `encodeURIComponent` 编码为 `root%2F1`。
所有卡片路由使用 FastAPI 路径转换器 `{card_id:path}` 捕获，确保斜杠 id 可用。

### 4.2 与前端一致的领域规则

- **优先级映射**：UI 优先级 `#N` ↔ `preset_weight = 1 - (N-1) * 0.1`（#11+ → 0.05）
- **权重合成**（`composeWeights`）：user_overrides > preset_weight 降序 > browse_weight 降序（mixed 模式），同一 target 取序号最小者
- **新建 id**：卡片 = 父路径下最大序号 + 1；节点 = `node-custom-N` 递增不冲突
- **级联删除**：删卡片清理所有节点 `bound_cards` 引用；删节点清理所有出向引用与卡片 `bound_nodes`
- **路线规划**：途经点 ≤ 7 用全排列，否则贪心；补充 connection / subpath 候选

### 4.3 会话态归属

浏览进度（当前站点 / 卡片下标）与当前视图保存在**服务端内存**
（与完整模式（pro）的语义一致：刷新前端不丢失浏览进度），不写入 YAML。

### 4.4 AI 生成

`POST /api/ai/generate/{card-title|card-desc|node-label|node-desc}`：
优先代理本机 LM Studio（`http://localhost:1234/v1/chat/completions`，8s 超时）；
不可用或失败时降级为模板化本地生成，保证端点始终可用。

## 五、启动与验证

```bash
# 启动（系统 Python）
python backend/run.py

# 健康检查
curl http://localhost:8171/api/health

# 前端切换完整模式（pro）：管理界面 ⚙ → 完整模式（pro）→ 测试连接 → 保存
# 或 URL 参数：?backend_mode=pro&backend_url=http://localhost:8171
```

CLI 验证（完整模式（pro））：

```bash
set KN_BACKEND_MODE=pro
kn-cli card list
kn-cli plan generate --ids node-ml-foundation,node-supervised
```
