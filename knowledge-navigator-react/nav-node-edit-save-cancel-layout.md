# 节点编辑面板保存/取消按钮位置

> 当前导航界面的 DropDownPanel 节点信息面板点击"编辑节点"会跳转到管理视图（TreeView）的 NodeEditPanel。真正的编辑、保存、取消应位于 NodeEditPanel 中，且遵循"保存仅本地缓存、同步写后端"的分离原则。

---

## 1. 当前架构回顾

### 1.1 两个面板的分工

| 面板 | 视图 | 功能 | 保存按钮 |
|------|------|------|----------|
| **DropDownPanel** | 导航界面（NavView） | 只读展示节点信息 | 无保存按钮，仅有"编辑节点"跳转按钮 |
| **NodeEditPanel** | 管理界面（TreeView） | 编辑节点字段、绑定卡片、管理出向连接 | 当前为自动保存（输入即写） |

### 1.2 当前保存链路（需改造）

```
NodeEditPanel
  ├─ input onChange → updateField('label', e.target.value)
  │     → mutateSelected()
  │       → commitToSource() → allNavNodes 更新 ✅
  │       → wtUpdateNode() → PUT /api/nodes/{id} → 后端 YAML ❌（需改为仅缓存）
  │
  ├─ textarea onChange → updateField('description', e.target.value)
  │     → 同上链路
  │
  ├─ BoundCardEditor add/remove → addBoundCard / removeBoundCard
  │     → 同上链路
  │
  └─ NextNodeEditor add/update/remove → addNextNode / updateNextNode / removeNextNode
        → 同上链路
```

当前每个输入操作都通过 `updateField` → `mutateSelected` → `commitToSource` 链路，既更新内存又写后端。改造后应拆为两步：**保存仅本地缓存**、**同步按钮写后端**。

---

## 2. 设计目标

### 2.1 DropDownPanel（导航面板）

- 保持当前"只读展示"模式不变
- "编辑节点"按钮 → 跳转到管理视图（TreeView）的 NodeEditPanel
- **不在 DropDownPanel 中增加任何编辑功能或保存按钮**

### 2.2 NodeEditPanel（管理面板）

- 将当前"自动保存"改为**显式保存/取消**
- **保存按钮** — 仅更新前端内存数据（`allNavNodes` + `navNodeMap`），不写后端
- **取消按钮** — 放弃本次编辑的所有更改，恢复为当前内存中的原始值
- 保存/取消按钮位于面板底部（删除区域的上方），固定位置

---

## 3. 改动文件清单

| 文件 | 改动内容 |
|------|----------|
| `src/components/node-mgr/NodeEditPanel.tsx` | 新增 draft state、保存/取消按钮、提交/放弃逻辑 |
| `src/components/node-mgr/NodeMgr.module.css` | 保存/取消按钮样式 + 底部操作栏容器 |
| `src/store/navNodeStore.ts` | `updateField` 中的 `commitToSource` 移除 `wtUpdateNode`（改为纯内存），新增 `saveAllDrafts` 方法用于同步时一次性写入后端 |
| `src/components/views/NavView.tsx` | 同步按钮 → 调用 `navNodeStore.saveAllDrafts()` 写后端（与现有 `POST /api/graphs/sync-all` 配合或独立实现） |

---

## 4. NodeEditPanel 布局

### 4.1 面板结构（保存/取消按钮位置）

```
┌──────────────────────────────────────────────┐
│  编辑面板 — 认知心理学简介                     │
│                                              │
│  ── 基本字段 ──                               │
│  id（只读）                                   │
│  node-cog-psy-foundation                     │
│                                              │
│  label                                       │
│  [认知心理学简介                    ] [✨]    │
│                                              │
│  description                                 │
│  ┌──────────────────────────────────────────┐│
│  │ 认知心理学是研究人类心理过程...           ││  ← 可编辑文本域
│  │                                          ││
│  └──────────────────────────────────────────┘│
│                                              │
│  ── 绑定卡片 ──                               │
│  [卡片1] [卡片2]          [+]                 │
│                                              │
│  ── 出向连接 ──                               │
│  [节点A] [节点B]          [+]                 │
│                                              │
│  ════════════════════════════════════════════ │  ← 分割线
│  [💾 保存]    [↩ 取消]                       │  ← 保存/取消按钮
│  ════════════════════════════════════════════ │
│                                              │
│  ── 浏览记录 ──                               │
│  [...]                                       │
│                                              │
│  ── 危险操作 ──                               │
│  [删除节点]                                   │
└──────────────────────────────────────────────┘
```

