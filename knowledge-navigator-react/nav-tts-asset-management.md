# TTS 资产化管理设计

> 参考 `mindflow_qt` 的 TTS 资产化设计理念，适配当前项目（React + FastAPI Web 栈）的完整方案。

---

## 1. 设计目标

当前项目的 TTS 实现是"每次请求实时合成"模式，无任何缓存复用。引入资产管理后：

| 目标 | 现状 | 改造后 |
|------|------|--------|
| **缓存复用** | 每次点击朗读都重新合成 | 相同文本+参数组合只合成一次，后续返回缓存文件 |
| **索引可查** | 无索引 | manifest 文件记录所有音频资产的元信息 |
| **预热加速** | 无预热 | 首次加载导航图时，后台批量预生成音频 |
| **一致性保证** | 无持久化 | manifest 与实际文件状态始终保持一致 |
| **配置持久化** | localStorage 前端存储 | 前端配置 + 后端缓存目录统一管理 |

---

## 2. 核心架构

### 2.1 模块职责

| 模块 | 位置 | 职责 |
|------|------|------|
| **TTSAssetManager** | `backend/app/services/tts_assets.py` | 资产管理核心，管理 manifest 读写、缓存查询、异步生成 |
| **get_tts_asset_manager** | `backend/app/services/tts_assets.py` | 全局单例工厂，按 `cache_dir` 缓存 manager 实例 |
| **tts 路由** | `backend/app/routers/tts.py` | 现有路由改造，集成资产化流程 |
| **tts_manifest.yaml** | `backend/tts_cache/` | 资产索引清单文件 |
| **ttsPlayer.ts** | `src/utils/ttsPlayer.ts` | 前端播放引擎，增加缓存优先逻辑 |
| **ttsConfig** | `src/config/tts.ts` | TTS 配置（voice/rate/pitch），仍使用 localStorage |

### 2.2 分层位置

```
前端 (React)
  src/config/tts.ts              ← TTS 配置定义
  src/utils/ttsPlayer.ts         ← 播放引擎
  src/components/shared/TtsButton.tsx   ← 触发按钮

后端 (FastAPI)
  backend/app/services/tts_assets.py    ← 资产管理
  backend/app/routers/tts.py            ← REST 路由
  backend/tts_cache/                    ← 资产存储目录
    ├── tts_manifest.yaml               ← 资产索引
    └── tts_<fingerprint>.mp3           ← 音频文件
```

---

## 3. 资产索引：Manifest

### 3.1 文件路径

```
backend/tts_cache/tts_manifest.yaml
```

### 3.2 文件结构

```yaml
assets:              # 资产池：以指纹为 key
  a1b2c3d4e5f6a7b8:  # SHA1[:16]
    filename: "tts_a1b2c3d4e5f6a7b8.mp3"
    params:          # 合成参数
      text: "欢迎使用认知导航系统"
      voice: "zh-CN-XiaoxiaoNeural"
      rate: "+0%"
      pitch: "+0Hz"
    refs:            # 引用该资产的来源（节点 ID / 卡片 ID）
      - "node/g1/nav_01"
      - "card/g1/card_01"
    size_bytes: 0           # 文件大小，创建时暂存 0，合成完成后更新
    updated_at: "2026-07-28T10:00:00"

event_index:         # 事件/来源 → 指纹映射
  "node/g1/nav_01":
    fingerprint: "a1b2c3d4e5f6a7b8"
    params: { text: "...", voice: "...", rate: "...", pitch: "..." }
  "card/g1/card_01":
    fingerprint: "a1b2c3d4e5f6a7b8"
    params: { text: "...", voice: "...", rate: "...", pitch: "..." }
```

### 3.3 指纹生成规则

```python
import hashlib

def make_fingerprint(voice: str, rate: str, pitch: str, text: str) -> str:
    """生成 16 位十六进制指纹"""
    raw = f"{voice}|{rate}|{pitch}|{text.strip()}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]
```

- 输入规范化：text 会 strip()，缺失参数使用默认值
- 保证相同参数组合对应唯一指纹，避免重复合成
- **当前项目比 mindflow_qt 多一个 pitch 参数**，指纹计算包含 pitch

### 3.4 设计约束

