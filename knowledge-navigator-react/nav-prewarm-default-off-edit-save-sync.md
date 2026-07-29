# 预热默认关 + 节点编辑保存按钮 + 右上角同步按钮

> 三项改动：调整预热开关默认值、在导航画布面板中支持原地编辑并保存节点、在导航界面右上角增加一键同步按钮。

---

## 1. 预热开关默认改为关

### 1.1 改动

**文件**: `src/config/tts.ts`

```typescript
// 修改前
const DEFAULT: TtsConfig = {
  voice: 'zh-CN-XiaoxiaoNeural',
  rate: '+0%',
  pitch: '+0Hz',
  prewarm: true,
}

// 修改后
const DEFAULT: TtsConfig = {
  voice: 'zh-CN-XiaoxiaoNeural',
  rate: '+0%',
  pitch: '+0Hz',
  prewarm: false,
}
```

### 1.2 影响

| 场景 | 修改前 | 修改后 |
|------|--------|--------|
| 新用户首次访问 | 自动预热 | 不预热 |
| 老用户升级（已有配置） | 旧配置无 `prewarm`，合并后为 `true` | 同左（已有配置中的值不受影响） |
| 用户手动开启 | 预热 | 预热 |

老用户升级时，`getTtsConfig()` 的 `{ ...DEFAULT, ...JSON.parse(raw) }` 逻辑中，`raw` 不含 `prewarm`，所以仍取 `true`。仅在 **手动清除 localStorage 或首次访问的新用户** 才会走 `false`。

---

## 2. 节点编辑界面增加保存按钮

### 2.1 设计目标

当前 DropDownPanel 的"编辑节点"按钮会跳转到 TreeView 管理视图进行修改。本功能在 DropDownPanel 的 **全屏（full）态** 中直接增加一个 **编辑模式**，让用户在查看节点详情的同时可以原地修改 label 和 description。

**保存 vs 同步分离**：
- **保存按钮** — 仅更新前端内存数据（local cache），不写后端
- **同步按钮** — 将前端所有内存改动统一写回后端 YAML 文件

这样修改少量字段时本地即时生效，确认无误后一次性同步到后端，避免每次保存都触发后端写入。

### 2.2 改动文件清单

| 文件 | 改动内容 |
|------|----------|
| `src/components/panel/DropDownPanel.tsx` | 增加编辑模式切换、可编辑字段、保存按钮 |
| `src/components/panel/DropDownPanel.module.css` | 编辑模式样式 |
| `src/store/navNodeStore.ts` | 暴露 `updateField` 或新增 `saveNode` 方法 |
| `src/api/writeThrough.ts` | 确认 `wtUpdateNode` 已支持后端同步 |

### 2.3 UI 布局

在 full 态的节点详情区域增加"编辑"按钮，点击后切换字段为可编辑状态：

```
┌─────────────────────────────────────────┐
│  手柄 (拖拽区域)                          │
│                                         │
│  认知心理学简介          [⊞] [⛶] [📄] 🔊  │   ← headRow
│  ─────────────────────────────────────  │
│  label: [认知心理学简介            ]     │   ← 可编辑输入框
│                                         │
│  description:                           │
│  ┌──────────────────────────────────┐   │
│  │ 认知心理学是研究人类心理过程的   │   │   ← 可编辑文本域
│  │ 科学，涵盖注意力、记忆、思维等   │   │
│  │ 领域...                          │   │
│  └──────────────────────────────────┘   │
│                                         │
│  绑定卡片 2 · 出向连接 3                 │   ← 只读统计
│                                         │
│  [跳转到源图]  [添加为途径点]  [保存]     │   ← 编辑态显示"保存"
│                                         │   ← 非编辑态显示"编辑节点"
└─────────────────────────────────────────┘
```

### 2.4 组件改动要点

**文件**: `src/components/panel/DropDownPanel.tsx`

