# 认知导航 — 画布交互设计分析

## 一、视图架构变更

原版设计为"三层画布视图"：全局全览（D3 力导向图）→ 路径选择（DAG 流）→ 内容浏览。新版重构为：

| 原版 | React 版 | 画布技术 |
|------|----------|---------|
| 全局全览（力导向图 + 认知卡片） | **搜索视图**（文本搜索 → 匹配卡片 → 绑定节点查询） | 无画布，纯列表渲染 |
| 路径选择（DAG 逐站流） | **导航视图 - 全览模式**（力导向图） | D3-force |
| — | **导航视图 - 逐站模式**（DAG 流） | D3 手动布局 |
| 内容浏览（卡片堆叠） | **浏览视图**（按途径点顺序浏览） | 无画布，CSS 堆叠 |

核心变化：
- 原全览视图的**搜索匹配功能**被剥离为独立 SearchView，使用纯列表渲染
- 原全览视图的**力导向图**与**DAG 流**合并到 NavView，通过全览/逐站双模式切换
- 新增**多途径点路线规划**：用户可在 NavView 中点击多个节点组成途径点序列

---

## 二、技术方案

### 2.1 NavCanvas — 统一画布（合并力导向 + DAG）

使用 **`useNavCanvas`** 单一 Hook 管理两种渲染模式，内部维护两个独立的 D3 实例：

```
useNavCanvas(containerRef, mode, data, options)
                          │
              ┌───────────┴───────────┐
              │                       │
        mode='overview'          mode='station'
              │                       │
    ┌─────────────────┐     ┌─────────────────┐
    │ D3-force        │     │ D3 手动坐标布局  │
    │ forceSimulation │     │ 3 层固定流      │
    │ forceLink       │     │ prev → curr    │
    │ forceManyBody   │     │       → next   │
    │ forceCenter     │     │ 贝塞尔曲线      │
    │ forceCollide    │     │ transition 动画 │
    │ d3-zoom         │     │                 │
    │ 箭头 marker     │     │ 权重标签 (w:)   │
    │ 途径点亮高      │     │                 │
    └─────────────────┘     └─────────────────┘
              │                       │
              └───────────┬───────────┘
                          │
                  切换 mode 时切换 SVG group
                  不销毁另一实例
```

**技术选型对比**：

| 方案 | 力导向图 | DAG 流 | 包体积 | 定制度 |
|------|---------|--------|--------|-------|
| **D3 模块化（推荐）** | d3-force | 手动布局 + d3-shape | ~50KB gzip | 极高 |
| Cytoscape.js | 原生 | 原生 | ~200KB gzip | 中 |
| G6 (AntV) | 原生 | 原生 | ~150KB gzip | 中 |

**推荐 D3 模块化**的理由：
- 两种模式渲染逻辑差异大（力模拟 vs 固定坐标），统一库反而需要适配层
- D3 模块化可按需引入（仅需 `d3-force`、`d3-selection`、`d3-shape`、`d3-zoom`、`d3-transition`）
- 与 React 通过 Hook 解耦，D3 负责 DOM 操作，React 负责生命周期

### 2.2 搜索视图（SearchView）— 纯列表匹配

无需画布类库。搜索匹配逻辑：

```
输入文本 → debounce 300ms
    ↓
在 allCards 中模糊匹配:
  card.title.includes(query) ||
  card.description.includes(query) ||
  card.corpus.some(c => c.includes(query))
    ↓
匹配结果排序（匹配字段优先级: title > description > corpus）
    ↓
渲染 CardMatchItem 列表（icon + title + 高亮片段 + 匹配度）
    ↓
用户选中卡片 → 查询 card.bound_nodes → 渲染 BoundNodeItem 列表
    ↓
用户选中导航节点 → 点击「进入导航」→ navStore.init(nodeId)
```

### 2.3 树形管理（TreeView）— 原生 DOM

保持原有方案，无变化。

---

## 三、地图导航 vs 认知导航 — 设计异同分析

### 异同对比表

