# TTS 后台预热开关

> 在 TTS 设置弹窗中增加"启用后台预热"开关，让用户自主控制是否在加载导航图时自动预合成音频。

---

## 1. 设计目标

| 场景 | 无预热 | 开启预热 | 关闭预热 |
|------|--------|----------|----------|
| 首次点击 TTS 按钮 | 等待 1-3s 实时合成 | 缓存命中，瞬时播放 | 等待 1-3s 实时合成 |
| 加载新导航图 | 无后台操作 | 自动合成所有节点音频 | 无后台操作 |
| 钻入子图 | 无后台操作 | 自动合成子图节点音频 | 无后台操作 |

预热开关让用户在网络带宽或计算资源紧张时可以选择关闭，避免后台占用。

---

## 2. 改动文件清单

| 文件 | 改动内容 |
|------|----------|
| `src/config/tts.ts` | `TtsConfig` 接口增加 `prewarm: boolean` 字段 |
| `src/components/settings/TtsSettingsDialog.tsx` | 设置弹窗增加开关 UI 和状态绑定 |
| `src/components/settings/TtsSettingsDialog.module.css` | 开关样式 |
| `src/hooks/useNavCanvas.ts` 或 `src/components/views/NavView.tsx` | 画布数据加载后条件触发预热 |

---

## 3. 配置层改动

### 3.1 新增 prewarm 字段

**文件**: `src/config/tts.ts`

```typescript
export interface TtsConfig {
  voice: string
  rate: string
  pitch: string
  prewarm: boolean   // 新增：是否启用后台预热
}

const DEFAULT: TtsConfig = {
  voice: 'zh-CN-XiaoxiaoNeural',
  rate: '+0%',
  pitch: '+0Hz',
  prewarm: true,     // 默认开启预热
}
```

`getTtsConfig()` 的合并逻辑 `{ ...DEFAULT, ...JSON.parse(raw) }` 天然支持新增字段 — 旧配置不含 `prewarm` 时自动使用 `true` 兜底。

---

## 4. 设置弹窗改动

### 4.1 UI 布局

在试听按钮上方插入预热开关行：

```
┌─────────────────────────────────┐
│  TTS 语音设置                    │
│                                 │
│  音色 (Voice)   [下拉列表    ▼]  │
│  语速 (Rate): +0%  [===●=====]  │
│  音调 (Pitch): +0Hz [===●=====] │
│                                 │
│  ┌─ 预热 ─────────────────────┐ │
│  │  [●] 启用后台预热           │ │
│  │  首次加载导航图时自动预合成   │ │
│  │  音频，减少等待时间          │ │
│  └────────────────────────────┘ │
│                                 │
│  [🔊 试听]                      │
│                                 │
│  [重置默认]          [取消] [保存] │
└─────────────────────────────────┘
```

### 4.2 组件改动

**文件**: `src/components/settings/TtsSettingsDialog.tsx`

```typescript
// 新增状态
const [prewarm, setPrewarm] = useState(getTtsConfig().prewarm)

// 保存时连带写入
const handleSave = useCallback(() => {
  setTtsConfig({ voice, rate, pitch, prewarm })
  onClose()
}, [voice, rate, pitch, prewarm, onClose])

// 重置时同步
const handleReset = useCallback(() => {
  const d = getDefaultTtsConfig()
  setVoice(d.voice)
  setRate(d.rate)
  setPitch(d.pitch)
  setPrewarm(d.prewarm)   // 新增
}, [])
```

在 JSX 的试听按钮上方插入开关区域：

```tsx
{/* ── 预热开关 ── */}
<div className={styles.prewarmSection}>
  <label className={styles.prewarmToggle}>
    <span className={styles.prewarmLabel}>启用后台预热</span>
    <input
      type="checkbox"
      className={styles.prewarmCheckbox}
      checked={prewarm}
      onChange={(e) => setPrewarm(e.target.checked)}
    />
    <span className={styles.prewarmSwitch} />
  </label>
  <p className={styles.prewarmHint}>
    首次加载导航图时自动预合成音频，减少等待时间
  </p>
</div>

{/* 试听 */}
<button className={styles.testBtn} onClick={handleTest} disabled={testing}>
  {testing ? '试听中...' : '🔊 试听'}
</button>
```

---

## 5. 开关样式

**文件**: `src/components/settings/TtsSettingsDialog.module.css`

```css
/* ── 预热开关区域 ── */
.prewarmSection {
  padding: 12px;
  margin: 8px 0;
  background: var(--fill-f1);
  border-radius: var(--radius-md);
}

.prewarmToggle {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  user-select: none;
}

.prewarmLabel {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  color: var(--label-primary);
}

/* 隐藏原生 checkbox */
.prewarmCheckbox {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}

/* 自定义 switch 滑块轨道 */
.prewarmSwitch {
  position: relative;
  width: 40px;
  height: 22px;
  background: var(--fill-f3);
  border-radius: 11px;
  transition: background 0.2s;
  flex-shrink: 0;
}

/* switch 圆形按钮 */
.prewarmSwitch::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 18px;
  height: 18px;
  background: white;
  border-radius: 50%;
  transition: transform 0.2s;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}

/* 选中态：轨道变主题色，滑块右移 */
.prewarmCheckbox:checked + .prewarmSwitch {
  background: var(--accent, #06b6d4);
}
.prewarmCheckbox:checked + .prewarmSwitch::after {
  transform: translateX(18px);
}

/* 提示文字 */
.prewarmHint {
  margin: 6px 0 0 0;
  font-size: 12px;
  color: var(--label-tertiary);
  line-height: 1.4;
}
```