```typescript
// 新增编辑状态
const [editing, setEditing] = useState(false)
const [editLabel, setEditLabel] = useState('')
const [editDesc, setEditDesc] = useState('')
const [saving, setSaving] = useState(false)

// 进入编辑模式
const handleStartEdit = () => {
  setEditLabel(node.label)
  setEditDesc(node.description || '')
  setEditing(true)
}

// 取消编辑
const handleCancelEdit = () => {
  setEditing(false)
}

// 保存编辑（仅更新前端内存数据，不写后端）
const handleSaveEdit = () => {
  if (!node) return
  const updated = { ...node, label: editLabel, description: editDesc }

  // 更新本地数据源
  const { allNavNodes, navNodeMap } = allNodesModule
  const idx = allNavNodes.findIndex((n) => n.id === node.id)
  if (idx >= 0) allNavNodes[idx] = updated
  navNodeMap.set(node.id, updated)

  // 刷新面板显示
  usePanelStore.getState().setNode(updated)

  toast('节点已保存（本地缓存）')
  setEditing(false)
}
```

### 2.5 编辑模式 JSX 渲染

```tsx
{/* 编辑态：可编辑字段 */}
{editing ? (
  <div className={styles.editFields}>
    <label className={styles.editField}>
      <span className={styles.editLabel}>label</span>
      <input
        className={styles.editInput}
        value={editLabel}
        onChange={(e) => setEditLabel(e.target.value)}
      />
    </label>
    <label className={styles.editField}>
      <span className={styles.editLabel}>description</span>
      <textarea
        className={styles.editTextarea}
        value={editDesc}
        onChange={(e) => setEditDesc(e.target.value)}
        rows={4}
      />
    </label>
  </div>
) : (
  <>
    <h3 className={styles.nodeLabel}> ... </h3>
    <p className={styles.nodeDesc}>{node.description}</p>
  </>
)}

{/* 底部按钮：编辑态显示保存/取消，非编辑态显示编辑节点 */}
{position === 'full' && (
  <div className={styles.actions}>
    {editing ? (
      <>
        <Button variant="primary" onClick={handleSaveEdit} disabled={saving}>
          {saving ? '保存中...' : '保存'}
        </Button>
        <Button variant="outline" onClick={handleCancelEdit}>
          取消
        </Button>
      </>
    ) : (
      <>
        {isRef && sourceGraphId && (
          <Button variant="outline" onClick={handleJumpToSource}>
            跳转到源图「{sourceGraphLabel || sourceGraphId}」
          </Button>
        )}
        <Button variant="primary" onClick={handleAddWaypoint}>
          添加为途径点
        </Button>
        <Button variant="outline" onClick={handleStartEdit}>
          编辑节点
        </Button>
      </>
    )}
  </div>
)}
```

### 2.6 Save 按钮逻辑流程图

```
用户点击"编辑节点" → setEditing(true)
  → headRow 下方显示可编辑输入框和文本域
  → 底部按钮变为 [保存] [取消]

用户修改 label/description → editLabel/editDesc 更新

用户点击"保存"
  → 更新 allNavNodes 和 navNodeMap（本地内存立即生效）
  → 更新 panelStore 中的 node（面板即时反映）
  → Toast"节点已保存（本地缓存）"
  → setEditing(false)，恢复只读显示
  └── ⚠️ 此时后端 YAML 尚未更新，需点击右上角 🔄 同步 持久化

用户点击"取消"
  → 放弃更改，setEditing(false)，恢复只读显示
```

> 保存后 panelStore 中的 `node` 对象已是最新的，画布上该节点的 label 也会即时刷新（D3 通过 `useEffect` 监听 `allNodes` 重新渲染）。

### 2.7 编辑模式样式

**文件**: `src/components/panel/DropDownPanel.module.css`

```css
/* ── 编辑模式 ── */
.editFields {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 4px 0;
}

.editField {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.editLabel {
  font-size: 11px;
  font-weight: 500;
  color: var(--label-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.editInput,
.editTextarea {
  background: var(--fill-f2);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  color: var(--label-primary);
  font-size: 13px;
  font-family: var(--font-sans);
  padding: 8px 10px;
  transition: border-color 0.15s;
}

.editInput:focus,
.editTextarea:focus {
  outline: none;
  border-color: var(--accent, #06b6d4);
}

.editTextarea {
  resize: vertical;
  min-height: 60px;
  line-height: 1.5;
}
```