- **manifest 是缓存资产索引，不是业务真源** — 丢失可通过重新合成重建
- **清理策略必须保证 manifest 与实际文件状态最终一致**
- 写入使用原子替换（先写 `.tmp` 再 `os.replace`），防止写半损坏
- manifest 读写在 `threading.Lock` 保护下进行

---

## 4. 资产获取流程

### 4.1 同步获取核心流程

```
POST /api/tts/speak { text, voice, rate, pitch }
    │
    ├─ 1. 计算指纹：SHA1(voice|rate|pitch|text.strip())[:16]
    │
    ├─ 2. 检查缓存：
    │     ├─ manifest 中有该指纹 && 文件存在 && size > 0
    │     │     └─ 直接返回 FileResponse (audio/mpeg)
    │     └─ 未命中
    │           └─ 进入合成流程
    │
    ├─ 3. 合成音频：
    │     ├─ edge_tts.Communicate() 合成
    │     ├─ 写入 tts_cache/tts_<fingerprint>.mp3
    │     ├─ 更新 manifest（指纹、参数、refs、时间戳）
    │     └─ 返回 FileResponse
    │
    └─ 4. 前端：
          ├─ playTts() 获取音频 URL
          ├─ 播放完成后释放 Blob URL
          └─ 不缓存到前端（下次请求走后端缓存）
```

### 4.2 注册引用（Refs）

当 TTS 按钮被点击时，如果需要记录某个节点的音频引用关系，可以在请求中包含 `source` 字段：

```http
POST /api/tts/speak
{
  "text": "欢迎使用认知导航系统",
  "voice": "zh-CN-XiaoxiaoNeural",
  "rate": "+0%",
  "pitch": "+0Hz",
  "source": "node/g1/nav_01"    // 可选，用于 manifest refs 追踪
}
```

后端收到 `source` 后，在 manifest 的 `assets[fp].refs` 中追加该来源（去重）。

### 4.3 缓存探测接口（可选）

新增 `GET /api/tts/check` 用于前端或预热系统探测缓存状态：

```
GET /api/tts/check?text=...&voice=...&rate=...&pitch=...
  → { "cached": true, "fingerprint": "a1b2c3d4e5f6a7b8", "url": "/api/tts/audio/a1b2c3d4e5f6a7b8.mp3" }
  → { "cached": false, "fingerprint": "a1b2c3d4e5f6a7b8" }
```

### 4.4 直接获取文件接口（可选）

新增 `GET /api/tts/audio/{fingerprint}.mp3` 直接返回缓存文件：

```python
@router.get("/audio/{fingerprint}.mp3")
async def get_cached_audio(fingerprint: str):
    mgr = get_tts_asset_manager()
    path = mgr.peek_audio_path(fingerprint)
    if path:
        return FileResponse(path, media_type="audio/mpeg")
    raise HTTPException(404, "音频缓存未找到")
```

---

## 5. 预热机制

### 5.1 预热场景

首次加载导航图或切换导航图时，预先合成当前可见节点和卡片的音频。

### 5.2 预热触发点

| 场景 | 触发时机 | 预热范围 |
|------|----------|----------|
| 导航图加载 | 画布数据加载完成后 | 当前可见的所有导航节点 label + description |
| 钻入子图 | 子图数据加载完成后 | 子图中所有可见节点 |
| 切换图 | 用户切换选择的图集合后 | 新图所有可见节点 |
| 手动触发 | 用户点击"预热"按钮 | 当前图所有节点 |

### 5.3 预热流程

```
用户加载导航图
  → 前端获取画布数据
  → 前端触发预热请求 POST /api/tts/warmup
    │
    ├─ 后端解析请求体中的预热点列表
    │     [{ text, voice?, rate?, pitch?, source }]
    │
    ├─ 检查 manifest 已有缓存
    │     ├─ 已缓存 → 跳过
    │     └─ 未缓存 → 加入合成队列
    │
    ├─ 后台 asyncio.create_task 异步批量合成
    │     逐个调用 edge_tts.Communicate()
    │     同步写入文件 + 更新 manifest
    │
    └─ 返回 { accepted: N, total: M }
```

### 5.4 预热 API

