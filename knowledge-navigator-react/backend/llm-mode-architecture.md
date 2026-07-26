# LLM 双模式架构：后端直连与 Coze Studio 代理

## 概述

Knowledge Navigator 的 AI 生成能力需要 LLM 支撑。为此设计**双模式架构**：

- 前端：`lite`（轻量 Store）/ `pro`（后端 API）双模式 → 由 `backend-architecture.md` 定义
- 后端的 LLM 模块：`backend_mode`（直连 LM Studio）/ `coze_api_mode`（经 Coze Studio Workflow）双模式 → **本文定义**

```
                    ┌─────────────────────────────────┐
                    │          前端 (React)            │
                    │   ┌───────────────────────────┐  │
                    │   │  lite mode: 直接操作 Store │  │
                    │   │  pro mode: 调用后端 API  │  │
                    │   └───────────────────────────┘  │
                    └──────────────┬──────────────────┘
                                   │ POST /api/ai/generate/{endpoint}
                                   ▼
                    ┌─────────────────────────────────┐
                    │       Python 后端 (FastAPI)      │
                    │   ┌───────────────────────────┐  │
                    │   │  LLM 模块                  │  │
                    │   │                           │  │
                    │   │  ┌─ backend_mode ───────┐ │  │
                    │   │  │  直连 LM Studio      │ │  │
                    │   │  │  localhost:1234      │ │  │
                    │   │  └──────────────────────┘ │  │
                    │   │          或                │  │
                    │   │  ┌─ coze_api_mode ──────┐ │  │
                    │   │  │  经 Coze Studio       │ │  │
                    │   │  │  Workflow API 间接调用 │ │  │
                    │   │  │  LM Studio            │ │  │
                    │   │  └──────────────────────┘ │  │
                    │   └───────────────────────────┘  │
                    └─────────────────────────────────┘
```

---

## 1. 整体架构

### 1.1 数据流

```
用户操作（前端）
    │
    ├── 轻量模式（lite）
    │      └── Zustand Store（前端内存）
    │            └── AI 生成：调用后端 /api/ai/generate/*（需后端运行）
    │
    └── 完整模式（pro）
           └── Python 后端 API
                 └── LLM 模块
                       ├── backend_mode → LM Studio (localhost:1234)
                       └── coze_api_mode → Coze Studio Workflow
                                             └── Workflow LLM 节点 → LM Studio
```

### 1.2 两种 LLM 模式对比

| 维度 | backend_mode | coze_api_mode |
|------|-------------|---------------|
| 路径 | Python 后端 → LM Studio | Python 后端 → Coze Studio → Workflow → LM Studio |
| 跳数 | 1 跳 | 2 跳 |
| 依赖 | 仅需 LM Studio 运行 | 需 Coze Studio 后端 + Workflow 已发布 |
| 灵活性 | 固定提示词模板 | Workflow 内可编排 LLM + Code + 条件分支等复杂逻辑 |
| 延迟 | 较低（少一跳网络） | 较高（多一跳 + Workflow 引擎开销） |
| 可观测性 | LLM 原始输出 | Workflow Trace 可追踪全链路 |
| 降级方案 | 轻量模板降级 | 降级为 backend_mode 或轻量模板 |

---

## 2. 配置机制

### 2.1 环境变量

在 `backend/.env` 或系统环境变量中配置：

```bash
# ── LLM 模式 ──
LLM_MODE=backend_mode           # backend_mode | coze_api_mode

# ── backend_mode 配置（直连 LM Studio） ──
LM_STUDIO_URL=http://localhost:1234/v1/chat/completions
LM_TIMEOUT=8

# ── coze_api_mode 配置（经 Coze Studio Workflow） ──
COZE_API_BASE=http://localhost:8888          # Coze Studio Go 后端地址
COZE_API_KEY=                                # API Key（如需要鉴权）
COZE_WORKFLOW_ID=                            # Workflow ID（发布后获得）
COZE_API_TIMEOUT=30
```

### 2.2 动态切换

LLM 模块在启动时读取 `LLM_MODE` 环境变量决定使用哪种模式，运行时可通过 API 切换：