关键布局决策：
- **保存/取消按钮**固定在面板底部偏上位置，用一个分割线隔离上下区域
- 保存/取消区域与浏览记录、删除操作保持视觉分离
- 保存后不关闭面板，用户可继续编辑其他字段
- 同步按钮在导航视图右上角，集中完成全量持久化

### 4.2 组件改动

**文件**: `src/components/node-mgr/NodeEditPanel.tsx`

```typescript
// ── 局部草稿状态（替代直接 updateField） ──
const [draftLabel, setDraftLabel] = useState(node.label)
const [draftDesc, setDraftDesc] = useState(node.description || '')
const [dirty, setDirty] = useState(false)

// 同步草稿标志：任意字段变化时标记 dirty
useEffect(() => {
  setDraftLabel(node.label)
  setDraftDesc(node.description || '')
  setDirty(false)
}, [node.id]) // eslint-disable-line react-hooks/exhaustive-deps

// ── 保存（仅本地缓存） ──
const handleSave = () => {
  updateField('label', draftLabel)
  updateField('description', draftDesc)
  setDirty(false)
  toast('节点已保存（本地缓存）')
}

// ── 取消（放弃草稿） ──
const handleCancel = () => {
  setDraftLabel(node.label)
  setDraftDesc(node.description || '')
  setDirty(false)
  toast('已放弃修改')
}
```

JSX 中的输入框改为绑定 draft state：

```tsx
<input
  className={styles.input}
  value={draftLabel}
  onChange={(e) => {
    setDraftLabel(e.target.value)
    setDirty(true)
  }}
/>
<textarea
  className={styles.textarea}
  rows={3}
  value={draftDesc}
  onChange={(e) => {
    setDraftDesc(e.target.value)
    setDirty(true)
  }}
/>
```

在 BoundCardEditor 和 NextNodeEditor 之后、删除区域之前插入保存/取消按钮行：

```tsx
<BoundCardEditor node={node} />
<NextNodeEditor node={node} />

{/* ── 保存/取消按钮 ── */}
<div className={styles.saveBar}>
  <button
    className={styles.saveBtn}
    onClick={handleSave}
    disabled={!dirty}
  >
    💾 保存
  </button>
  <button
    className={styles.cancelBtn}
    onClick={handleCancel}
    disabled={!dirty}
  >
    ↩ 取消
  </button>
  <span className={styles.saveHint}>
    {dirty ? '有未保存的更改' : '已是最新'}
  </span>
</div>

<BrowseHistoryViewer node={node} />

{/* 删除节点 */}
<section className={styles.section}>
```

---

## 5. 样式

**文件**: `src/components/node-mgr/NodeMgr.module.css`

```css
/* ── 保存/取消操作栏 ── */
.saveBar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 0;
  border-top: 1px solid var(--separator);
  border-bottom: 1px solid var(--separator);
}

.saveBtn {
  padding: 8px 20px;
  background: var(--accent, #06b6d4);
  border: none;
  border-radius: var(--radius-sm);
  color: #fff;
  font-size: 13px;
  font-weight: 500;
  font-family: var(--font-sans);
  cursor: pointer;
  transition: opacity 0.15s;
}

.saveBtn:hover:not(:disabled) {
  opacity: 0.85;
}

.saveBtn:disabled {
  opacity: 0.4;
  cursor: default;
}

.cancelBtn {
  padding: 8px 16px;
  background: transparent;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  color: var(--label-secondary);
  font-size: 13px;
  font-family: var(--font-sans);
  cursor: pointer;
  transition: background 0.15s;
}

.cancelBtn:hover:not(:disabled) {
  background: var(--fill-f1);
}

.cancelBtn:disabled {
  opacity: 0.4;
  cursor: default;
}

.saveHint {
  margin-left: auto;
  font-size: 11px;
  color: var(--label-quaternary);
}
```

---

## 6. 保存链路改造

### 6.1 navNodeStore 改造

**文件**: `src/store/navNodeStore.ts`

```typescript
/**
 * 将更新后的节点写回共享数据源（allNavNodes 数组 + navNodeMap）。
 * 不再自动写后端，持久化由 saveAllDrafts() 统一完成。
 */
function commitToSource(updated: NavNode) {
  const idx = allNavNodes.findIndex((n) => n.id === updated.id)
  if (idx >= 0) allNavNodes[idx] = updated
  navNodeMap.set(updated.id, updated)
  // ❌ 移除了 wtUpdateNode(updated) — 持久化交由同步按钮统一处理
}
```

新增批量持久化方法供同步按钮调用：

```typescript
/**
 * 将所有已保存到内存的节点变更一次性写回后端 YAML。
 * 由导航视图右上角的 🔄 同步 按钮触发。
 */
export async function saveAllDraftsToBackend(): Promise<number> {
  let count = 0
  for (const node of allNavNodes) {
    await wtUpdateNode(node)
    count++
  }
  return count
}
```