---

## 3. 右上角增加同步按钮

### 3.1 设计目标

在 NavView 的 header 区域（标题右侧）增加一个"同步"按钮，点击后将 **前端内存中所有图数据** 统一写回后端 YAML 文件。

**同步按钮承担了全部的持久化职责**：

```
编辑节点 → [保存] → 前端 allNavNodes 内存更新（本地缓存）
                      ↓ 等待用户确认
                      → [🔄 同步] → POST /api/graphs/sync-all
                                      → 后端遍历 store.graphs
                                      → 全部写回 YAML 文件
                                      → 更新 manifest 计数
```

关键原则：
- 保存（本地）和同步（后端）严格分离，两步操作
- 同步是 **全量** 操作，不仅写入保存的节点编辑，也涵盖所有图数据的最新内存状态
- 同步按钮仅在 Pro 模式下显示（本地模式无后端）
- 点击后前端不发送节点数据本身，而是触发后端直接从其内存 `store.graphs` 写 YAML（因为前端 NodeEditPanel 等编辑操作已通过 `wtUpdateNode` 实时同步到后端内存）

### 3.2 改动文件清单

| 文件 | 改动内容 |
|------|----------|
| `src/components/views/NavView.tsx` | header 中增加同步按钮 + 点击处理 |
| `src/components/views/NavView.module.css` | 同步按钮样式 |
| `backend/app/routers/graphs.py` | 新增 `POST /api/graphs/sync-all` 全量同步接口 |
| `backend/app/store.py` | 新增 `save_all()` 方法 |

### 3.3 UI 布局

在 NavView 的 header 区域右侧增加同步按钮：

```
┌─────────────────────────────────────────────┐
│  认知导航                                      │
│  当前节点: 认知心理学简介    [🔄 同步]         │
└─────────────────────────────────────────────┘
```

按钮放置逻辑：
- 位于 `.header` 内，使用 `justify-content: space-between` 或绝对定位靠右
- 仅在 Pro 模式下显示（本地模式无后端）
- 点击后有 loading 状态反馈
- 同步完成后显示 Toast 提示

### 3.4 前端改动

**文件**: `src/components/views/NavView.tsx`

```typescript
import { isProMode, getBackendConfig } from '../../config/backend'

const [syncing, setSyncing] = useState(false)

const handleSync = async () => {
  if (!isProMode()) {
    toast('无后端模式无需同步')
    return
  }
  setSyncing(true)
  try {
    const baseUrl = getBackendConfig().baseUrl
    const resp = await fetch(`${baseUrl}/api/graphs/sync-all`, { method: 'POST' })
    if (!resp.ok) throw new Error(`同步失败: ${resp.status}`)
    const data = await resp.json()
    toast(`同步完成: ${data.saved_graphs} 个图已保存`)
  } catch (e) {
    toast('同步失败: ' + (e instanceof Error ? e.message : '网络错误'))
  } finally {
    setSyncing(false)
  }
}
```

在 JSX header 中添加按钮：

```tsx
<div className={styles.header}>
  <div className={styles.headerLeft}>
    <h2 className={styles.title}>认知导航</h2>
    {currentNode && hasCanvasData && (
      <p className={styles.subtitle}>当前节点: {currentNode.label}</p>
    )}
  </div>
  {isProMode() && (
    <button
      className={styles.syncBtn}
      onClick={handleSync}
      disabled={syncing}
      title="同步所有数据到后端 YAML 文件"
    >
      {syncing ? '⏳' : '🔄'} 同步
    </button>
  )}
</div>
```

**文件**: `src/components/views/NavView.module.css`

