# 多层钻出后快照丢失修复

## 问题描述

多层钻入后再逐层钻出，最后一次钻出后画布未恢复顶层全量数据。

### 影响场景

- 用户勾选 `['g1', 'g2', 'g3']` 展示全量画布
- 钻入 g1→g2（第一次钻入）
- 再钻入 g2→g3（第二次钻入）
- 钻出 g3→g2（第一次钻出）：**正常**
- 钻出 g2→g1（第二次钻出）：**异常** — 画布仍显示 g2 数据而非全量 `['g1', 'g2', 'g3']`

### 修复前数据流追踪

```
g1→g2 钻入:  snapshot ← ['g1','g2','g3']     ✅ 正确保存
g2→g3 钻入:  snapshot ← ['g2']                ❌ 覆盖了原快照
g3→g2 钻出:  恢复 snapshot=['g2'] → 清空      ⚠️ 恢复正确，但清空丢失了上层快照
g2→g1 钻出:  snapshot=[] → 跳过恢复            ❌ 无法恢复 ['g1','g2','g3']
```

---

## 根因

快照 `snapshotSelectedGraphIds` 是钻入栈上的**全局独立变量**，而非存储在钻入栈项中。每次钻入无条件覆盖它，每次钻出恢复后清空它：

```
钻入栈（stack）             快照（snapshot）
[{g1}]                      ['g1','g2','g3']   ← 第一层钻入
[{g1}, {g2}]                ['g2']             ← 覆盖了
pop → {g2}                  清空 → []           ← 恢复后清空
pop → {g1}                  空 → 无法恢复        ← ❌
```

---

## 修复方案

将快照信息**存储在钻入栈项中**，每层钻入保存各自的快照，钻出时从**弹出的栈项**恢复。

### 改动清单

| 文件 | 变更 |
|------|------|
| `src/store/drillStore.ts` | `DrillStackItem` 新增 `snapshot: string[]` 字段 |
| `src/store/graphStore.ts` | `drillIn()` 新增 `snapshot` 参数，传递给 push |
| `src/components/views/NavView.tsx` | `handleDrillIn` 传参给 `drillIn`；`handleDrillOut` 从 `popped.snapshot` 恢复 + `setPanelNode` 同步面板 |
| `src/components/views/FreeBrowseView.tsx` | 同上变更 |

### 改动详情

#### 1. `src/store/drillStore.ts` — DrillStackItem 新增 snapshot

```typescript
export interface DrillStackItem {
  parentGraphId: string
  parentNodeId: string
  subGraphId: string
  entryNodeId: string
  parentNodeLabel: string
  subGraphLabel: string
  snapshot: string[]    // ← 新增：钻入前的 selectedGraphIds 快照（钻出时恢复）
}
```

#### 2. `src/store/graphStore.ts` — drillIn 传递 snapshot

```typescript
// 签名新增 snapshot 参数
drillIn: (subGraphId, entryNodeId, parentNodeId, parentNodeLabel, snapshot) => {
  // ...
  useDrillStore.getState().push({
    // ... 原有字段 ...
    snapshot,   // ← 保存在栈项中
  })
}
```

#### 3. `src/components/views/NavView.tsx` — handleDrillIn 和 handleDrillOut

**handleDrillIn**：移除 `setSnapshot()` 调用，改为传参

```typescript
const handleDrillIn = () => {
  // ...
  const currentSelected = useNavStore.getState().selectedGraphIds
  // ← 不再调用 setSnapshot(currentSelected)

  useNavStore.getState().setSelectedGraphs([targetId])
  drillIn(targetId, entryId, currentNode.id, currentNode.label, currentSelected)
  //                                                           ↑ 传参
  setCurrentNode(entryId)
}
```

**handleDrillOut**：从 `popped.snapshot` 恢复，同步更新面板

```typescript
const handleDrillOut = () => {
  const popped = useGraphStore.getState().drillOut()
  if (popped) {
    setCurrentNode(popped.parentNodeId)

    // 从弹出的栈项中恢复对应层的快照
    if (popped.snapshot && popped.snapshot.length > 0) {
      useNavStore.getState().setSelectedGraphs(popped.snapshot)
    }

    // 恢复面板显示的节点（子图节点的选中状态）
    const parentNode = getCurrentNode({ currentNodeId: popped.parentNodeId })
    if (parentNode) setPanelNode(parentNode)

    toast(`已钻出，回到「${popped.parentNodeLabel}」`)
  }
}
```

