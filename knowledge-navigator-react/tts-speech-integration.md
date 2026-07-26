# TTS 语音朗读集成 — 功能规范

## 版本

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| 1.0 | 2026-07-26 | — | 初始规范：edge-tts 后端 + 节点/卡片朗读按钮 + TTS 音色配置 |

---

## 一、概述

### 1.1 目标

为导航节点和认知卡片增加文字转语音（TTS）朗读能力：

1. **后端 TTS 服务**：基于 `edge-tts`（Microsoft Edge 免费 TTS）提供语音合成 API
2. **前端朗读按钮**：在节点描述区、卡片内容区增加一键朗读按钮
3. **TTS 设置**：提供音色选择、语速、音调等可配置项

### 1.2 技术选型

| 方案 | 说明 |
|------|------|
| 后端：`edge-tts` | Python 库，调用 Microsoft Edge 免费 TTS API，无需 API Key，支持数十种中文音色 |
| 前端：HTML5 Audio | 后端返回 MP3 流，前端 `<audio>` 或 `new Audio()` 播放 |

---

## 二、后端 TTS 模块

### 2.1 依赖

```txt
# backend/requirements.txt 新增
edge-tts>=6.1
```

### 2.2 新增路由 `routers/tts.py`

前缀: `/api/tts`

#### GET /api/tts/voices

返回可用音色列表（首次请求后缓存 1 小时）。

**响应 200：**
```json
{
  "voices": [
    {
      "name": "zh-CN-XiaoxiaoNeural",
      "friendly_name": "晓晓 (女, 普通话)",
      "locale": "zh-CN",
      "gender": "Female"
    },
    {
      "name": "zh-CN-YunxiNeural",
      "friendly_name": "云希 (男, 普通话)",
      "locale": "zh-CN",
      "gender": "Male"
    }
  ]
}
```

#### POST /api/tts/speak

将文本转为语音，返回 MP3 音频流。

**请求体：**
```json
{
  "text": "要朗读的文本内容",
  "voice": "zh-CN-XiaoxiaoNeural",
  "rate": "+0%",
  "pitch": "+0Hz"
}
```

**响应 200：** `audio/mpeg` 流（`StreamingResponse`）

**响应 400：** 文本为空或过长（> 5000 字）

### 2.3 实现要点

```python
# backend/app/routers/tts.py

import edge_tts
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from io import BytesIO

router = APIRouter(prefix="/api/tts", tags=["tts"])

# 音色列表缓存（首次请求后有效期 1 小时）
_voices_cache: list[dict] | None = None
_voices_cache_time: float = 0

async def get_voices() -> list[dict]:
    global _voices_cache, _voices_cache_time
    now = time.time()
    if _voices_cache and now - _voices_cache_time < 3600:
        return _voices_cache
    voices = await edge_tts.list_voices()
    result = [{
        "name": v["ShortName"],
        "friendly_name": v.get("FriendlyName", v["ShortName"]),
        "locale": v["Locale"],
        "gender": v.get("Gender", "Unknown"),
    } for v in voices if v["Locale"].startswith("zh")]
    _voices_cache = result
    _voices_cache_time = now
    return result

@router.get("/voices")
async def list_voices():
    return {"voices": await get_voices()}

@router.post("/speak")
async def speak(body: SpeakBody):
    text = body.text.strip()
    if not text:
        raise HTTPException(400, "文本不能为空")
    if len(text) > 5000:
        raise HTTPException(400, "文本过长（最多 5000 字）")

    communicate = edge_tts.Communicate(text, body.voice, rate=body.rate, pitch=body.pitch)
    buf = BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])
    buf.seek(0)
    return StreamingResponse(buf, media_type="audio/mpeg")
```

### 2.4 注册路由

在 `main.py` 中新增 `tts` 到 router 列表。

---

## 三、前端 TTS 架构

### 3.1 TTS 配置存储

新建 `src/config/tts.ts`，与 `src/config/backend.ts` 同层，使用 localStorage 持久化：

```typescript
// src/config/tts.ts

export interface TtsConfig {
  voice: string      // 音色名，默认 'zh-CN-XiaoxiaoNeural'
  rate: string       // 语速，默认 '+0%' 范围 '-50%'~'+100%'
  pitch: string      // 音调，默认 '+0Hz' 范围 '-20Hz'~'+20Hz'
}

const STORAGE_KEY = 'kn_tts_config'
const DEFAULT: TtsConfig = {
  voice: 'zh-CN-XiaoxiaoNeural',
  rate: '+0%',
  pitch: '+0Hz',
}

export function getTtsConfig(): TtsConfig { ... }
export function setTtsConfig(config: Partial<TtsConfig>): void { ... }
export function getDefaultTtsConfig(): TtsConfig { ... }
```

### 3.2 TTS 播放工具

新建 `src/utils/ttsPlayer.ts`：

```typescript
let currentAudio: HTMLAudioElement | null = null

export function stopTts(): void {
  if (currentAudio) { currentAudio.pause(); currentAudio = null }
}

export async function playTts(text: string, config?: Partial<TtsConfig>): Promise<void> {
  stopTts()
  const cfg = { ...getTtsConfig(), ...config }

  const res = await fetch('/api/tts/speak', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, voice: cfg.voice, rate: cfg.rate, pitch: cfg.pitch }),
  })
  if (!res.ok) throw new Error('TTS 请求失败')

  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  currentAudio = new Audio(url)
  currentAudio.onended = () => { URL.revokeObjectURL(url); currentAudio = null }
  await currentAudio.play()
}
```

