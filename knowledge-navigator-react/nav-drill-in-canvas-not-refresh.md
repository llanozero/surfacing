# 钻入子图后画布未刷新问题

## 问题描述

在导航画布中点击子图节点的"钻入"按钮后，画布仍显示顶层（top）的旧数据，没有切换到子图的节点和边。面包屑导航虽然正确更新为钻入路径，但画布数据未跟随。

## 根因分析

### 钻入流程追踪

```
用户点击子图节点 → handleNodeClick() 选中节点
  → 点击"钻入"按钮 → handleDrillIn()
    → 保存 currentSelected (top 的图列表) 到 drillStore.snapshot
    → drillIn(targetId) → 更新 activeGraphId + push 钻入栈
    → setCurrentNode(entryId)
    → 但未设置画布的 selectedGraphIds！
```

钻入后：
- `inDrill = true`（钻入栈有数据）
- `activeGraphId = subGraphId`
- `selectedGraphIds` **仍是顶层图列表**（未变更）
- `canvasNodes` / `canvasEdges` **仍是顶层聚合数据**（未清除）

### 问题代码一：handleDrillIn 未设置 selectedGraphIds

**文件**: `src/components/views/NavView.tsx` 第 210-225 行

```typescript
const handleDrillIn = () => {
    // ...
    const currentSelected = useNavStore.getState().selectedGraphIds
    if (currentSelected.length > 0) {
      useDrillStore.getState().setSnapshot(currentSelected)   // ← 保存了快照
    }
    // 缺少: useNavStore.getState().setSelectedGraphs([targetId])

    drillIn(targetId, entryNodeId, currentNodeId, currentNodeLabel)
    setCurrentNode(entryId)
    toast(`已钻入「${currentNode.label}」`)
}
```

`handleDrillIn` 保存了顶层图列表快照（便于钻出后恢复），但没有将 `selectedGraphIds` 切换为子图 ID。导致画布数据源仍指向顶层聚合数据。

### 问题代码二：数据获取 useEffect 被 inDrill 守卫阻断

**文件**: `src/components/views/NavView.tsx` 第 70-91 行

```typescript
useEffect(() => {
    if (inDrill) return // ← 钻入时直接 return，不获取新数据！
    if (selectedGraphIds.length === 0) {
      setCanvasNodes([])
      setCanvasEdges([])
      return
    }
    let cancelled = false
    api.fetchCanvasData(selectedGraphIds).then((res) => {
      // ...设置 canvasNodes/canvasEdges...
    })
}, [selectedGraphIds.join(','), inDrill])
```

`inDrill` 为 `true` 时，`useEffect` 直接 return，即使 `selectedGraphIds` 因钻入而发生变化，也不会获取新数据。

### 问题代码三：hasCanvasData 依赖旧数据

```typescript
const hasCanvasData = inDrill || canvasNodes.length > 0  // ← 旧数据仍存在
```

由于 `canvasNodes` 保留了顶层数据，`hasCanvasData` 始终为 `true`，画布继续使用旧 `canvasNodes`/`canvasEdges` 渲染。

### 对比：钻出时正确恢复

```typescript
const handleDrillOut = () => {
    const popped = useGraphStore.getState().drillOut()
    if (popped) {
      setCurrentNode(popped.parentNodeId)
      const snapshot = useDrillStore.getState().snapshotSelectedGraphIds
      if (snapshot.length > 0) {
        useNavStore.getState().setSelectedGraphs(snapshot)  // ← 钻出时正确恢复
        useDrillStore.getState().setSnapshot([])
      }
    }
}
```

钻出时通过 `setSelectedGraphs(snapshot)` 恢复顶层图列表，触发 `useEffect` 重新获取数据。但钻入时缺少对应的 `setSelectedGraphs([subGraphId])`。

## 修复方案

### 改动一：handleDrillIn 设置子图 selectedGraphIds

```typescript
const handleDrillIn = () => {
    // ...
    const currentSelected = useNavStore.getState().selectedGraphIds
    if (currentSelected.length > 0) {
      useDrillStore.getState().setSnapshot(currentSelected)
    }

    // 切换到子图的画布数据
    useNavStore.getState().setSelectedGraphs([targetId])

    drillIn(targetId, entryNodeId, currentNode.id, currentNode.label)
    setCurrentNode(entryId)
    toast(`已钻入「${currentNode.label}」`)
}
```

### 改动二：移除 useEffect 中的 inDrill 守卫

当 `selectedGraphIds` 变化时，即使在钻入模式中也应该获取数据。移除 `inDrill` 守卫不会引入副作用，因为：
- 钻入模式下 `GraphMultiSelect` 已隐藏，用户无法变更选择
- `selectedGraphIds` 仅在钻入/钻出时变化
- 钻入后浏览子图内节点，`selectedGraphIds` 不变，effect 不会重复触发

```typescript
useEffect(() => {
    // 移除: if (inDrill) return
    if (selectedGraphIds.length === 0) {
      setCanvasNodes([])
      setCanvasEdges([])
      return
    }
    // 继续获取画布数据...
}, [selectedGraphIds.join(',')])
```

### 数据流修复后

```
钻入前:
  selectedGraphIds = ['g1', 'g2']
  canvasNodes = [g1+g2 所有节点]
  canvasEdges = [g1+g2 所有边]
  面包屑: top

钻入时 (handleDrillIn):
  ① 保存 snapshot = ['g1', 'g2']
  ② setSelectedGraphs(['g2'])         ← 新增
  ③ drillIn('g2', 'entry-node', ...)
  ④ setCurrentNode('entry-node')

钻入后:
  selectedGraphIds = ['g2']
  inDrill = true
  → useEffect 触发 fetchCanvasData(['g2'])
    → canvasNodes = [g2 的节点]
    → canvasEdges = [g2 的边]
  → 画布渲染子图数据
  面包屑: top / g2 数学基础 / entry-node
```

## 测试验证

1. 选择多个图展示顶层 → 展示聚合数据
2. 点击子图节点 → 点击"钻入"按钮
3. 画布应切换为子图的节点和边
4. 面包屑应显示 `top / 子图名`
5. 当前节点应为子图的入口节点
6. 钻出后画布应恢复顶层聚合数据
