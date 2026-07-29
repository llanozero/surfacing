# 导航界面清理：删除同步按钮 + 修复多选折叠框

## 变更说明

| 变更项 | 原因 | 涉及文件 |
|--------|------|----------|
| 删除导航视图同步按钮 | 同步功能已迁移到统一设置面板的"同步"Tab | [NavView.tsx](file:///c:/Users/llano/Desktop/龙虾/surfacing/knowledge-navigator-react/src/components/views/NavView.tsx) |
| 清理 syncBtn CSS 样式 | 样式冗余 | [NavView.module.css](file:///c:/Users/llano/Desktop/龙虾/surfacing/knowledge-navigator-react/src/components/views/NavView.module.css) |
| 修复多选折叠框丢失 | NavView 外部 `!inDrill` 守卫与组件内部自检重复，导致非钻入状态下也被隐藏 | [NavView.tsx](file:///c:/Users/llano/Desktop/龙虾/surfacing/knowledge-navigator-react/src/components/views/NavView.tsx) |

## 一、删除同步按钮

### 删除的代码

**1. 导入（NavView.tsx:31-32）**

```typescript
// 已删除：
import { saveAllDraftsToBackend } from '../../store/navNodeStore'
import { isProMode, getBackendConfig } from '../../config/backend'
```

**2. 状态和 handler（NavView.tsx:171-193）**

```typescript
// 已删除：
const [syncing, setSyncing] = useState(false)

const handleSync = async () => {
  if (!isProMode()) {
    toast('无后端模式无需同步')
    return
  }
  setSyncing(true)
  try {
    const nodeCount = await saveAllDraftsToBackend()
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

**3. JSX 按钮（NavView.tsx:299-308）**

```tsx
{/* 已删除：
{isProMode() && (
  <button className={styles.syncBtn} onClick={handleSync} disabled={syncing}
    title="同步所有数据到后端 YAML 文件">
    {syncing ? '⏳' : '🔄'} 同步
  </button>
)}
*/}
```

**4. CSS 样式（NavView.module.css:22-37）**

```css
/* 已删除 .syncBtn 及其 hover/disabled 子规则 */
```

### 同步功能去哪里了

同步功能仍然存在，入口已迁移到统一设置面板（[SettingsDialog.tsx](file:///c:/Users/llano/Desktop/龙虾/surfacing/knowledge-navigator-react/src/components/settings/SettingsDialog.tsx)）的"同步"Tab，通过 StatusBar 的 ⚙ 按钮访问。

## 二、修复多选折叠框

### 问题

NavView.tsx 第 316 行：

```tsx
{!inDrill && <GraphMultiSelect />}
```

而 [GraphMultiSelect.tsx](file:///c:/Users/llano/Desktop/龙虾/surfacing/knowledge-navigator-react/src/components/nav/GraphMultiSelect.tsx) 第 35 行自身已有 drill 状态守卫：

```tsx
if (inDrill || graphs.length <= 1) return null
```

外部 `!inDrill` 守卫与组件内部自检重复。当用户钻入/钻出时，两个 `inDrill` 值（都取自 `useDrillStore((s) => s.stack)`）可能因 zustand 订阅时机差异导致组件在非钻入状态下也被隐藏。

### 修复

移除外部守卫，让 GraphMultiSelect 自身完全控制渲染条件：

```tsx
{/* 修复前 */}
{!inDrill && <GraphMultiSelect />}

{/* 修复后 */}
<GraphMultiSelect />
```

### 渲染条件（由 GraphMultiSelect 内部控制）

| 条件 | 行为 |
|------|------|
| `drillStack.length > 0`（钻入状态） | `return null`，不渲染 |
| `graphs.length <= 1`（少于 2 个图） | `return null`，不渲染 |
| 其他情况 | 渲染折叠框，默认折叠状态（`collapsed = true`） |

## 涉及文件

| 文件 | 变更 |
|------|------|
| [NavView.tsx](file:///c:/Users/llano/Desktop/龙虾/surfacing/knowledge-navigator-react/src/components/views/NavView.tsx) | 删除 `saveAllDraftsToBackend`/`isProMode`/`getBackendConfig` 导入；删除 `syncing` state 和 `handleSync`；删除 JSX 同步按钮；移除 GraphMultiSelect 外部 `!inDrill` 守卫 |
| [NavView.module.css](file:///c:/Users/llano/Desktop/龙虾/surfacing/knowledge-navigator-react/src/components/views/NavView.module.css) | 删除 `.syncBtn` 样式块 |
| [GraphMultiSelect.tsx](file:///c:/Users/llano/Desktop/龙虾/surfacing/knowledge-navigator-react/src/components/nav/GraphMultiSelect.tsx) | 未修改（内部 drill 守卫本身已完善） |
