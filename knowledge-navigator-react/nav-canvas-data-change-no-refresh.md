# 画布取消勾选后未刷新问题

## 问题描述

在导航画布多图选择面板中，取消勾选某个导航图后，画布仍然显示旧数据，没有刷新。

## 根因分析

### 数据流

```
GraphMultiSelect (取消勾选)
  → navStore.setSelectedGraphs()
    → NavView 重新渲染
      → useEffect 触发 fetchCanvasData()
        → setCanvasNodes/setCanvasEdges (状态更新)
          → NavView 再次渲染, 传新数据给 useNavCanvas
            → useNavCanvas 收到新数据, 但 D3 不更新 ← 问题在这里
```

### 问题代码

**文件**: `src/hooks/useNavCanvas.ts`

#### `overviewBuiltRef` 永久守卫

```typescript
// 第 140-153 行
const overviewBuiltRef = useRef(false)

const buildOverview = useCallback(() => {
  // ...
  if (overviewBuiltRef.current) return  // ← 首次构建后永远为 true
  overviewBuiltRef.current = true       // ← 仅首次设为 true，永不重置
  // ... 创建 D3 节点/边/仿真 ...
}, [containerRef])
```

`buildOverview` 用 `overviewBuiltRef` 确保 D3 力导向图只构建一次。当画布数据变化时（取消勾选图导致 `allNodes`/`allEdges` 变化），该 ref 仍为 `true`，因此 `buildOverview` 直接 return，D3 仿真保留旧节点。

#### 模式切换 useEffect 的条件守卫

```typescript
// 第 418-427 行
useEffect(() => {
  overviewGRef.current?.style('display', mode === 'overview' ? 'inline' : 'none')
  stationGRef.current?.style('display', mode === 'station' ? 'inline' : 'none')
  if (mode === 'overview') {
    if (!overviewBuiltRef.current) buildOverview()  // ← overviewBuiltRef 永不为 false
  } else {
    renderStation()
  }
}, [mode, data.allNodes?.length, data.allEdges?.length, buildOverview, renderStation])
```

虽然 `data.allNodes?.length` 在 deps 中，但 `overviewBuiltRef.current` 永远是 `true`，所以 `buildOverview()` 永远不会再被调用。

#### 对比：逐站模式已正确处理

`renderStation` 每次执行都先清空再重建：

```typescript
const renderStation = useCallback(() => {
  // ...
  stationG.selectAll('*').remove()  // ← 每次都清除旧元素
  // ... 重新创建所有元素 ...
}, [containerRef])
```

因此逐站模式可以正常响应数据变化。

### D3 仿真创建的元素

`buildOverview` 执行时，用 `d.allNodes` 和 `d.allEdges` 创建：

- `linkSel`: SVG path 元素（边）
- `nodeSel`: SVG g 元素（节点）
- `sim`: D3 力仿真（绑定节点数据和边数据）

当新数据传入后：
- `dataRef.current` 已更新为新数据
- 但 D3 仿真中的节点和边仍是旧的
- SVG 元素仍是旧的
- 画布显示旧数据 → "残留数据"

## 修复方案

在 `useNavCanvas` 中添加数据版本追踪，当核心数据变化时重置 `overviewBuiltRef` 并清除旧元素，使 D3 可以重建。

### 关键改动

在模式切换 `useEffect` 之前增加数据版本检测：

```typescript
// 数据版本追踪 ref
const overviewDataVersionRef = useRef('')

// 核心数据变化时重置重建标志 + 清除旧元素
useEffect(() => {
  if (mode !== 'overview') return
  const d = dataRef.current
  const key = `${d.allNodes?.length ?? 0}:${d.allEdges?.length ?? 0}`
  if (overviewDataVersionRef.current && overviewDataVersionRef.current !== key) {
    overviewGRef.current?.selectAll('*').remove()
    overviewBuiltRef.current = false
  }
  overviewDataVersionRef.current = key
}, [mode, data.allNodes?.length, data.allEdges?.length])
```

当 `data.allNodes?.length` 或 `data.allEdges?.length` 发生变化时：
1. 清除 `overviewG` 下的所有旧 D3 元素
2. 重置 `overviewBuiltRef.current = false`
3. 后续模式切换 `useEffect` 检测到 `!overviewBuiltRef.current`，调用 `buildOverview()` 用新数据重建

### 影响范围

- 仅影响 D3 全览视图的构建逻辑
- 首次挂载行为不变（`overviewDataVersionRef` 首次为空字符串，不触发重置）
- 逐站模式不受影响（已有清除逻辑）
- 缩放、高亮等样式更新不受影响

## 测试验证

1. 选择两个以上导航图 → 画布展示聚合数据
2. 取消勾选其中一个图 → 画布刷新，仅显示剩余图的数据
3. 全选/全取消切换 → 画布正确刷新
4. 钻入/钻出 → 画布正确切换
5. 逐站模式 → 数据跟随选中节点正确变化