#### 4. `src/components/views/FreeBrowseView.tsx` — 同步修复

与 NavView 完全相同的逻辑变更。

---

## 修复后数据流

```
按 g1,g2,g3 → top 画布显示全量

钻入 g1→g2:
  stack = [{snapshot: ['g1','g2','g3']}]
  画布 → g2

钻入 g2→g3:
  stack = [{snapshot: ['g1','g2','g3']}, {snapshot: ['g2']}]
  画布 → g3

钻出 g3→g2:
  popped = {snapshot: ['g2'], ...}
  恢复 selectedGraphIds = ['g2']
  stack = [{snapshot: ['g1','g2','g3']}]
  画布 → g2 ✅

钻出 g2→g1:
  popped = {snapshot: ['g1','g2','g3'], ...}
  恢复 selectedGraphIds = ['g1','g2','g3']
  stack = []
  画布 → 全量聚合 ✅
```

### 关键改进点

| 方面 | 修复前 | 修复后 |
|------|--------|--------|
| 快照存储位置 | `drillStore.snapshotSelectedGraphIds`（全局独立） | `DrillStackItem.snapshot`（每层独立） |
| 快照覆盖 | 每次钻入无条件覆盖 | 每层钻入保存自己的快照到栈项 |
| 快照恢复 | 从全局变量读，恢复后清空 | 从弹出的栈项读，不影响其他层 |
| 多层钻出 | 第二次钻出时快照已空 | 每层钻出都能恢复自己的快照 |

---

## 改进二：钻出时恢复选中节点以更新面板

### 问题

钻出子图后，`currentNode` 虽然正确恢复为子图节点的 ID，但 `panelStore` 中显示的节点未同步更新。面板（DropDownPanel）仍显示钻出前的子图内节点数据，而非钻出后的子图节点数据。

### 根因

`handleDrillOut` 仅调用 `setCurrentNode(popped.parentNodeId)` 更新了导航状态，但未调用 `setPanelNode` 更新面板状态：

```typescript
// 修复前：仅更新 currentNode，面板未同步
const handleDrillOut = () => {
  const popped = useGraphStore.getState().drillOut()
  if (popped) {
    setCurrentNode(popped.parentNodeId)
    // ❌ 缺少 setPanelNode 调用
    // 面板仍显示旧数据
  }
}
```

### 修复

在 `handleDrillOut` 中恢复 `currentNode` 后，同步恢复面板显示的节点：

```typescript
// 修复后：面板随 currentNode 同步更新
const handleDrillOut = () => {
  const popped = useGraphStore.getState().drillOut()
  if (popped) {
    setCurrentNode(popped.parentNodeId)

    // 恢复面板显示的节点（子图节点的选中状态）
    const parentNode = getCurrentNode({ currentNodeId: popped.parentNodeId })
    if (parentNode) setPanelNode(parentNode)

    // ... 恢复快照 ...
    toast(`已钻出，回到「${popped.parentNodeLabel}」`)
  }
}
```

### 数据流追踪

```
钻入 g1→g2 前:
  currentNode = node-math-subgraph (子图节点)
  panelNode  = node-math-subgraph
  ↓ 钻入
  currentNode = node-probability-theory (g2 入口)
  panelNode  = node-probability-theory

在 g2 中导航到 node-bayes-theorem:
  currentNode = node-bayes-theorem
  panelNode  = node-bayes-theorem
  ↓ 钻出
  currentNode = node-math-subgraph (从栈项恢复)
  panelNode  = node-math-subgraph (← 修复：同步恢复)
```

---

## 验证步骤（完整）

1. 选择 g1+g2+g3 → 全览画布显示全量聚合节点
2. 点击 g1 的子图节点 `node-math-subgraph` → 钻入 g2
3. 在 g2 中导航到 `node-cog-psy-subgraph` → 钻入 g3
4. 在 g3 中导航后点击钻出
   - 画布恢复为 g2 数据，面包屑回退到 `top / g2`
5. 再次点击钻出
   - 画布恢复为全量 `['g1','g2','g3']` 聚合数据，面包屑回退到 `top`

---

## 编译验证

```
npx tsc --noEmit
→ exit code 0，编译零错误
```