| 维度 | 地图导航 | 认知导航 | 设计启示 |
|------|---------|---------|---------|
| **空间模型** | 物理二维/三维空间，经纬度坐标 | 抽象概念空间，节点通过语义关联 | 前者可用绝对坐标，后者必须用关系网络表达 |
| **路径特性** | 最短路径优先，通常单一起终点 | 多途径点序列，受权重影响，可中途增删 | 需要途径点条（WaypointsBar），支持增删重排 |
| **方向性** | 道路有方向，全局拓扑基本已知 | 节点间关系有向，可动态演化 | 需支持循环路径和动态边权重更新 |
| **缩放层级** | 城市级→街区级→道路级 | 搜索匹配→全览全图→逐站导航→卡片浏览 | 四层递进：搜索→全览（力导向）→逐站（DAG）→内容 |
| **导航模式** | 路线规划→turn-by-turn | 搜索→选点→添加途径点→顺序浏览 | 浏览模式更接近"沿途径点序列游览" |
| **定位方式** | GPS 绝对定位 | 文本搜索模糊匹配→认知卡片定位 | 搜索是认知导航的"GPS" |
| **POI** | 餐厅、加油站等地标 | 认知卡片（标题+描述+语料库） | 认知卡片 = 知识地标 |
| **途经点** | 支持添加途经点（加油站/休息区） | 支持添加多个导航节点为途径点 | **新增**：WaypointsBar 类比地图途经点条 |
| **终点抵达** | 到达目的地 | 浏览完所有途径点的绑定卡片 | "下一站"按钮类比地图的"继续导航" |

### 核心差异

1. **地图是静态拓扑，认知图是动态拓扑**
   - 地图的路径基本不变，而认知导航中用户浏览行为会生成新的权重边
   - 前端需要支持运行时动态增删节点和边

2. **地图导航强调"到达"，认知导航强调"探索"**
   - 地图的结束是到达目的地，认知的结束可能是"发现了一个新概念"
   - 多途径点设计允许用户自由组合探索路径

3. **地图有统一的底图坐标系，认知图没有**
   - 力导向布局每次初始化的节点位置不同
   - 全览/逐站双模式提供了"全局视图"和"局部视图"两种视角

### 适合的前端效果

| 效果 | 技术 | 适用场景 |
|------|------|---------|
| **力导向弹性动画** | d3-force + d3-transition | 全览模式节点拖拽、搜索聚焦 |
| **路径流动粒子** | SVG stroke-dashoffset 动画 | 逐站模式表示"行进方向" |
| **卡片堆叠过渡** | CSS transform + cubic-bezier | 内容浏览的上下滑动 |
| **节点脉冲高亮** | SVG filter + animation | 途径点标记和节点选中 |
| **边权重渐变** | SVG gradient along path | 展示预设权重和浏览权重的混合比例 |
| **途径点 Chip 滚动** | CSS overflow-x:auto + snap | 途径点序列的横向滚动 |
| **树节点展开折叠** | CSS height transition | 树形管理目录展开 |

---

## 四、D3 实现路径

### 4.1 useNavCanvas — 统一 Hook

```
输入：
  containerRef    → SVG 挂载的 div 容器
  mode            → 'overview' | 'station'
  data:
    allNodes[]    → 所有导航节点（全览模式用）
    allEdges[]    → 所有有向边（全览模式用）
    currentNode   → 当前节点（逐站模式用）
    prevNodes[]   → 前驱节点（逐站模式用）
    nextNodes[]   → 后继节点（逐站模式用）
    waypointIds   → 途径点 id 集合（高亮用）
  options:
    onNodeClick   → 节点点击回调
    onSelectNext  → 逐站模式点击后继回调

输出：
  { zoomIn, zoomOut, zoomReset }

内部机制：
  useEffect → 挂载时创建 SVG + defs
    ├── mode='overview' → 创建 forceSimulation group
    │   ├── d3.forceSimulation(nodes)
    │   │   .force('link', forceLink(edges))
    │   │   .force('charge', forceManyBody(-450))
    │   │   .force('center', forceCenter(w/2,h/2))
    │   │   .force('collide', forceCollide(30))
    │   │   .on('tick', renderLinks + renderNodes)
    │   ├── 预热 300 tick
    │   └── d3-zoom 绑定到 SVG
    │
    ├── mode='station' → 创建 DAG group
    │   ├── 手动计算坐标 (topY, cy, botY)
    │   ├── prevNodes → 底部行
    │   ├── currentNode → 中间行（高亮 + glow 滤镜）
    │   └── nextNodes → 顶部行（带权重标签）
    │
    ├── waypointIds 变化 → 更新 overview 节点描边/填充
    └── useEffect 返回清理 → simulation.stop() + SVG 清空
```