```css
.header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  flex-shrink: 0;
}

.headerLeft {
  flex: 1;
  min-width: 0;
}

.syncBtn {
  flex-shrink: 0;
  margin-top: 2px;
  background: var(--fill-f1);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  color: var(--label-secondary);
  font-size: 12px;
  padding: 4px 10px;
  cursor: pointer;
  font-family: var(--font-sans);
  transition: background 0.15s, color 0.15s;
  white-space: nowrap;
}

.syncBtn:hover {
  background: var(--fill-f2);
  color: var(--label-primary);
}

.syncBtn:disabled {
  opacity: 0.5;
  cursor: default;
}
```

### 3.5 后端改动

**文件**: `backend/app/routers/graphs.py`

```python
# 新增全量同步路由
@router.post("/sync-all")
def sync_all_graphs() -> dict[str, Any]:
    """将所有内存中的图数据写回 YAML 文件。"""
    saved = store.save_all()
    return {"ok": True, "saved_graphs": saved}
```

**文件**: `backend/app/store.py`

```python
def save_all(self) -> int:
    """将所有内存中的图数据写回 YAML 文件，返回保存的图数量。"""
    with self._lock:
        count = 0
        for gid, g in self.graphs.items():
            filepath = GRAPHS_DIR / f"{gid}.yaml"
            g.save(filepath)
            count += 1
        # 同步更新 manifest 计数
        for entry in self.manifest.get("graphs", []):
            gid = entry.get("graph_id", "")
            g = self.graphs.get(gid)
            if g:
                entry["node_count"] = len(g.nodes)
                entry["card_count"] = len(g.cards)
        self._save_manifest()
        return count
```

### 3.6 同步按钮触发链路

```
用户点击 🔄 同步
  → fetch POST /api/graphs/sync-all
  → 后端 store.save_all()
    → 遍历所有 graph_id → Graph.save(filepath) → 写 YAML
    → 更新 manifest 计数 → _save_manifest()
  → 返回 { saved_graphs: N }
  → 前端 Toast"同步完成: N 个图已保存"
```

---

## 4. 合计改动清单

| # | 文件 | 改动类型 | 说明 |
|---|------|----------|------|
| 1 | `src/config/tts.ts` | 修改 | `prewarm` 默认值 `true` → `false` |
| 2 | `src/components/panel/DropDownPanel.tsx` | 修改 | 增加编辑模式状态、编辑/保存/取消处理函数、编辑态 JSX |
| 3 | `src/components/panel/DropDownPanel.module.css` | 修改 | 增 `.editFields`、`.editInput`、`.editTextarea` 等样式 |
| 4 | `src/components/views/NavView.tsx` | 修改 | header 中增加同步按钮 + 点击处理函数 |
| 5 | `src/components/views/NavView.module.css` | 修改 | `header` 改为 `space-between`，新增 `.headerLeft`、`.syncBtn` 样式 |
| 6 | `backend/app/routers/graphs.py` | 修改 | 新增 `POST /api/graphs/sync-all` 路由 |
| 7 | `backend/app/store.py` | 修改 | 新增 `save_all()` 方法 |

---

## 5. 验证步骤

### 5.1 预热默认关
1. 清除 localStorage：`localStorage.removeItem('kn_tts_config')`
2. 调用 `getTtsConfig()` → `{ prewarm: false, ... }`
3. 加载导航图 → 后端无 `/api/tts/warmup` 请求

### 5.2 节点编辑保存
1. 在导航画布中点击节点 → DropDownPanel 展开
2. 切换到 full 态，点击"编辑节点"
3. label 和 description 变为可编辑输入框
4. 修改 label 为"新标题"，点击"保存"
5. 面板显示新标题，关闭再打开 → 保留修改
6. 检查后端 YAML 文件 → 该节点的 label 已更新
7. 点击"编辑节点"→ 修改后点击"取消" → 恢复原始内容

### 5.3 同步按钮
1. Pro 模式下进入导航视图
2. 右上角显示 🔄 同步 按钮
3. 点击同步按钮 → 按钮变为 ⏳ 同步（disabled）
4. 完成后 Toast 显示"同步完成: N 个图已保存"
5. 检查后端 graphs/ 目录下 YAML 文件更新时间
6. Lite 模式（无后端）→ 同步按钮不显示
