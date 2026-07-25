# 导航画布节点交互增强 — 功能规范

## 版本

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| 1.0 | 2026-07-25 | — | 初始规范：全览视图选中节点样式 + 逐站视图单击更新当前节点 |

---

## 一、概述

### 1.1 目标

增强 NavView 中两种模式（全览/逐站）的节点点击交互行为，解决当前两个问题：

1. **全览视图**：点击节点仅打开下拉面板，节点本身无视觉反馈，无法区分"当前选中的节点"与"途经点节点"
2. **逐站视图**：点击节点同样只打开面板，中心节点不会更新为新选节点，相关连线也不刷新

### 1.2 当前问题对照

| 问题 | 当前行为 | 期望行为 |
|------|----------|----------|
| 全览：选中节点样式 | 仅打开面板，画布上无任何高亮 | 选中节点应有独立高亮样式，区别于普通节点和途经点节点 |
| 全览：选中与途经点区分 | 途经点黄色描边，选中节点无标注 | 三种视觉状态：普通 / 途经点 / 当前选中 |
| 逐站：点击更新中心节点 | 打开面板，center 保持不变 | 点击节点后 → 更新为新的中心节点 + 重绘连线 |
| 逐站：节点点击行为 | `handleNodeClick` 仅调用 `setPanelNode` | 额外调用 `setCurrentNode` 切换当前节点 |

---

## 二、全览视图 — 三种节点视觉状态

### 2.1 状态定义

全览视图中的每个导航节点应具有以下三种视觉状态之一：

| 状态 | 含义 | 视觉样式 | 优先级 |
|------|------|----------|--------|
| **普通** | 未被选中，也不是途经点 | 现有样式：青色(ACCENT2)描边，深色填充 | — |
| **途经点** | 已被用户添加为途经点 | 现有样式：黄色(WAYPOINT)描边 4px，黄色光晕 | 覆盖普通 |
| **当前选中** | 用户最近单击选中的节点 | **新增**：亮青色(ACCENT)描边 4px，光晕放大 | **覆盖途经点** |

三种样式的优先级：**当前选中 > 途经点 > 普通**。即若某节点既是途经点又是当前选中，按当前选中样式渲染。

### 2.2 视觉样式详细定义

```
普通节点:
  ┌──────────────────┐
  │  ⚪ 青色描边 2.5px  │  stroke: #14b8a6 (ACCENT2)
  │  深色填充 #1e293b    │  fill: #1e293b
  │  淡色光晕 r=18      │  halo fill: #14b8a6, opacity 0.25
  └──────────────────┘

途经点节点 (现有):
  ┌──────────────────┐
  │  ⚪ 黄色描边 4px    │  stroke: #ffd230 (WAYPOINT)
  │  深色填充 #1e293b    │  fill: #1e293b
  │  黄色光晕 r=18      │  halo fill: #ffd230, opacity 0.4
  └──────────────────┘

当前选中节点 (新增):
  ┌──────────────────┐
  │  ⚪ 亮青描边 4px    │  stroke: #06b6d4 (ACCENT)
  │  亮色填充 #0e2a33    │  fill: #0e2a33 (较亮背景)
  │  亮青光晕 r=24      │  halo fill: #06b6d4, opacity 0.3
  │  外圈脉冲环 r=36    │  ★ 新增: 脉冲动画环
  └──────────────────┘
```

### 2.3 脉冲环动画

当前选中的节点外围有一个缓慢呼吸的脉冲环，用于吸引视觉焦点：

```
┌──────────────────────────────────┐
│            ↗ 脉冲环              │
│   ╭──────────────────╮          │
│   │   ╭────────────╮  │↕ r=36  │
│   │   │  ⚪ 节点     │  │        │
│   │   ╰────────────╯  │        │
│   ╰──────────────────╯          │
│           动画: opacity 0.15↔0.4 │
│                 周期 2s          │
└──────────────────────────────────┘
```

CSS/JS 动画定义：