---

## 6. 预热触发逻辑

### 6.1 条件判断

预热触发点需要检查配置开关：

```typescript
// 在 NavView 的数据加载 useEffect 中（或其他触发点）
import { getTtsConfig } from '../../config/tts'
import { triggerWarmup } from '../../utils/ttsWarmup'

// 数据加载完成后
useEffect(() => {
  if (!graphData || !graphData.nodes) return

  // 检查预热开关
  const cfg = getTtsConfig()
  if (!cfg.prewarm) return   // ← 开关关闭则不预热

  triggerWarmup(graphData)
    .catch(() => { /* 预热失败不阻塞用户操作 */ })
}, [graphData])
```

### 6.2 预热工具函数

如果按之前 `nav-tts-asset-management.md` 的设计实现 `triggerWarmup`，应放在独立文件 `src/utils/ttsWarmup.ts` 中：

```typescript
// src/utils/ttsWarmup.ts
import { getTtsConfig } from '../config/tts'
import { apiUrl } from './ttsPlayer'

interface GraphData {
  nodes: Array<{ id: string; graph_id: string; label: string; description?: string }>
}

export async function triggerWarmup(graphData: GraphData): Promise<void> {
  const cfg = getTtsConfig()
  if (!cfg.prewarm) return

  const items = graphData.nodes.map((n) => ({
    text: `${n.label}。${n.description || ''}`,
    voice: cfg.voice,
    rate: cfg.rate,
    pitch: cfg.pitch,
    source: `node/${n.graph_id || 'top'}/${n.id}`,
  }))

  await fetch(apiUrl('/api/tts/warmup'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ items }),
  })
}
```

### 6.3 切换图时的处理

当用户切换选择的导航图集合（多选框变化）时，也应重新判断预热逻辑：

```typescript
// 在 NavView 中监听 selectedGraphIds 变化
const selectedGraphIds = useNavStore((s) => s.selectedGraphIds)

useEffect(() => {
  if (!graphData?.nodes?.length) return
  const cfg = getTtsConfig()
  if (!cfg.prewarm) return
  triggerWarmup(graphData)
}, [selectedGraphIds, graphData])
```

---

## 7. prewarm 默认值的影响

| 用户场景 | prewarm 默认值 | 首次加载行为 |
|----------|---------------|-------------|
| 新用户（首次访问） | `true`（默认） | 自动预热 |
| 老用户升级（已有配置） | 旧配置不含 `prewarm`，`getTtsConfig` 合并后为 `true` | 自动预热 |
| 主动关闭的用户 | `false` | 不预热 |

老用户升级时，`{ ...DEFAULT, ...JSON.parse(raw) }` 中 `prewarm` 不在 `raw` 内，取 `DEFAULT.prewarm = true`，即 **所有用户默认受益**，无需手动开启。

---

## 8. 验证步骤

1. **默认开启验证**：
   - 清除 localStorage：`localStorage.removeItem('kn_tts_config')`
   - 调用 `getTtsConfig()` → `{ prewarm: true, ... }`
   - 加载导航图 → 看到后端日志有 `/api/tts/warmup` 请求

2. **关闭预热验证**：
   - 打开 TTS 设置弹窗，关闭"启用后台预热"开关，保存
   - `getTtsConfig()` → `{ prewarm: false, ... }`
   - 加载导航图 → 后端无 `/api/tts/warmup` 请求
   - 手动点击 TTS 按钮 → 正常合成播放（不走预热但存量逻辑不受影响）

3. **开关持久化验证**：
   - 重启浏览器
   - `getTtsConfig().prewarm` 保持关闭前的值

4. **重置默认验证**：
   - 点击设置弹窗的"重置默认"按钮
   - `prewarm` 恢复为 `true`
   - 保存后加载导航图 → 后端收到预热请求

---

## 9. 与 TTS 资产设计文档的关系

本 MD 对应 `nav-tts-asset-management.md` 第 8 节"预热配置开关"的详细实现。两者依赖关系：

```
nav-tts-asset-management.md         ← 整体 TTS 资产设计（含预热 API 定义）
  └── nav-tts-prewarm-toggle.md     ← 本文件：预热开关的详细实现
```

实现前后端预热功能时，需同时参考：
- **后端**: `nav-tts-asset-management.md` 第 5 节（预热 API）+ 第 6 节（`POST /api/tts/warmup`）
- **前端**: 本文件（开关 UI + 条件触发逻辑）