```
GET  /api/ai/mode          ← 查看当前 LLM 模式
POST /api/ai/mode          ← 切换 LLM 模式
```

**请求体：**
```json
{
  "mode": "coze_api_mode"
}
```

**响应：**
```json
{
  "ok": true,
  "mode": "coze_api_mode",
  "previous_mode": "backend_mode"
}
```

---

## 3. backend_mode：直连 LM Studio

### 3.1 架构

```
Python 后端 (FastAPI)
    │
    ├── /api/ai/generate/{endpoint}
    │      ↓
    │   _lm_generate(prompt)
    │      ↓
    ├── urllib.request → LM Studio (localhost:1234)
    │      ↓
    │   /v1/chat/completions (OpenAI 兼容接口)
    │      ↓
    └── 成功 → 返回 LLM 输出
        失败 → _fallback() 轻量模板降级
```

### 3.2 现有实现

参见 `backend/app/routers/ai.py`。

核心调用函数 `_lm_generate()`：

```python
LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
LM_TIMEOUT = 8

def _lm_generate(prompt: str) -> str | None:
    payload = json.dumps({
        "model": "local-model",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 120,
    }).encode("utf-8")
    req = urllib.request.Request(LM_STUDIO_URL, data=payload,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=LM_TIMEOUT) as res:
            data = json.loads(res.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return None  # 触发降级
```

### 3.3 降级策略

当 LM Studio 不可用时，使用轻量模板：

| endpoint | 降级策略 |
|----------|----------|
| `card-title` | 取语料第一条前 12 字 + "…"，或返回原标题 |
| `card-desc` | 取语料第一条前 50 字，或返回默认描述 |
| `node-label` | 返回原 label |
| `node-desc` | 返回原 description 或默认描述 |

---

## 4. coze_api_mode：经 Coze Studio Workflow

### 4.1 架构

```
Python 后端 (FastAPI)
    │
    ├── /api/ai/generate/{endpoint}
    │      ↓
    │   _coze_generate(prompt, endpoint)
    │      ↓
    ├── POST /v1/workflow/run → Coze Studio Go 后端 (:8888)
    │      ↓
    │   Workflow Engine (Eino DAG)
    │      ↓
    │   LLM Node → LM Studio（Coze 内部经 OpenAI 兼容协议连接）
    │      ↓
    │   Workflow 执行完毕 → 返回结果
    │      ↓
    └── 成功 → 从 Workflow 输出中提取 result
        失败 → 降级为 backend_mode → 再失败则轻量模板
```

### 4.2 Workflow 设计

需要在 Coze Studio 中创建一个专用的 AI 生成 Workflow：

```
Workflow: "认知卡片 AI 生成"

Entry 节点
  │ 输入: { endpoint: "card-title", context: "..." }
  ▼
LLM 节点
  │ system_prompt: 按 endpoint 使用对应的提示词
  │ user_prompt: "{{context}}"
  │ model: 接入 LM Studio 的 OpenAI 兼容模型
  ▼
Code 节点（可选，清理输出）
  │ 去除引号、多余换行，提取纯文本
  ▼
Exit 节点
  │ 输出: { result: "生成的标题/描述" }
```

提示词与 `backend/app/routers/ai.py` 中的 `PROMPTS` 保持一致：

| endpoint | system_prompt |
|----------|--------------|
| `card-title` | "为以下认知卡片生成一个简洁的中文标题（不超过15字），只输出标题本身" |
| `card-desc` | "为以下认知卡片生成一句中文描述（不超过50字），只输出描述本身" |
| `node-label` | "为以下导航节点生成一个简洁的中文名称（不超过10字），只输出名称本身" |
| `node-desc` | "为以下导航节点生成一句中文描述（不超过50字），只输出描述本身" |

### 4.3 调用 Workflow API