```typescript
// 脉冲环配置
const PULSE_R = 36
const PULSE_DURATION = 2000  // ms

// D3 动画实现
function applyPulseAnimation(sel: d3.Selection) {
  const ring = sel.append('circle')
    .attr('r', PULSE_R)
    .attr('fill', 'none')
    .attr('stroke', ACCENT)
    .attr('stroke-width', 1.5)
    .attr('opacity', 0.3)

  function pulse() {
    ring.transition()
      .duration(PULSE_DURATION / 2)
      .attr('r', PULSE_R + 8)
      .attr('opacity', 0.15)
      .transition()
      .duration(PULSE_DURATION / 2)
      .attr('r', PULSE_R)
      .attr('opacity', 0.3)
      .on('end', pulse)  // 循环
  }
  pulse()
}
```

### 2.4 选中节点数据传递

向 `NavCanvasData` 新增 `selectedNodeId` 字段，用于全览视图识别当前选中的节点：

```typescript
interface NavCanvasData {
  // ... 现有字段
  allNodes?: NavNode[]
  allEdges?: GraphEdge[]
  currentNode?: NavNode | null
  prevNodes?: NextNodeItem[]
  nextNodes?: NextNodeItem[]
  waypointIds?: Set<string>
  selectedNodeId?: string | null   // ← 新增: 全览视图中当前选中节点的 id
}
```

### 2.5 渲染逻辑变更

`buildOverview` 中节点样式渲染逻辑更新为三态判断：

```typescript
// 伪代码: 每次途经点高亮或选中变化时重新应用样式
function applyNodeStyles() {
  const sel = nodeSelRef.current
  if (!sel) return
  const waypointIds = dataRef.current.waypointIds ?? new Set()
  const selectedId = dataRef.current.selectedNodeId

  // body 圆圈
  sel.select('circle.nc-body')
    .attr('fill', (n) => (n.id === selectedId ? '#0e2a33' : '#1e293b'))
    .attr('stroke', (n) => {
      if (n.id === selectedId) return ACCENT
      if (waypointIds.has(n.id)) return WAYPOINT
      return ACCENT2
    })
    .attr('stroke-width', (n) => {
      if (n.id === selectedId || waypointIds.has(n.id)) return 4
      return 2.5
    })

  // halo 光晕
  sel.select('circle.nc-halo')
    .attr('r', (n) => (n.id === selectedId ? 24 : 18))
    .attr('fill', (n) => {
      if (n.id === selectedId) return ACCENT
      if (waypointIds.has(n.id)) return WAYPOINT
      return ACCENT2
    })
    .attr('opacity', (n) => {
      if (n.id === selectedId) return 0.3
      if (waypointIds.has(n.id)) return 0.4
      return 0.25
    })

  // 脉冲环: 选中节点添加，非选中节点移除
  sel.each(function (n) {
    const g = d3.select(this)
    const existing = g.select<SVGCircleElement>('circle.nc-pulse')
    if (n.id === selectedId) {
      if (existing.empty()) applyPulseAnimation(g)
    } else {
      existing.remove()
    }
  })
}
```

---

## 三、逐站视图 — 单击更新当前节点

### 3.1 行为变更

当前 `handleNodeClick` 仅打开面板。变更后，在逐站模式下单击节点应额外更新当前节点：

```
逐站模式点击前:
  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
  │  数学基础     │    │  机器学习基础  │    │  监督学习    │
  │  (前驱)      │    │  ● 当前中心   │    │  (后继)      │
  └──────────────┘    └──────────────┘    └──────────────┘

用户点击「监督学习」节点
        │
        ▼

逐站模式点击后:
  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
  │  机器学习基础  │    │  监督学习    │    │  神经网络基础 │
  │  (前驱)      │    │  ● 当前中心   │    │  (后继)      │
  └──────────────┘    └──────────────┘    └──────────────┘
  (连线、权重全部重算重绘)
```

### 3.2 NavView 点击处理变更

```typescript
// NavView.tsx — handleNodeClick 根据当前模式分流

const setCurrentNode = useNavStore((s) => s.setCurrentNode)

const handleNodeClick = (node: NavNode) => {
  // 始终打开面板（现有行为）
  setPanelNode(node)

  // 逐站模式: 额外更新当前节点 → 触发重绘
  if (mode === 'station') {
    setCurrentNode(node.id)
  }
}
```

### 3.3 逐站重绘现有机制

当前 `useNavCanvas` 已通过以下 useEffect 监听数据变化并重绘：