```http
POST /api/tts/warmup
Content-Type: application/json

{
  "items": [
    { "text": "节点一的标题与描述", "source": "node/g1/nav_01" },
    { "text": "节点二的标题与描述", "source": "node/g1/nav_02" }
  ]
}
```

响应：

```json
{
  "accepted": 5,
  "total": 12,
  "cached_skipped": 7
}
```

### 5.5 预热规则

- **预热不阻塞响应** — 使用 `asyncio.create_task` 在后台异步执行
- **预热只负责预生成，不改变业务动作序列**
- **预热结果写回时必须保证 manifest 对齐**
- **失败时记录日志，不影响整体流程**
- **预热任务必须可中止** — 当用户切换导航图时，使用 `asyncio.CancelledError` 取消进行中的预热

### 5.6 Web 栈 vs Qt 栈的预热差异

| 方面 | mindflow_qt (Qt/Python) | 本项目 (React/FastAPI) |
|------|------------------------|------------------------|
| 并发模型 | `threading.Thread` | `asyncio.create_task` |
| 进度通知 | Signal bridge → UI | 预热接口返回 accepted 计数，前端不做实时进度追踪 |
| 中断机制 | 无显式中断 | `asyncio.Task.cancel()` |
| 线程安全 | `threading.Lock` | `asyncio.Lock` |

---

## 6. 后端改造要点

### 6.1 新增文件 `backend/app/services/__init__.py`

创建包初始化文件（如果不存在）。

### 6.2 新增文件 `backend/app/services/tts_assets.py`

