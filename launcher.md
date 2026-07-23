# Launcher：三项目统一接入层

一个轻量 Web 服务，作为 card、coze-studio、cognitive-cards 的套壳入口，通过 CLI 和 REST API 协同三个项目，将完整认知管道封装为一键可达的快捷入口。

---

## 定位

```
                          ┌─────────────────┐
         CLI  ──────────▶ │                 │
                          │    Launcher     │
         Web  ──────────▶ │   (接入层套壳)    │
                          │                 │
         API  ──────────▶ │                 │
                          └───────┬─────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
               ┌────────┐  ┌───────────┐  ┌──────────────┐
               │  card  │  │coze-studio│  │cognitive-    │
               │  L1    │  │  L2       │  │cards L3      │
               └────────┘  └───────────┘  └──────────────┘
```

Launcher 不承载业务逻辑，只做三件事：**路由**（将输入分发到对应项目）、**编排**（串联多步管道）、**呈现**（统一格式化输出）。三个子项目各自独立运行，Launcher 通过内部 API 或进程调用与其通信。

---

## CLI：命令行快捷入口

统一命令前缀 `lobster`，按项目分命名空间。

### 全管道命令

```bash
# 从困境描述出发，跑完整三阶段管道
lobster run "在多人聚会中不知道该说什么"

# 指定阶段范围
lobster run "对公开演讲感到恐惧" --from card --to studio

# 仅生成信号，不做沉浸演绎
lobster run "害怕拒绝别人的请求" --stop-at card
```

管道自动执行：
1. **card** 接收困境描述 → 匹配卡牌信号与策略
2. **coze-studio** 接收信号 → 生成沉浸叙事/场景/对话
3. **cognitive-cards** 接收叙事 + 用户状态 → 产出注意力锦囊

### card 命名空间

```bash
lobster card list                          # 列出所有卡牌
lobster card show 借刀杀人                  # 查看卡牌详情、策略、隐喻
lobster card match "朋友找我帮忙但我办不到"   # 困境 → 匹配最合适的卡牌
lobster card routes 借刀杀人               # 展开卡牌的主力/辅助路线
lobster card signal "借刀杀人" --route 辅助  # 导出简化信号（供 studio 消费）
```

### studio 命名空间

```bash
lobster studio narrate --signal <signal.json>     # 信号 → 沉浸叙事
lobster studio scene --card 借刀杀人 --route 主力   # 跳过 signal，直接生成场景
lobster studio dialog --scene-id <id>              # 为指定场景生成对话
lobster studio workflow list                       # 列出可用工作流
lobster studio workflow run <workflow> --input <file>
```

### cognitive 命名空间

```bash
lobster cognitive nudge                       # 获取一枚注意力锦囊
lobster cognitive nudge --context "正要开始一段重要对话"
lobster cognitive state                        # 查看当前认知状态
lobster cognitive anchor --sense 听觉           # 获取指定感官锚点
lobster cognitive flywheel start               # 启动注意力飞轮
lobster cognitive flywheel status              # 飞轮运行状态
lobster cognitive card list                    # 列出 10 张认知卡片
lobster cognitive card show 1                  # 查看指定认知卡片
```

### 快捷别名

```bash
lobster l              # lobster card list
lobster n               # lobster cognitive nudge
lobster run             # 全管道运行
```

---

## REST API

基础路径 `http://localhost:8412/api/v1`。

### 管道

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/pipeline/run` | 提交困境描述，触发全管道 |
| GET | `/pipeline/status/{run_id}` | 查询管道运行状态 |
| GET | `/pipeline/result/{run_id}` | 获取管道完整产物 |
| POST | `/pipeline/run` | `?stages=card,studio` 指定阶段 |

**请求体：**

```json
{
  "input": "在多人聚会中不知道该说什么",
  "stages": ["card", "studio", "cognitive"],
  "options": {
    "card": { "max_matches": 3 },
    "studio": { "workflow": "default_narrative", "format": "scene+dialog" },
    "cognitive": { "nudge_count": 3 }
  }
}
```

**响应：**

```json
{
  "run_id": "r_20260723_001",
  "status": "completed",
  "stages": {
    "card": {
      "matched": [
        { "name": "社交破冰", "confidence": 0.87, "signal": { ... } },
        { "name": "借刀杀人", "confidence": 0.72, "signal": { ... } }
      ]
    },
    "studio": {
      "scene": { "title": "...", "description": "...", "characters": [...] },
      "dialog": [ ... ]
    },
    "cognitive": {
      "nudges": [ { "sense": "触觉", "cue": "..." }, ... ],
      "anchor": { ... }
    }
  }
}
```

### card

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/card/list` | 卡牌列表 |
| GET | `/card/{name}` | 卡牌详情 |
| POST | `/card/match` | 困境匹配卡牌 |
| GET | `/card/{name}/signal?route=main` | 导出简化信号 |