```typescript
useEffect(() => {
  if (mode === 'station') renderStation()
}, [mode, data.currentNode, data.prevNodes, data.nextNodes, renderStation])
```

变更 `currentNodeId` 后，NavView 重新渲染，传入 `useNavCanvas` 的 `data.currentNode` 变为新节点，`data.prevNodes` 和 `data.nextNodes` 也对应更新，逐站视图自动重绘。

**无需修改 useNavCanvas，只需保证 `handleNodeClick` 调用 `setCurrentNode` 即可。**

### 3.4 面板联动

逐站模式下点击节点切换中心后：
1. 画布重绘：新节点居中，前驱/后继及相关连线更新
2. DropDownPanel 保持打开状态，内容更新为新节点的信息（现有行为，`setPanelNode` 已处理）
3. 如果新节点已在途径点列表中，面板显示"已添加"状态
4. 顶部 `subtitle` 中的"当前节点"文字同步更新（现有行为，NavView 从 store 读取）

---

## 四、数据流

### 4.1 selectedNodeId 归属

新增的 `selectedNodeId` 字段存放于 `navStore` 中，与 `currentNodeId` 分开管理：

```typescript
interface NavStore {
  // ... 现有字段
  currentNodeId: string       // 导航视图的"锚点"节点（逐站中心 + 全览选中高亮基准）
  selectedNodeId: string | null  // ← 新增: 全览视图中当前点击选中的节点 id

  // ... 现有方法
  setCurrentNode: (nodeId: string) => void   // 更新 currentNodeId
  setSelectedNode: (nodeId: string | null) => void  // ← 新增: 全览选中
}
```

两个字段的分工：

| 字段 | 用途 | 全览模式 | 逐站模式 |
|------|------|----------|----------|
| `currentNodeId` | 导航锚点 | 影响逐站中心，全览不直接使用 | 中心节点，prev/next 基于此计算 |
| `selectedNodeId` | 全览选中高亮 | 控制节点高亮样式 | 不使用 |

### 4.2 全览点击 → 选中

```typescript
// NavView.tsx 中 handleNodeClick 增强

const handleNodeClick = (node: NavNode) => {
  setPanelNode(node)

  if (mode === 'station') {
    setCurrentNode(node.id)
  } else {
    // 全览模式: 更新选中高亮
    setSelectedNode(node.id)
  }
}
```

### 4.3 全览高亮重绘

向 `useNavCanvas` 传入 `selectedNodeId`，通过新的 useEffect 触发样式刷新：

```typescript
// NavView.tsx — 传入 data
const selectedNodeId = useNavStore((s) => s.selectedNodeId)

const { zoomIn, zoomOut, zoomReset } = useNavCanvas(
  canvasRef,
  mode,
  {
    allNodes: allNavNodes,
    allEdges,
    currentNode,
    prevNodes: currentNode ? getPrevNodes(currentNode.id) : [],
    nextNodes: currentNode ? getNextNodes(currentNode.id) : [],
    waypointIds: new Set(waypoints.map((w) => w.id)),
    selectedNodeId,        // ← 传入
  },
  { onNodeClick: handleNodeClick },
)
```

```typescript
// useNavCanvas — 新增选中变化监听
useEffect(() => {
  applyNodeStyles()   // 三态样式更新
}, [data.selectedNodeId, data.waypointIds])
```

### 4.4 选中节点清除时机

| 场景 | 行为 |
|------|------|
| 切换到逐站模式 | 不清除 `selectedNodeId`，但全览高亮在逐站模式下不可见 |
| 切换回全览模式 | 若 `selectedNodeId` 仍有值，恢复高亮 |
| 清空搜索结果 | 不清除 |
| 进入规划/浏览视图再返回 | 保持 `selectedNodeId` 不变 |

---

## 五、NavView 代码变更摘要

### 5.1 NavView.tsx 变更