```python
"""
TTS 资产管理模块（单例模式）
"""
import hashlib, os, yaml, logging
from datetime import datetime
from pathlib import Path
from typing import Optional

# 默认缓存目录：backend/tts_cache/
DEFAULT_CACHE_DIR = Path(__file__).resolve().parents[2] / "tts_cache"

class TTSAssetManager:
    def __init__(self, cache_dir: Path = DEFAULT_CACHE_DIR):
        self._cache_dir = cache_dir
        self._manifest_path = cache_dir / "tts_manifest.yaml"
        self._lock = asyncio.Lock()   # 异步锁
        self._manifest: dict | None = None
        cache_dir.mkdir(parents=True, exist_ok=True)

    # --- 核心方法 ---

    def make_fingerprint(self, voice: str, rate: str, pitch: str, text: str) -> str:
        raw = f"{voice}|{rate}|{pitch}|{text.strip()}"
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]

    async def peek_audio_path(self, fingerprint: str) -> Optional[Path]:
        """检查本地是否存在对应的 mp3 文件"""
        path = self._cache_dir / f"tts_{fingerprint}.mp3"
        return path if path.exists() and path.stat().st_size > 0 else None

    async def get_audio_path(
        self, text: str, voice: str, rate: str, pitch: str,
        source: Optional[str] = None, generate: bool = True
    ) -> Optional[Path]:
        """获取或生成音频文件路径"""
        fp = self.make_fingerprint(voice, rate, pitch, text)
        cached = await self.peek_audio_path(fp)
        if cached:
            if source:
                await self._register_ref(fp, source)
            return cached
        if not generate:
            return None
        # 合成并保存
        return await self._synthesize(text, voice, rate, pitch, fp, source)

    async def warmup(self, items: list[dict]) -> dict:
        """批量预热：检查缓存并异步合成"""
        accepted = 0
        cached_skipped = 0
        for item in items:
            v = item.get("voice", "zh-CN-XiaoxiaoNeural")
            r = item.get("rate", "+0%")
            p = item.get("pitch", "+0Hz")
            t = item.get("text", "").strip()
            if not t:
                continue
            fp = self.make_fingerprint(v, r, p, t)
            if await self.peek_audio_path(fp):
                cached_skipped += 1
                continue
            src = item.get("source")
            asyncio.create_task(self._synthesize(t, v, r, p, fp, src))
            accepted += 1
        return {"accepted": accepted, "total": len(items), "cached_skipped": cached_skipped}

    # --- 内部方法 ---

    async def _synthesize(self, text: str, voice: str, rate: str, pitch: str,
                          fingerprint: str, source: Optional[str]) -> Path:
        """合成音频并写入磁盘"""
        from edge_tts import Communicate
        path = self._cache_dir / f"tts_{fingerprint}.mp3"
        try:
            communicate = Communicate(text, voice=voice, rate=rate, pitch=pitch)
            with open(path, "wb") as f:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        f.write(chunk["data"])
            # 更新 manifest
            await self._update_manifest(fingerprint, {
                "filename": path.name,
                "params": {"text": text, "voice": voice, "rate": rate, "pitch": pitch},
                "refs": [source] if source else [],
                "size_bytes": path.stat().st_size,
                "updated_at": datetime.now().isoformat(),
            })
        except Exception as e:
            logging.error(f"TTS 合成失败 [fp={fingerprint}]: {e}")
            if path.exists():
                path.unlink()
            raise
        return path

    async def _register_ref(self, fingerprint: str, source: str):
        """在 manifest 中记录引用关系"""
        async with self._lock:
            man = await self._load_manifest()
            if fingerprint in man.get("assets", {}):
                refs = man["assets"][fingerprint].setdefault("refs", [])
                if source not in refs:
                    refs.append(source)
            # 更新 event_index
            man.setdefault("event_index", {})[source] = fingerprint
            await self._dump_manifest(man)

    async def _load_manifest(self) -> dict:
        """加载 manifest（带内存缓存）"""
        if self._manifest is not None:
            return self._manifest
        if self._manifest_path.exists():
            with open(self._manifest_path, "r", encoding="utf-8") as f:
                self._manifest = yaml.safe_load(f) or {"assets": {}, "event_index": {}}
        else:
            self._manifest = {"assets": {}, "event_index": {}}
        return self._manifest

    async def _dump_manifest(self, man: dict):
        """原子写入 manifest"""
        tmp = self._manifest_path.with_suffix(".yaml.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            yaml.dump(man, f, allow_unicode=True, default_flow_style=False)
        os.replace(tmp, self._manifest_path)
        self._manifest = man

    async def _update_manifest(self, fingerprint: str, entry: dict):
        """更新/合并单个资产条目到 manifest"""
        async with self._lock:
            man = await self._load_manifest()
            existing = man["assets"].get(fingerprint, {})
            # 合并 refs（去重）
            old_refs = existing.get("refs", [])
            new_refs = entry.get("refs", [])
            merged_refs = list(dict.fromkeys(old_refs + new_refs))
            entry["refs"] = merged_refs
            man["assets"][fingerprint] = entry
            # 更新 event_index
            for ref in merged_refs:
                man.setdefault("event_index", {})[ref] = fingerprint
            await self._dump_manifest(man)


# --- 全局单例工厂 ---
_instances: dict[str, TTSAssetManager] = {}
_instances_lock = asyncio.Lock()

async def get_tts_asset_manager(cache_dir: Optional[Path] = None) -> TTSAssetManager:
    cache_dir = cache_dir or DEFAULT_CACHE_DIR
    key = str(cache_dir.resolve())
    if key not in _instances:
        async with _instances_lock:
            if key not in _instances:
                _instances[key] = TTSAssetManager(cache_dir)
    return _instances[key]
```

### 6.3 改造现有 TTS 路由

**文件**: `backend/app/routers/tts.py`

