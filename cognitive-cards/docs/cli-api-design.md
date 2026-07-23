# 涌现引擎 CLI & API 设计

基于三阶段涌现管道（语义匹配 → 语料库细化 → 锦囊路径涌现）的 CLI 命令行工具和 REST API 设计实现。

---

## 1. 三阶段与接口映射

```
用户输入
    │
    ▼
┌─ 阶段一：语义匹配 ─────────────────────────────────────┐
│  API:  POST /api/emergence/match                       │
│  CLI:  cognitive match "text"                          │
│  输入: 用户自然语言文本                                  │
│  输出: matched_cards[] + user_state_analysis           │
└───────────────────────────────────────────────────────┘
    │
    ▼
┌─ 阶段二：语料库细化 ───────────────────────────────────┐
│  API:  POST /api/emergence/refine                      │
│  CLI:  cognitive refine "text" [--card-id card_05]     │
│  输入: 用户文本 + 匹配卡片 ID                           │
│  输出: refined_corpus[] (语料子集 + 风格匹配 + 评分)    │
└───────────────────────────────────────────────────────┘
    │
    ▼
┌─ 阶段三：锦囊路径涌现 ─────────────────────────────────┐
│  API:  POST /api/emergence (全管道)                     │
│  CLI:  cognitive emerge "text"                         │
│  输入: 用户文本                                         │
│  输出: emergent_kit (引导词+身体动作) + predicted_path   │
└───────────────────────────────────────────────────────┘
```

---

## 2. CLI 命令参考

### 安装

```bash
cd cognitive-cards
pip install -r requirements.txt
```

CLI 脚本 `cli.py` 零依赖（仅用 Python 标准库），通过 HTTP 与本地运行的 server.py 通信。

### 命令总览

```
cognitive <command> [options]

命令：
  run       完整三阶段管道（= emerge）
  match     阶段一：语义匹配卡片
  refine    阶段二：细化语料库
  emerge    阶段三：锦囊路径涌现
  cards     卡片管理（list / show）
  kits      锦囊管理（list / show）
  corpus    语料库浏览（list）
  health    服务健康检查
```

### 阶段命令详情

#### `cognitive run <text>` — 完整管道

```bash
cognitive run "最近总是设定目标又拖延，每次开始前都觉得自己准备不够"
cognitive run "在多人聚会中不知道该说什么" --format json
cognitive run "害怕拒绝别人的请求" -f pretty
```

完整输出包含三个阶段的所有结果：匹配卡片、细化语料、锦囊引导词、身体动作、预测路径、警告。

#### `cognitive match <text>` — 阶段一：语义匹配

```bash
cognitive match "越准备越焦虑，迟迟无法开始"
```

输出：

```
═══════════════════════════════════════════
  语义匹配结果
═══════════════════════════════════════════

  ★ Card 05 · 合拍飞轮  置信度 0.654
    用户描述的是设定目标后无法进入执行状态，属于合拍飞轮的启动问题

  · Card 10 · 重新定向能量  置信度 0.375
    输入与"重新定向能量"存在一定关联

  用户状态分析:
    心态: 设计者心态
    位置: 在执行者入口处受阻
    风险: ['过度准备', '拖延启动']
```

选项：
- `-f, --format json` — JSON 输出
- `--server URL` — 指定服务地址

#### `cognitive refine <text>` — 阶段二：语料库细化

```bash
cognitive refine "越准备越焦虑" --card-id card_05
cognitive refine "越准备越焦虑"                # 自动先匹配卡片
```

输出：

```
═══════════════════════════════════════════
  语料库细化 · card_05「合拍飞轮」
═══════════════════════════════════════════

  [0.87] "飞轮启动前最安静的时刻，恰恰是最需要信任的时刻..."
         风格: 诗意_温和, 简洁
         关键词: 启动, 信任, 阻力

  [0.82] "每一次预热都不是浪费，而是在告诉你的神经系统：安全了，可以开始了。"
         风格: 温暖, 清晰
         关键词: 预热, 过渡, 开始, 安全
```

#### `cognitive emerge <text>` — 阶段三：锦囊涌现

```bash
cognitive emerge "越准备越焦虑"
```

输出：