```typescript
// NavView.tsx — 新增选中状态 + 点击分流

const setCurrentNode = useNavStore((s) => s.setCurrentNode)
const setSelectedNode = useNavStore((s) => s.setSelectedNode)
const selectedNodeId = useNavStore((s) => s.selectedNodeId)

const handleNodeClick = (node: NavNode) => {
  setPanelNode(node)
  if (mode === 'station') {
    setCurrentNode(node.id)
  } else {
    setSelectedNode(node.id)
  }
}

// 传入 selectedNodeId
const { zoomIn, zoomOut, zoomReset } = useNavCanvas(
  canvasRef,
  mode,
  {
    allNodes: allNavNodes,
    allEdges,
    currentNode,
    prevNodes: currentNode ? getPrevNodes(currentNode.id) : [],
    nextNodes: currentNode ? getNextNodes(currentNode.id) : [],
    waypointIds: new Set(waypoints.map((w) => w.id)),
    selectedNodeId,            // ← 新增
  },
  { onNodeClick: handleNodeClick },
)
```

### 5.2 navStore.ts 变更

```typescript
interface NavStore {
  // ... 现有字段
  selectedNodeId: string | null

  // ... 现有方法
  setSelectedNode: (nodeId: string | null) => void
}

// store 实现
export const useNavStore = create<NavStore>((set) => ({
  // ... 现有
  selectedNodeId: null,

  setSelectedNode: (nodeId) => set({ selectedNodeId: nodeId }),
  // ...
}))
```

### 5.3 useNavCanvas.ts 变更

```typescript
export interface NavCanvasData {
  // ... 现有
  allNodes?: NavNode[]
  allEdges?: GraphEdge[]
  currentNode?: NavNode | null
  prevNodes?: NextNodeItem[]
  nextNodes?: NextNodeItem[]
  waypointIds?: Set<string>
  selectedNodeId?: string | null   // ← 新增
}

// 新增 effect: 选中节点变化时刷新全览样式
useEffect(() => {
  applyNodeStyles()
}, [data.selectedNodeId, data.waypointIds, applyNodeStyles])
```

新增 `applyNodeStyles` 函数（三态样式 + 脉冲环），取代原有的 `applyWaypointHighlight`。

---

## 六、验收标准

- [ ] 全览视图中点击节点，该节点外圈显示亮青色(ACCENT)描边 + 放大光晕
- [ ] 全览视图中选中节点有脉冲环动画（缓慢呼吸 2s 周期）
- [ ] 全览视图中途经点节点保持黄色描边，与选中节点的亮青色可区分
- [ ] 全览视图中若节点既是途经点又是选中，按选中样式渲染（覆盖途经点）
- [ ] 全览视图中点击另一个节点，高亮转移，原节点恢复普通/途经点样式
- [ ] 逐站视图中点击前驱或后继节点，该节点变为新的中心节点
- [ ] 逐站视图切换中心后，前驱/后继列表及相关连线刷新
- [ ] 逐站视图切换中心后，下拉面板内容更新为新节点信息
- [ ] 逐站视图切换中心后，顶部"当前节点"文字同步更新
- [ ] 全览与逐站模式之间切换，选中状态保持（逐站模式下不可见）
- [ ] 所有 TypeScript 类型定义正确，编译零错误

---

## 七、与现有功能的兼容性

| 现有功能 | 兼容性 | 说明 |
|----------|--------|------|
| 途经点黄色高亮 | ✅ 不变 | 现有样式保留，选中时被覆盖 |
| 下拉面板点击打开 | ✅ 不变 | 始终触发 |
| 全览力导向图布局 | ✅ 不变 | 仅样式刷新，不重置仿真 |
| 逐站 DAG 布局 | ✅ 不变 | 触发重绘，布局逻辑不变 |
| 途径点序列 | ✅ 不变 | 不影响 waypoints 增删改 |
| ZoomControls | ✅ 不变 | 不影响缩放 |
| 面板三段停靠 | ✅ 不变 | 不影响面板拖拽 |

---

## 八、边界情况

| 场景 | 行为 |
|------|------|
| 全览中选中已标记为途经点的节点 | 按选中样式渲染（亮青覆盖黄色），松开选中后恢复黄色 |
| 选中节点后切换到逐站模式再切回 | 选中的高亮保持，切回时恢复显示 |
| 选中节点后清空所有途经点 | 不影响选中高亮 |
| 逐站中点击当前中心节点 | 无效果（setCurrentNode 传入相同 id，navStore 不触发变更） |
| 选中节点后节点因搜索/数据变更消失 | 自动清空 selectedNodeId |