```python
COZE_API_BASE = "http://localhost:8888"
COZE_WORKFLOW_ID = "..."

def _coze_generate(context: str, endpoint: str) -> str | None:
    """通过 Coze Studio Workflow 生成。"""
    url = f"{COZE_API_BASE}/v1/workflow/run"
    payload = json.dumps({
        "workflow_id": COZE_WORKFLOW_ID,
        "parameters": json.dumps({
            "endpoint": endpoint,
            "context": context,
        }),
        "is_async": False,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=COZE_API_TIMEOUT) as res:
            data = json.loads(res.read().decode("utf-8"))
        # Workflow 执行结果在 data.data 中
        execution_data = json.loads(data.get("data", "{}"))
        return execution_data.get("result") or None
    except Exception:
        return None  # 触发降级
```

### 4.4 流式调用（可选）

Coze Studio 也支持流式 Workflow 执行：

```
POST /v1/workflow/stream_run
```

对于需要流式输出（如长文本生成）的场景，可用此端点 + Server-Sent Events。

---

## 5. LLM 模块统一接口

无论哪种模式，LLM 模块对外暴露统一的 `generate()` 函数：

```python
# backend/app/llm.py（新增）

import os
from typing import Any

# ── 配置 ──
LLM_MODE = os.getenv("LLM_MODE", "backend_mode")  # backend_mode | coze_api_mode

# backend_mode 配置
LM_STUDIO_URL = os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1/chat/completions")
LM_TIMEOUT = int(os.getenv("LM_TIMEOUT", "8"))

# coze_api_mode 配置
COZE_API_BASE = os.getenv("COZE_API_BASE", "http://localhost:8888")
COZE_API_KEY = os.getenv("COZE_API_KEY", "")
COZE_WORKFLOW_ID = os.getenv("COZE_WORKFLOW_ID", "")
COZE_API_TIMEOUT = int(os.getenv("COZE_API_TIMEOUT", "30"))


def generate(endpoint: str, entity: dict[str, Any]) -> str:
    """统一入口：按当前模式调用 LLM，失败时降级。"""
    context = _build_context(endpoint, entity)
    prompt = PROMPTS[endpoint].format(context=context)

    if LLM_MODE == "coze_api_mode":
        result = _coze_generate(context, endpoint)
        if result is not None:
            return result
        # coze_api_mode 失败 → 降级到 backend_mode
        result = _lm_generate(prompt)

    else:  # backend_mode
        result = _lm_generate(prompt)
        if result is not None:
            return result
        # backend_mode 失败 → 尝试 coze_api_mode 兜底
        if COZE_WORKFLOW_ID:
            result = _coze_generate(context, endpoint)

    if result is not None:
        return result
    return _fallback(endpoint, entity)
```

### 5.1 降级链路

```
coze_api_mode 降级链路：
  Coze API 可用 → 经 Workflow 调用 LLM
       ↓ 不可用
  降级为 backend_mode → 直连 LM Studio
       ↓ 不可用
  轻量模板降级

backend_mode 降级链路：
  直连 LM Studio
       ↓ 不可用
  尝试 coze_api_mode 兜底（若配置了 COZE_WORKFLOW_ID）
       ↓ 不可用
  轻量模板降级
```

### 5.2 调用方（现有 ai.py 的变更）

原有的 `generate` 路由改为调用 `llm.generate()`：

```python
# backend/app/routers/ai.py（适配）

from ..llm import generate as llm_generate

@router.post("/generate/{endpoint}")
def generate(endpoint: str, body: GenerateBody) -> dict[str, str]:
    if endpoint not in PROMPTS:
        raise HTTPException(status_code=404, detail=f"未知生成类型: {endpoint}")

    is_card = endpoint.startswith("card-")
    entity = store.get_card(body.id) if is_card else store.get_node(body.id)
    if entity is None:
        raise HTTPException(status_code=404, detail=f"{'卡片' if is_card else '节点'} {body.id} 不存在")

    result = llm_generate(endpoint, entity)
    return {"result": result}
```

---

## 6. API 扩展

### 6.1 新增端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/ai/mode` | 获取当前 LLM 模式 |
| POST | `/api/ai/mode` | 切换 LLM 模式 |
| GET | `/api/ai/status` | 查看 LM Studio / Coze API 连通状态 |

#### GET /api/ai/mode

```json
{
  "mode": "coze_api_mode",
  "available_modes": ["backend_mode", "coze_api_mode"],
  "coze_workflow_id": "wf_xxxx",
  "coze_available": true,
  "lm_studio_available": true
}
```