### 4.2 途径点高亮逻辑（全览模式）

```
用户点击节点 → dropdown panel → "添加为途径点"
    ↓
navStore.addWaypoint(node)
    ↓
useNavCanvas 感知 waypointIds Set 变化
    ↓
d3.selectAll('.gnode circle')
  .attr('stroke', d => waypointIds.has(d.id) ? '#67e8f9' : '#14b8a6')
  .attr('stroke-width', d => waypointIds.has(d.id) ? 4 : 2.5)
```

### 4.3 逐站模式前后继计算

```
当前节点 = currentNode
    ↓
查询 currentNode.next_nodes → 按 preset_weight 降序排列
    ↓
渲染为顶部行（nextNodes），每个节点显示 w:0.75 权重标签
    ↓
查询所有节点的 next_nodes 中 target_id === currentNode.id → 渲染为底部行（prevNodes）
    ↓
连线: prev 连到 current（虚线），current 连到 next（实线）
```

---

## 五、推荐的库组合

| 模块 | 推荐库 | 包体积 |
|------|-------|--------|
| 力导向图（全览模式） | d3-force + d3-zoom + d3-selection | ~30KB gzip |
| DAG 流（逐站模式） | d3-shape + d3-selection（手动布局） | ~10KB gzip |
| 画布缩放 | d3-zoom | 已包含 |
| 动画过渡 | d3-transition | ~5KB gzip |
| 途径点序列 | 原生 React 组件（无库） | 0 |
| 卡片匹配搜索 | 原生 JS 模糊匹配（无库） | 0 |
| 树形管理 | 原生 DOM（无库） | 0 |
| 状态管理 | Zustand | ~2KB gzip |

**总新增依赖**：D3 模块按需引入约 ~50KB gzip + Zustand ~2KB gzip。

**注意**：不再需要 elkjs。逐站模式的 DAG 布局通过手动计算 3 层固定坐标实现（前驱 row → 当前 row → 后继 row），层级深度固定为 3，不需要通用 DAG 布局引擎。这大大减少了包体积和复杂度。

---

## 六、视觉设计方案

### 深色科技主题（保持与原版一致）

| Token | 值 | 用途 |
|-------|-----|------|
| `--bg` | `#0f172a` | 画布背景 |
| `--bg-card` | `#1e293b` | 下拉面板/节点卡片 |
| `--pr` | `#06b6d4` (cyan) | 主色：节点圆、选中态、按钮 |
| `--pr-h` | `#0891b2` | 主色 hover |
| `--tx` | `#e2e8f0` | 主文字 |
| `--mu` | `#94a3b8` | 辅助文字 |
| `--mu-dim` | `#64748b` | 权重标签 |

### 画布视觉元素

| 元素 | 全览模式 | 逐站模式 |
|------|---------|---------|
| 节点形状 | 圆形（r=24） | 圆形（current r=36, other r=28） |
| 节点颜色 | 描边 `#14b8a6`，填充 `#1e293b` | current 带 glow filter |
| 途径点高亮 | 描边 `#67e8f9`，加粗 4px | 不适用 |
| 边 | 贝塞尔弧线，粗细按权重 | 贝塞尔曲线，preset=实线 browse=虚线 |
| 背景 | 点网格 pattern（28x28） | 无背景 |
| 缩放 | 支持（0.4x ~ 3x） | 不支持（固定视口） |