### studio

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/studio/narrate` | 信号 → 沉浸叙事 |
| POST | `/studio/scene` | 直接生成场景 |
| GET | `/studio/workflows` | 可用工作流列表 |
| POST | `/studio/workflow/{name}/run` | 运行指定工作流 |

### cognitive

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/cognitive/nudge?context=...` | 获取一枚锦囊 |
| GET | `/cognitive/state` | 当前认知状态 |
| POST | `/cognitive/flywheel/start` | 启动注意力飞轮 |
| GET | `/cognitive/flywheel/status` | 飞轮状态 |
| GET | `/cognitive/cards` | 10 张认知卡片列表 |
| GET | `/cognitive/cards/{id}` | 认知卡片详情 |

---

## Web Dashboard

浏览器打开 `http://localhost:8412`，提供三栏控制面板。

### 面板布局

```
┌──────────────────────────────────────────────────────────────┐
│  Launcher                                          [⚙ 设置]  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─ 快速启动 ──────────────────────────────────────────────┐ │
│  │                                                         │ │
│  │  描述你当前的困境或需求：                                 │ │
│  │  ┌─────────────────────────────────────────────────┐    │ │
│  │  │                                                 │    │ │
│  │  └─────────────────────────────────────────────────┘    │ │
│  │  [ 全管道运行 ]  [ 仅匹配卡牌 ]  [ 仅生成叙事 ]           │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌─ card ───────────────┐ ┌─ studio ──────────────┐         │
│  │                      │ │                       │         │
│  │  匹配结果             │ │  生成叙事              │         │
│  │  ├ 社交破冰 87%      │ │  ├ 场景：《聚会...》   │         │
│  │  ├ 借刀杀人 72%      │ │  ├ 角色：A, B, C      │         │
│  │  └ 角色扮演 58%      │ │  └ 对话：42 段         │         │
│  │                      │ │                       │         │
│  │  [展开信号] [导出]    │ │  [预览] [重新生成]     │         │
│  └──────────────────────┘ └───────────────────────┘         │
│                                                              │
│  ┌─ cognitive ───────────────────────────────────────────┐  │
│  │                                                        │  │
│  │  锦囊 #1  触觉·握拳三秒   │ 飞轮状态 ● 运行中           │  │
│  │  锦囊 #2  听觉·深呼吸     │ 当前卡片：悖论绕过          │  │
│  │  锦囊 #3  视觉·焦点转移   │ 锚点：手腕皮筋             │  │
│  │                                                        │  │
│  │  [换一枚锦囊]  [暂停飞轮]                               │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─ 管道历史 ──────────────────────────────────────────────┐ │
│  │  r_001  "聚会焦虑"           card✓ studio✓ cog✓  2min前  │ │
│  │  r_002  "拒绝恐惧"           card✓ studio✗        5min前  │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

---

## 技术选型

| 考虑 | 选择 | 原因 |
|------|------|------|
| 语言 | Go（Hertz 框架） 或 Python（FastAPI） | 与现有项目栈一致：coze-studio 用 Go，cognitive-cards 用 Python |
| CLI 框架 | Cobra (Go) / Click (Python) | 成熟稳定的命令行框架 |
| Web 前端 | 内嵌静态页面，HTMX + 极简 CSS | 不引入重前端框架，Launcher 只是操作面板 |
| 子项目通信 | HTTP 内部调用 或 subprocess | card 是文档，可进程内读取；coze-studio 和 cognitive-cards 通过各自 API 调用 |
| 管道编排 | 简单的顺序编排器（内置） | 管道阶段是线性依赖的，不需引入 workflow engine |
| 配置 | YAML config file | 统一管理三个子项目的地址、端口、参数 |

### 子项目通信方案

```
Launcher
   │
   ├─ card (Markdown 文档)  →  直接进程内读取、解析卡牌规则文件
   │                          或通过本地文件 watch 保持同步
   │
   ├─ coze-studio (Go 微服务) →  HTTP 调用其内部 API
   │                              POST /api/workflow/run
   │
   └─ cognitive-cards (Flask) →  HTTP 调用其 API
                                  GET /api/nudge
                                  POST /api/flywheel/start
```

---

## 启动方式

```bash
# 开发模式
cd launcher
go run main.go --config config.yaml

# 或 Python
python launcher.py --config config.yaml

# 全局 CLI 安装后
lobster --help
lobster run "在会议上不敢表达不同意见"
```

`config.yaml` 示例：

```yaml
server:
  host: 0.0.0.0
  port: 8412

projects:
  card:
    path: ../card
    index_file: index.md
  studio:
    base_url: http://localhost:8888
    api_prefix: /api
  cognitive:
    base_url: http://localhost:5000
    api_prefix: /api

pipeline:
  timeout: 120s
  default_stages: [card, studio, cognitive]
```

---

## 设计原则

1. **薄壳**：Launcher 不做业务逻辑，只做路由 + 编排 + 格式化。任何属于 card/studio/cognitive 领域的能力，下沉到对应项目。
2. **同步 + 异步双模**：`POST /pipeline/run` 返回 `run_id`，前端轮询或通过 SSE 获取进度。CLI 模式下可等待阻塞输出。
3. **渐进连接**：任一子项目不可用时，管道降级运行（如 card 可用、studio 不可用时，CLI 仅输出卡牌信号）。
4. **统一输出格式**：无论 CLI 还是 API，管道产物的 JSON schema 一致，方便下游消费。