### 6.2 NavView 同步按钮联动

**文件**: `src/components/views/NavView.tsx`

同步按钮的 `handleSync` 增加 `saveAllDraftsToBackend` 调用，确保节点编辑的缓存变更也一并写入后端：

```typescript
const handleSync = async () => {
  if (!isProMode()) {
    toast('无后端模式无需同步')
    return
  }
  setSyncing(true)
  try {
    // 1. 将所有节点缓存写回后端
    const nodeCount = await saveAllDraftsToBackend()
    // 2. 触发后端全量 YAML 写盘（含卡片、边等）
    const baseUrl = getBackendConfig().baseUrl
    const resp = await fetch(`${baseUrl}/api/graphs/sync-all`, { method: 'POST' })
    if (!resp.ok) throw new Error(`同步失败: ${resp.status}`)
    const data = await resp.json()
    toast(`同步完成: ${nodeCount} 个节点 + ${data.saved_graphs} 个图已保存`)
  } catch (e) {
    toast('同步失败: ' + (e instanceof Error ? e.message : '网络错误'))
  } finally {
    setSyncing(false)
  }
}
```

---

## 7. 完整操作链路

```
┌─────────────────────────────────────────────────────────────┐
│  导航界面（NavView）                                         │
│                                                             │
│  节点信息面板 (DropDownPanel)                                │
│    ┌──────────────────────────────────┐                     │
│    │  认知心理学简介       [⊞] [⛶] 📄  │                     │
│    │  描述文字...                       │                     │
│    │  [添加为途径点]  [编辑节点]         │                     │
│    └──────────────────────────────────┘                     │
│          │ 点击"编辑节点"                                    │
│          ▼                                                   │
│  跳转到管理视图 → 选中该节点 → NodeEditPanel 展示              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  管理视图（TreeView）                                        │
│                                                             │
│  NodeEditPanel                                              │
│    label: [认知心理学简介              ]  ← draft state     │
│    desc:  [认知心理学是研究...         ]  ← draft state     │
│                                                             │
│    ════════════════════════════════════════════              │
│    [💾 保存]  [↩ 取消]          有未保存的更改               │
│    ════════════════════════════════════════════              │
│                                                             │
│    [删除节点]                                                │
│                                                             │
│  用户点击"保存" → draft → updateField → allNavNodes 更新     │
│                     (本地缓存, 不写后端)                      │
└─────────────────────────────────────────────────────────────┘
         │
         ▼  返回导航视图
┌─────────────────────────────────────────────────────────────┐
│  导航界面（NavView）                                         │
│                                                             │
│  右上角: [🔄 同步]                                           │
│                                                             │
│  用户点击"同步" → saveAllDraftsToBackend()                    │
│                  → fetch POST /api/graphs/sync-all           │
│                  → 后端 write YAML                           │
│                  → Toast"同步完成"                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. 边界情况处理

| 场景 | 行为 |
|------|------|
| 用户修改后未保存就离开当前节点（选中其他节点） | `useEffect` 在 `node.id` 变化时重置草稿为原始值，丢失未保存修改 |
| 用户修改后保存，离开再回来 | 已通过 `updateField` 写入 `allNavNodes`，重新选中时读取最新值 |
| 用户保存后未同步，刷新页面 | 浏览器刷新 → 前端内存丢失 → 读取后端 YAML → 未同步的变更丢失 |
| 保存时 dirty 为 false | 保存按钮 disabled，无法点击 |
| 同步时网络失败 | Toast 提示失败，用户可重试 |
| 同时编辑多个节点 | 每个节点独立草稿状态（`node.id` 变化时重置） |

---

## 9. 验证步骤

1. **进入编辑面板**：导航画布点击节点 → DropDownPanel 展开 → 点击"编辑节点" → 跳转到管理视图 → NodeEditPanel 显示该节点数据
2. **修改后取消**：修改 label → 点击"取消" → label 恢复原值 → 提示"已放弃修改"
3. **修改后保存**：修改 label → 点击"保存" → 提示"节点已保存（本地缓存）" → panel 数据已更新
4. **确认未写后端**：检查后端 YAML 文件 → 节点 label **未**更新
5. **同步到后端**：返回导航视图 → 点击右上角"🔄 同步" → 提示"同步完成: 1 个节点 + N 个图已保存"
6. **确认后端已写**：检查后端 YAML 文件 → 节点 label 已更新
7. **刷新浏览器**：重新加载页面 → 节点 label 为同步后的值（从后端加载）