### 3.3 TTS 播放按钮组件

新建 `src/components/shared/TtsButton.tsx`：

```tsx
interface TtsButtonProps {
  text: string
  size?: 'sm' | 'md'
}

const TtsButton: React.FC<TtsButtonProps> = ({ text, size = 'sm' }) => {
  const [playing, setPlaying] = useState(false)
  const handleClick = async () => {
    setPlaying(true)
    try {
      await playTts(text)
    } catch (e) {
      toast('TTS 播放失败')
    } finally {
      setPlaying(false)
    }
  }
  return <button onClick={handleClick} disabled={playing}>{playing ? '⏸' : '🔊'}</button>
}
```

### 3.4 放置位置

| 位置 | 文件 | 朗读内容 |
|------|------|----------|
| 节点下拉面板 | `DropDownPanel.tsx` | `node.description` |
| 自由分支浏览 | `FreeBrowseView.tsx` | `currentNode.label + description` |
| 浏览卡片 | `BrowseCard.tsx` | `card.title + card.desc`（或语料） |
| 搜索卡片列表 | `CardMatchItem.tsx` | `card.title + description` |

---

## 四、TTS 设置界面

### 4.1 TTS 设置对话框

新建 `src/components/settings/TtsSettingsDialog.tsx`（模态对话框）：

```
┌──────────────────────────────────────────┐
│  TTS 语音设置                       [✕]  │
│                                          │
│  音色 (Voice)                            │
│  ┌──────────────────────────────────┐   │
│  │ zh-CN-XiaoxiaoNeural        [▼]  │   │
│  └──────────────────────────────────┘   │
│  晓晓 (女, 普通话)                       │
│                                          │
│  语速 (Rate)                             │
│  -50%  [═══════╪═══════]  +100%         │
│              +0%                         │
│                                          │
│  音调 (Pitch)                            │
│  -20Hz  [══════╪═══════]  +20Hz         │
│              +0Hz                        │
│                                          │
│  [试听]                                  │
│                                          │
│  [保存]  [取消]                          │
└──────────────────────────────────────────┘
```

- 音色下拉：加载 `/api/tts/voices` 返回的中文音色列表
- 语速范围滑块：`-50%` 到 `+100%`，步长 `10%`
- 音调范围滑块：`-20Hz` 到 `+20Hz`，步长 `2Hz`
- 试听按钮：用当前配置朗读一段测试文本
- 保存到 localStorage

### 4.2 设置入口

在 `StatusBar.tsx`（顶部状态栏）增加齿轮图标按钮，点击打开 TtsSettingsDialog。

当前 StatusBar 已有后端模式指示器，在此旁边增加 TTS 设置入口。

---

## 五、代码变更清单

### 5.1 后端（4 个文件）

| 文件 | 变更 |
|------|------|
| `backend/requirements.txt` | 新增 `edge-tts>=6.1` |
| `backend/app/routers/tts.py` | **新建** — `/api/tts/voices` + `/api/tts/speak` |
| `backend/app/main.py` | 导入并注册 tts router |

### 5.2 前端（10 个文件）

| 文件 | 变更 |
|------|------|
| `src/config/tts.ts` | **新建** — TTS 配置持久化 |
| `src/utils/ttsPlayer.ts` | **新建** — 播放/停止工具 |
| `src/components/shared/TtsButton.tsx` | **新建** — 朗读按钮组件 |
| `src/components/shared/TtsButton.module.css` | **新建** — 按钮样式 |
| `src/components/settings/TtsSettingsDialog.tsx` | **新建** — TTS 设置对话框 |
| `src/components/settings/TtsSettingsDialog.module.css` | **新建** — 对话框样式 |
| `src/components/layout/StatusBar.tsx` | 新增 TTS 设置入口按钮 |
| `src/components/panel/DropDownPanel.tsx` | 节点描述旁增加 TTS 按钮 |
| `src/components/views/FreeBrowseView.tsx` | 节点描述旁增加 TTS 按钮 |
| `src/components/cards/BrowseCard.tsx` | 卡片标题旁增加 TTS 按钮 |

---

## 六、验收标准

- [ ] `GET /api/tts/voices` 返回中文音色列表
- [ ] `POST /api/tts/speak` 返回可播放的 MP3 音频流
- [ ] 前端可通过 `playTts()` 播放任意文本
- [ ] TTS 设置对话框可切换音色、语速、音调
- [ ] 试听按钮可用当前配置朗读测试文本
- [ ] DropDownPanel 节点描述区有 TTS 按钮
- [ ] FreeBrowseView 节点描述区有 TTS 按钮
- [ ] BrowseCard 卡片标题旁有 TTS 按钮
- [ ] 播放中点击新朗读按钮，停止当前播放
- [ ] 设置持久化到 localStorage，刷新后保留
- [ ] 编译零错误

---

## 七、边界情况

| 场景 | 行为 |
|------|------|
| 文本为空 | 按钮 disabled，后端返回 400 |
| 文本过长（>5000 字） | 后端返回 400，前端可截断处理 |
| 网络错误 | toast 提示"TTS 播放失败" |
| 后端未启动（本地模式） | 本地模式下隐藏 TTS 按钮，或 toast 提示 |
| 音频正在播放时再次点击 | 停止当前音频，开始新播放 |
| 音色列表加载失败 | 下拉显示默认音色，前端内置备选列表 |

---

*本文档定义了基于 edge-tts 的语音朗读功能，涵盖后端 API、前端播放、设置配置三部分。*
