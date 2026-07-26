# 后端 Python CLI 与 API 客户端

> 为 FastAPI 后端全部十组功能提供 Python 调用入口：
> `backend/app/client.py`（API 客户端 SDK）+ `backend/cli.py`（命令行）。
> 与 TS 版 kn-cli 并列：TS CLI 面向前端轻量/完整双模式，本 CLI 直连后端 HTTP。

## 一、API 客户端（app/client.py）

```python
import sys; sys.path.insert(0, "backend")
from app.client import BackendClient

client = BackendClient()                       # 默认 http://localhost:8171
client.health()                                # {'status': 'ok', 'cards': 37, ...}
cards = client.list_cards()                    # 全部认知卡片
node  = client.get_node("node-kit-a")          # 单个导航节点
plans = client.generate_plans(["node-kit-a", "node-kit-e", "node-kit-g"])
```

- 方法与服务端路由一一对应（50+ 个），卡片 id 含斜杠（`root/7/1`）自动 `%2F` 编码
- 非 2xx 抛出 `BackendError(status, message)`；连接失败 `status = -1`
- 超时默认 15s，可通过 `BackendClient(base_url, timeout=...)` 调整

## 二、命令行（backend/cli.py）

前置：后端已启动（`python backend/run.py` 或 `start-dev.bat` / `start-dev.ps1`）。

全局参数：`--url` 后端地址（或环境变量 `KN_BACKEND_URL`）；`--json` 输出原始 JSON。

### 命令总览

| 组 | 子命令 | 示例 |
|----|--------|------|
| health | — | `python backend/cli.py health` |
| card | `list / get / create / update / delete / children` | `card create --parent root/7 --title 新卡片` |
| | `corpus-list / corpus-add / corpus-update / corpus-remove` | `card corpus-add root/7/1 "语料文本"` |
| node | `list [--query] / get / create / update / delete` | `node create --label 新节点` |
| | `bind / unbind / next / next-add / next-update / next-remove / prev / history` | `node next-add node-kit-a node-kit-c --priority 2` |
| graph | `nodes / edges / sync` | `graph edges` |
| plan | `generate / list / get / select / replan` | `plan generate --ids node-kit-a,node-kit-e,node-kit-g` |
| browse | `start / status / cards / next / prev / waypoint` | `browse start --plan plan-0` |
| search | `query / vector` | `search query 机器学习 --mode keyword` |
| yaml | `export [--file] / validate / preview / import` | `yaml import imports/cognitive-cards-kits.yaml` |
| ai | `card-title / card-desc / node-label / node-desc` | `ai card-title root/7/1` |
| conn | `status / ensure / update / remove / fill-all` | `conn fill-all node-kit-a,node-kit-e,node-kit-g` |
| view | `get / set` | `view set plan` |

### 输出约定

- 成功：`✓ ...`；失败：`✗ ...`（stderr，退出码 1）
- 优先级展示沿用 `#N` 序号（内部自动换算 preset_weight）
- `--json` 适合管道处理：`python backend/cli.py --json card list | jq length`

## 三、验证结果（2026-07-26，真实后端全量实测）

- **11 个命令组全部通过**：卡片 CRUD + 语料增删改、节点 CRUD + 绑定/连接管理、
  图查询与重算、规划三候选（Plan A 0.95 推荐）、浏览全流程、关键词/向量搜索、
  YAML 导出→校验→预览（覆盖 19/8 正确识别）、AI 生成（LM Studio 在线出真实结果）、
  连接 ensure/fill-all/remove、视图切换
- 写操作测试均已清理（测试卡片/节点/连接用后即删），数据保持 37 卡片 / 25 节点
- 修复点：yaml 子命令文件路径支持位置参数（与 TS CLI 行为一致）

## 四、两套 CLI 的分工

| | TS kn-cli（`npm run kn-cli`） | Python CLI（`backend/cli.py`） |
|--|------------------------------|-------------------------------|
| 实现 | tsx + Zustand / BackendAdapter | requests → HTTP |
| 轻量模式（lite） | ✓（内存数据源，无需后端） | ✗（必须启动后端） |
| 完整模式（pro） | ✓（KN_BACKEND_MODE=pro） | ✓（默认即完整） |
| 会话态 | 每次进程独立 | 浏览进度保存在服务端，跨调用连续 |
| 适用 | 前端开发调试、无后端快速验证 | 后端联调、脚本自动化、运维 |