#### POST /api/ai/mode

**请求体：** `{"mode": "coze_api_mode"}`

**响应 200：**
```json
{
  "ok": true,
  "mode": "coze_api_mode",
  "previous_mode": "backend_mode"
}
```

**响应 400：** `{"detail": "未知模式: xxx，可选: backend_mode, coze_api_mode"}`

#### GET /api/ai/status

```json
{
  "lm_studio": {
    "available": true,
    "url": "http://localhost:1234/v1/chat/completions",
    "models": ["local-model"]
  },
  "coze_api": {
    "available": false,
    "url": "http://localhost:8888",
    "workflow_id": "wf_xxxx",
    "error": "连接被拒绝"
  },
  "current_mode": "backend_mode"
}
```

### 6.2 CLI 扩展

```
kn-backend ai
├── mode [--json]                # 查看当前 LLM 模式
├── mode set <backend|coze>      # 切换 LLM 模式
├── status [--json]              # 查看连通状态
└── generate <endpoint> <id>     # 触发生成（测试用）
```

---

## 7. Workflow 配置步骤（coze_api_mode 首次使用）

1. **登录 Coze Studio 管理后台**
2. **创建 Workflow** → 选择「认知卡片 AI 生成」模板（或从空白创建）
3. **配置输入参数**：`endpoint`（string）+ `context`（string）
4. **添加 LLM 节点**：
   - 模型：选择已接入 LM Studio 的 OpenAI 兼容模型
   - System Prompt：使用对应 endpoint 的提示词
   - User Prompt：`{{context}}`
5. **添加 Code 节点**（可选，清理输出）：
   ```javascript
   return { result: context.trim().replace(/^["']|["']$/g, '').split('\n')[0] }
   ```
6. **配置 Exit 节点** → 输出 `result`
7. **发布 Workflow** → 获取 `workflow_id`
8. **配置环境变量**：
   ```bash
   LLM_MODE=coze_api_mode
   COZE_API_BASE=http://localhost:8888
   COZE_WORKFLOW_ID=wf_xxxx
   ```

---

## 8. 验收标准

- [ ] `backend_mode`：直连 LM Studio 可正常生成卡片标题/描述、节点标签/描述
- [ ] `coze_api_mode`：经 Coze Studio Workflow 可正常生成（等价于直连输出）
- [ ] 两种模式输出结果一致（相同输入得到等价的生成内容）
- [ ] 模式切换 API 正常运行，不中断现有请求
- [ ] 健康检查 API 可反馈两种模式的连通状态
- [ ] 降级链路正确：coze_api_mode → backend_mode → 轻量模板
- [ ] 降级链路正确：backend_mode → coze_api_mode（可选）→ 轻量模板
- [ ] CLI `kn-backend ai mode` 可查看和切换模式
- [ ] 环境变量缺省时默认 `backend_mode`，向后兼容

---

## 9. 故障排查

| 现象 | 排查思路 |
|------|----------|
| `backend_mode` 调用失败 | LM Studio 是否运行？端口 1234 是否可访问？模型是否已加载？ |
| `coze_api_mode` 调用失败 | Coze Studio 后端是否运行？Workflow 是否已发布？`workflow_id` 是否正确？ |
| 两种模式都失败 | 检查环境变量 `LLM_MODE` 是否正确；网络防火墙是否拦截 localhost 请求 |
| 模式切换失败 | 检查模式名是否合法（仅 `backend_mode` / `coze_api_mode`） |
| Coze Studio 内 LLM 节点失败 | Workflow Trace 查看 LLM 节点的具体错误；检查 Coze 的模型配置是否正确 |
| 两种模式输出不一致 | Workflow LLM 节点的提示词是否与后端 `PROMPTS` 保持一致；temperature/max_tokens 参数是否一致 |

---

*本文档定义了 Knowledge Navigator Python 后端的 LLM 双模式架构：直连 LM Studio 与经 Coze Studio Workflow 代理。两种模式可运行时切换，降级链路确保 LLM 不可用时系统仍能提供模板输出。*
