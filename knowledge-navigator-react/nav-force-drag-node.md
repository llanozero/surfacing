# D3 力导向图：节点拖拽功能

## 功能描述

D3 力导向全览视图中，长按节点可拖拽该节点移动，其他节点受力学约束自动调整位置。

### 现有行为

| 交互 | 当前行为 | 保持不变 |
|------|---------|---------|
| 画布拖拽 (zoom/pan) | 在画布空白处拖拽平移/缩放整个导航图 | ✅ |
| 节点点击 | 点击节点选中，更新面板 | ✅ |
| **节点拖拽 (新增)** | **长按节点拖拽移动，其他节点受力学约束跟随位移** | **新增** |

---

## 实现方案

### 使用技术

- `d3.drag<SVGGElement, SimNode>()` — D3 原生拖拽行为
- `sim.alphaTarget(0.3)` — 拖拽时提高仿真活跃度，使其他节点响应用户操作
- `d.fx / d.fy` — 固定被拖拽节点的位置，仿真不再自动移动它

### 关键设计

#### 1. zoom 与 drag 共存

`d3.zoom` 绑定在 SVG 父元素上（画布拖拽），`d3.drag` 绑定在 `<g>` 子元素上（节点拖拽）。拖拽节点时通过 `event.sourceEvent.stopPropagation()` 阻止 mousedown 事件冒泡到 SVG，避免 zoom 行为同时激活。

```
mousedown in 空白区域 → zoom 行为 → 画布平移
mousedown on 节点     → drag 行为 → 节点拖拽（stopPropagation 阻止 zoom）
```

#### 2. 点击与拖拽共存

`d3.drag` 自动抑制拖拽过程中的 `click` 事件。节点上同时绑定了 `click` 和 `drag` 两个交互：

| 操作 | 触发事件 | 行为 |
|------|---------|------|
| 点击（按下+释放，无移动） | `click` | 选中节点，更新面板 |
| 拖拽（按下+移动+释放） | `drag:start` → `drag` → `drag:end` | 移动节点，其他节点受力学约束位移 |

#### 3. 拖拽力学约束

- `drag:start`：调用 `sim.alphaTarget(0.3).restart()` 提高仿真活跃度，`d.fx/d.fy` 固定被拖拽节点
- `drag`：持续更新 `d.fx/d.fy` 为用户鼠标位置
- `drag:end`：调用 `sim.alphaTarget(0)` 降低仿真活跃度，但**不释放** `fx/fy`（节点停留在拖拽终点位置）

#### 4. 光标样式

- 默认：`cursor: grab`（抓手）
- 拖拽中：`cursor: grabbing`（抓取中）

---

## 代码改动

**文件**: `src/hooks/useNavCanvas.ts` — `buildOverview` 函数

### 改动前

```typescript
const nodeSel = overviewG
  .append('g')
  .selectAll('g')
  .data(nodes)
  .enter()
  .append('g')
  .style('cursor', 'pointer')
  .on('click', (_e, n) => optionsRef.current.onNodeClick?.(n.ref))
// ... 仿真设置 ...
simRef.current = sim
nodeSelRef.current = nodeSel
applyNodeStyles()
```

### 改动后

```typescript
const nodeSel = overviewG
  .append('g')
  .selectAll('g')
  .data(nodes)
  .enter()
  .append('g')
  .style('cursor', 'grab')  // ← 改为 grab 提示可拖拽
// ... 仿真设置 ...
simRef.current = sim
nodeSelRef.current = nodeSel

// ── 节点拖拽（d3.drag）：长按拖拽单个节点，其他节点受力学约束位移 ──
const dragHandler = d3.drag<SVGGElement, SimNode>()
  .on('start', function (event, d) {
    // 阻止事件冒泡到 SVG 的 zoom 行为，避免画布平移和节点拖拽同时触发
    event.sourceEvent.stopPropagation()
    if (!event.active) sim.alphaTarget(0.3).restart()
    // 固定该节点的位置（fx/fy），仿真不再自动移动它
    d.fx = d.x
    d.fy = d.y
    // 光标样式切换为抓取中
    d3.select(this).style('cursor', 'grabbing')
  })
  .on('drag', (event, d) => {
    d.fx = event.x
    d.fy = event.y
  })
  .on('end', function (event, _d) {
    if (!event.active) sim.alphaTarget(0)
    // 保持 fx/fy 不释放，节点停留在拖拽终点位置
    d3.select(this).style('cursor', 'grab')
  })
nodeSel.call(dragHandler)

// 点击选中节点（d3.drag 自动抑制拖拽过程中的 click 事件）
nodeSel.on('click', (_e, n) => {
  optionsRef.current.onNodeClick?.(n.ref)
})

applyNodeStyles()
```

---

## 力学效果说明

拖拽一个节点时，力仿真会实时重新计算：

```
用户拖拽节点 A ════════════════════════════════╗
  ↓ d.fx/d.fy 持续更新                        ║
  ↓ sim.alphaTarget(0.3) 提高活跃度           ║
  ↓ 仿真 tick 反复执行                        ║
  ↓                                           ║
  force('link'): A 的连线拉拽相邻节点          ║
  force('charge'): 节点间斥力推动不相邻节点     ║
  force('collide'): 碰撞检测防止重叠            ║
  ↓                                           ║
其他节点实时调整位置 ←═════════════════════════╝
```

停止拖拽后：

```
sim.alphaTarget(0) → 仿真逐渐冷却
fx/fy 保持 → 被拖拽节点不弹回
其他节点在剩余 alpha 下继续微调 → 最终稳定在新的布局
```

---

## 验证步骤

1. 打开导航全览视图，加载至少 5 个节点的导航图
2. 在画布空白处拖拽 → 画布整体平移/缩放（原有行为正常）
3. 点击一个节点 → 节点被选中，面板更新（原有行为正常）
4. 长按一个节点并拖拽 → 节点跟随鼠标移动，其他受力学约束的节点同步位移
5. 拖拽过程中可观察到连线拉伸/压缩，节点间斥力和碰撞约束生效
6. 释放拖拽 → 节点停留在终点位置不弹回，其他节点逐渐稳定

---

## 影响范围

- 仅影响 D3 全览视图（`mode === 'overview'`）
- 逐站视图（`mode === 'station'`）不受影响
- 画布 zoom/pan 不受影响
- 节点点击选中不受影响

---

## 编译验证

```
npx tsc --noEmit
→ exit code 0，编译零错误
```