```
═══════════════════════════════════════════
  锦囊路径涌现
═══════════════════════════════════════════

  📦 锦囊 B · 迷失预警

  你描述的那种"越准备越焦虑"的感觉，我认得它。

  这不是你准备不够——是你的设计者心态（过度准备）太早入场了...

  现在，站起来，走三步。不是去做什么事——只是走三步，
  感受脚底踩到地板的感觉。三步之后，你会发现那个"准备"的声音安静了一些。

  就在那个安静里，开始。

  🏃 身体动作: 站起来，走三步，感受脚底踩到地板的感觉

  ─────────────────────────────────────────
  预测路径:
    1. 锦囊 B · 迷失预警       → 正常化感受，用身体感官绕过语义焦虑
    2. 锦囊 E · 回归执行者     → 进入执行者心态，信任预设路径
    3. 锦囊 F · 具身认知临战   → 沉浸于处境，让认知自发涌现
    4. 锦囊 G · 复盘提取       → 从环境级优化角度复盘

  ⚠️  当前阶段禁止提前复盘（kit_h 风险）
  ⚠️  在未经历执行者具身前不要跳到设计者心态
```

### 管理命令

```bash
cognitive cards list              # 列出所有 10 张认知卡片
cognitive cards show card_05      # 查看卡片详情
cognitive cards show 05           # 支持编号简写

cognitive kits list               # 列出全部 8 枚锦囊
cognitive kits show kit_b         # 查看锦囊详情

cognitive corpus list             # 列出全部语料条目
cognitive corpus list card_05     # 按卡片过滤语料

cognitive health                  # 检查服务状态
```

---

## 3. REST API 新增端点

在现有 `server.py` 基础上，新增以下端点以支持按阶段调用：

### 阶段一：语义匹配

```
POST /api/emergence/match
```

| 字段 | 类型 | 说明 |
|------|------|------|
| text | string | 用户输入文本 |
| source | string | 来源标识（chat/note/reflection） |
| top_k | int | 返回匹配数，默认 3 |

```json
// 请求
{ "text": "越准备越焦虑", "source": "cli", "top_k": 2 }

// 响应
{
  "matched_cards": [
    { "card_id": "card_05", "number": "05", "title": "合拍飞轮", "confidence": 0.654, "reason": "..." }
  ],
  "user_state_analysis": {
    "dominant_mindset": "设计者心态",
    "cycle_position": "在执行者入口处受阻",
    "risk_signals": ["过度准备", "拖延启动"]
  }
}
```

### 阶段二：语料库细化

```
POST /api/emergence/refine
```

| 字段 | 类型 | 说明 |
|------|------|------|
| text | string | 用户输入文本 |
| card_id | string | 目标卡片 ID（必填） |
| top_n | int | 返回条目数，默认 5 |

```json
// 请求
{ "text": "越准备越焦虑", "card_id": "card_05", "top_n": 3 }

// 响应
{
  "card_id": "card_05",
  "card_title": "合拍飞轮",
  "user_style_profile": "叙事_内省",
  "entries": [
    { "id": "corpus_05_003", "content": "...", "final_score": 0.87, ... }
  ]
}
```

### 阶段三：完整管道（现有，不变）

```
POST /api/emergence
```

> 该端点已存在于 server.py，同时作为全管道入口。CLI 的 `run` 和 `emerge` 命令复用此端点。

---

## 4. CLI 实现架构

```
cli.py (stdlib only, no extra deps)
   │
   │  HTTP (urllib)
   ▼
server.py (FastAPI, localhost:8170)
   │
   ├── POST /api/emergence          ← 全管道
   ├── POST /api/emergence/match    ← 阶段一 (新增)
   ├── POST /api/emergence/refine   ← 阶段二 (新增)
   ├── GET  /api/cards              ← 卡片列表
   ├── GET  /api/kits               ← 锦囊列表
   ├── GET  /api/corpus             ← 语料库
   └── GET  /api/health             ← 健康检查
```

CLI 使用 `argparse` 子命令模式，向服务器发送 HTTP 请求，解析 JSON 响应并格式化输出。支持：
- `--format json` / `-f json`：输出原始 JSON
- `--format pretty` / `-f pretty`（默认）：结构化美化输出
- `--server URL`：指定服务器地址，默认 `http://localhost:8170`

---

## 5. 降级与容错

| 场景 | CLI 行为 |
|------|----------|
| 服务器未启动 | 提示启动命令 `python server.py` |
| 输入 < 3 字符 | 返回 400 错误，提示多描述一些 |
| 无匹配卡片 | 降级返回第一张卡片，置信度 0.1 |
| LLM 不可用（远期） | 降级为关键词硬匹配 + 默认锦囊文案 |
| 网络超时 | 5 秒超时，提示重试 |

---

## 6. 与 Launcher 的集成

`cognitive` CLI 可作为 Launcher 的子命令注册：

```bash
lobster cognitive match "text"      # Launcher 转发到 cognitive-cards CLI
lobster cognitive emerge "text"     # 同上
```

或 Launcher 直接调用 cognitive-cards 的 HTTP API：

```
Launcher ──HTTP──▶ cognitive-cards server.py (localhost:8170)
                 POST /api/emergence
                 POST /api/emergence/match
                 POST /api/emergence/refine
```