```python
"""
改造要点：
1. POST /api/tts/speak  改为走 TTSAssetManager 的缓存优先流程
2. 新增 POST /api/tts/warmup  批量预热接口
3. GET /api/tts/voices  保持不变
4. 新增 GET /api/tts/audio/{fingerprint}.mp3  直接返回缓存文件
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from ..services.tts_assets import get_tts_asset_manager

router = APIRouter(prefix="/api/tts", tags=["tts"])

class SpeakBody(BaseModel):
    text: str
    voice: str = "zh-CN-XiaoxiaoNeural"
    rate: str = "+0%"
    pitch: str = "+0Hz"
    source: Optional[str] = None   # 新增加字段

class WarmupItem(BaseModel):
    text: str
    voice: str = "zh-CN-XiaoxiaoNeural"
    rate: str = "+0%"
    pitch: str = "+0Hz"
    source: Optional[str] = None

class WarmupBody(BaseModel):
    items: list[WarmupItem]

# 改造 speak 接口
@router.post("/speak")
async def speak(body: SpeakBody):
    if not body.text.strip():
        raise HTTPException(400, "文本不能为空")
    mgr = await get_tts_asset_manager()
    path = await mgr.get_audio_path(
        text=body.text,
        voice=body.voice,
        rate=body.rate,
        pitch=body.pitch,
        source=body.source,
        generate=True,
    )
    if not path:
        raise HTTPException(500, "语音合成失败")
    return FileResponse(path, media_type="audio/mpeg")

# 新增预热接口
@router.post("/warmup")
async def warmup(body: WarmupBody):
    mgr = await get_tts_asset_manager()
    result = await mgr.warmup([
        {
            "text": item.text,
            "voice": item.voice,
            "rate": item.rate,
            "pitch": item.pitch,
            "source": item.source,
        }
        for item in body.items
    ])
    return result

# 新增缓存文件直接获取
@router.get("/audio/{fingerprint}.mp3")
async def get_cached_audio(fingerprint: str):
    mgr = await get_tts_asset_manager()
    path = await mgr.peek_audio_path(fingerprint)
    if path:
        return FileResponse(path, media_type="audio/mpeg")
    raise HTTPException(404, "音频缓存未找到")

# voices 接口保持不变
...
```

---

## 7. 前端改造要点

### 7.1 `ttsPlayer.ts` 改造

```typescript
// 改造 playTts 函数
export async function playTts(
  text: string,
  overrides?: Partial<TtsConfig>,
  source?: string,        // 新增加数，用于 manifest refs 追踪
): Promise<void> {
  // ... 停止当前播放 ...

  const config = { ...getTtsConfig(), ...overrides }
  const truncated = text.slice(0, MAX_TEXT_LENGTH)

  const body: Record<string, unknown> = {
    text: truncated,
    voice: config.voice,
    rate: config.rate,
    pitch: config.pitch,
  }
  if (source) {
    body.source = source   // 传 source 给后端记录 refs
  }

  try {
    const resp = await fetch(apiUrl('/api/tts/speak'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!resp.ok) throw new Error(`TTS 请求失败: ${resp.status}`)

    const blob = await resp.blob()
    const url = URL.createObjectURL(blob)
    // ... 播放逻辑保持不变 ...
  } catch (err) {
    // ... 错误处理保持不变 ...
  }
}
```

### 7.2 TtsButton 组件改造

```tsx
// 增加 source prop 传递给 playTts
interface Props {
  text: string
  size?: 'sm' | 'md'
  source?: string   // 新增，格式如 "node/g1/nav_01"
}

// 调用时传递
playTts(text, undefined, source)
```

### 7.3 导航图加载时触发预热

```typescript
// 在 NavView 或 useNavCanvas 中，画布数据加载完成后触发预热
async function triggerWarmup(graphData: GraphData) {
  const config = getTtsConfig()
  const items = graphData.nodes.map(n => ({
    text: `${n.label}。${n.description || ''}`,
    voice: config.voice,
    rate: config.rate,
    pitch: config.pitch,
    source: `node/${n.graph_id}/${n.id}`,
  }))
  try {
    await fetch(apiUrl('/api/tts/warmup'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ items }),
    })
    // 预热是后台异步的，不需要等待完成
  } catch {
    // 预热失败不阻塞用户操作
  }
}
```

---

## 8. 预热配置开关

### 8.1 设置界面增加预热开关

在 `TtsSettingsDialog` 中增加一个"启用预热"的开关，对应配置项 `prewarm: boolean`。

```typescript
// src/config/tts.ts 扩展
interface TtsConfig {
  voice: string
  rate: string
  pitch: string
  prewarm: boolean   // 新增：是否启用预热
}
```

默认值：`prewarm: true`

### 8.2 预热启用逻辑

- **`prewarm: true`** — 导航图加载完成后自动触发预热（无感后台进行）
- **`prewarm: false`** — 仅按需合成（用户点击 TTS 按钮时才合成）

---

## 9. 缓存管理

### 9.1 文件结构

```
backend/
  tts_cache/
    tts_manifest.yaml       ← 资产索引清单
    tts_a1b2c3d4e5f6a7b8.mp3   ← 音频文件
    tts_b2c3d4e5f6a7b8c9.mp3
    ...
```

### 9.2 清理策略

| 策略 | 触发条件 | 行为 |
|------|----------|------|
| 手动清理 | 用户操作（设置界面"清除缓存"按钮） | 删除所有 mp3 文件 + 重置 manifest |
| 自动清理（可选） | 缓存目录超过阈值（如 500MB） | 按 `updated_at` 排序，删除最旧的 30% |

### 9.3 清除 API

```http
DELETE /api/tts/cache
  → { "deleted_files": 42, "freed_bytes": 52428800 }
```

---

## 10. 与 mindflow_qt 设计差异对照

| 维度 | mindflow_qt | 本项目 |
|------|-------------|--------|
| 应用栈 | Qt Desktop (PyQt) | Web (React + FastAPI) |
| 并发模型 | `threading.Thread` | `asyncio.create_task` |
| 锁机制 | `threading.Lock` | `asyncio.Lock` |
| UI 反馈 | Signal bridge 实时进度 | 预热接口返回计数，无实时进度 |
| 预热中断 | 无 | `asyncio.Task.cancel()` |
| 音频返回方式 | 本地文件路径 | HTTP FileResponse |
| 前端缓存 | 无（直接读本地文件） | 后端缓存 + Blob URL 播放 |
| 指纹参数 | voice + rate + text | voice + rate + pitch + text（多 pitch） |
| 配置存储 | Python config | 前端 localStorage |
| 引用追踪 | event_id / step_index | node_id / card_id |

---

## 11. 测试验证

### 11.1 单元测试

```python
# backend/tests/test_tts_assets.py

async def test_fingerprint_consistency():
    mgr = TTSAssetManager()
    fp1 = mgr.make_fingerprint("v1", "+0%", "+0Hz", "你好")
    fp2 = mgr.make_fingerprint("v1", "+0%", "+0Hz", "  你好  ")
    assert fp1 == fp2  # strip 后应一致

async def test_cache_hit():
    mgr = TTSAssetManager()
    fp = mgr.make_fingerprint("v1", "+0%", "+0Hz", "test")
    path = await mgr.peek_audio_path(fp)
    assert path is None  # 尚未合成

async def test_cache_miss_then_hit():
    mgr = TTSAssetManager()
    path = await mgr.get_audio_path("hello", "v1", "+0%", "+0Hz", generate=True)
    assert path and path.exists() and path.stat().st_size > 0
    # 再次获取应命中缓存
    path2 = await mgr.get_audio_path("hello", "v1", "+0%", "+0Hz", generate=False)
    assert path2 == path
```

### 11.2 验证步骤

1. 启动后端，首次请求 `/api/tts/speak`（参数：text="你好世界"）— 应触发 edge-tts 合成，耗时约 1-3s
2. 再次请求相同参数 — 应直接返回缓存文件，耗时约 10ms
3. 检查 `backend/tts_cache/` 目录 — 应包含 `tts_manifest.yaml` 和 `.mp3` 文件
4. 请求 `/api/tts/warmup` 预热 5 个节点 — 返回 `accepted: 5`
5. 再次请求相同节点的 speak — 全部命中缓存
6. 修改 voice 或 rate — 应重新合成（不同指纹）
7. 请求 `/api/tts/cache` — 应清除所有缓存文件
8. 再次播放 — 重新合成

---

## 12. 实施路线

| 阶段 | 内容 | 涉及文件 |
|------|------|----------|
| 1 | 新建 `backend/app/services/tts_assets.py` 实现 TTSAssetManager | `services/__init__.py`, `services/tts_assets.py` |
| 2 | 改造 `routers/tts.py`，集成资产化流程 | `routers/tts.py` |
| 3 | 前端 `ttsPlayer.ts` 增加 source 参数 | `ttsPlayer.ts` |
| 4 | TtsButton 增加 source prop | `TtsButton.tsx` |
| 5 | NavView 加载数据后触发预热 | `NavView.tsx` / `useNavCanvas.ts` |
| 6 | 设置界面增加预热开关 | `TtsSettingsDialog.tsx`, `config/tts.ts` |
| 7 | 端到端测试验证 | 手动测试 + 单元测试 |
