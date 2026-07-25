# React 版本迁移方案

## 一、技术选型

| 层 | 方案 | 理由 |
|----|------|------|
| 框架 | React 18 + TypeScript | 组件化、类型安全 |
| 构建 | Vite | 开发热更新、HMR 开箱即用 |
| 状态管理 | Zustand | 轻量、无 boilerplate、支持中间件 |
| 可视化 | D3.js v7 | 与现有版本一致 |
| 样式 | CSS Modules + CSS Variables | 按组件隔离，复用现有深色主题 token |
| 路由 | React Router (可选) | 若需 URL 持久化视图，否则用 state 切换 |

## 二、架构变更说明

原 index.html 中的 GlobalView（力导向全览图）与 NavView（DAG 逐站流）在新版中合并重构：

| 原版 | React 版 | 说明 |
|------|----------|------|
| GlobalView（全览力导向图） | SearchView（搜索视图） | 输入文本 → 匹配认知卡片 → 查询绑定的导航节点 → 选中节点进入导航 |
| NavView（DAG 逐站流） | NavView（统一导航视图） | 力导向全览 + DAG 逐站双模式，下拉面板"添加为途径点"，支持多途径点路线规划 |

类比：类似地图导航——搜索"咖啡馆"→列出匹配地点→选一个或多个作为途径点→顺序浏览。

## 三、项目目录结构

```
knowledge-navigator-react/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── public/
│   └── favicon.svg
└── src/
    ├── main.tsx                    # 入口，挂载 <App/>
    ├── App.tsx                     # 根组件：StatusBar + ViewRouter + TabBar
    ├── App.css                     # 全局样式 + CSS Variables
    │
    ├── store/
    │   ├── index.ts                # 统一导出
    │   ├── viewStore.ts            # activeView 切换 (search/nav/browse/tree)
    │   ├── searchStore.ts          # 搜索匹配 + 卡片/节点选中
    │   ├── panelStore.ts           # 下拉面板状态 (仅 NavView 内使用)
    │   ├── navStore.ts             # 导航模式切换 + 途径点序列 + D3 数据
    │   ├── browseStore.ts          # 卡片浏览 + 途径点进度
    │   └── treeStore.ts            # 树形管理
    │
    ├── data/
    │   ├── types.ts                # 所有数据模型 TypeScript 接口
    │   ├── allNavNodes.ts          # 全部导航节点 + 边数据（力导向图用）
    │   ├── cards.ts                # 认知卡片 + 浏览卡片数据
    │   └── treeData.ts             # 扁平树数据
    │
    ├── hooks/
    │   ├── useNavCanvas.ts         # 合并 D3 力导向 + DAG 流（单一 Hook）
    │   ├── useDragPanel.ts         # 下拉面板拖拽 Hook
    │   └── useCardSwipe.ts         # 卡片滑动 Hook
    │
    ├── components/
    │   ├── layout/
    │   │   ├── StatusBar.tsx        # 顶部状态栏
    │   │   ├── TabBar.tsx           # 底部标签栏
    │   │   └── TabButton.tsx        # 单个标签按钮
    │   │
    │   ├── shared/
    │   │   ├── SearchBar.tsx        # 搜索输入框
    │   │   ├── Toast.tsx            # 全局 Toast
    │   │   ├── Button.tsx           # btn-primary / btn-outline
    │   │   ├── BreadcrumbNav.tsx    # 面包屑导航
    │   │   └── Icon.tsx             # SVG 图标集合
    │   │
    │   ├── panel/
    │   │   ├── DropDownPanel.tsx    # 下拉面板容器 (仅 NavView 内嵌)
    │   │   ├── PanelHandle.tsx      # 拖拽手柄
    │   │   ├── PanelCollapsed.tsx   # 收起态内容
    │   │   ├── PanelContent.tsx     # 半屏/全屏内容
    │   │   └── PanelExpanded.tsx    # 全屏额外内容
    │   │
    │   ├── views/
    │   │   ├── SearchView.tsx       # 搜索视图（替代原 GlobalView）
    │   │   ├── NavView.tsx          # 导航视图（全览/逐站双模式 + 途径点管理）
    │   │   ├── BrowseView.tsx       # 浏览视图容器
    │   │   └── TreeView.tsx         # 树形管理容器
    │   │
    │   ├── canvas/
    │   │   ├── NavCanvas.tsx        # 统一画布组件（力导向/DAG 双模式）
    │   │   ├── ZoomControls.tsx     # 缩放按钮组
    │   │   └── CanvasBackground.tsx # 点网格背景
    │   │
    │   ├── search/
    │   │   ├── CardMatchList.tsx    # 卡片匹配结果列表
    │   │   ├── CardMatchItem.tsx    # 单行匹配卡片
    │   │   ├── BoundNodeList.tsx    # 绑定导航节点列表
    │   │   └── BoundNodeItem.tsx    # 单行绑定节点
    │   │
    │   ├── nav/
    │   │   ├── NavModeToggle.tsx    # 全览/逐站切换
    │   │   ├── WaypointsBar.tsx     # 途径点序列条
    │   │   └── WaypointChip.tsx     # 单个途径点 Chip
    │   │
    │   ├── tree/
    │   │   ├── TreeList.tsx         # 树列表容器
    │   │   ├── TreeNode.tsx         # 单行树节点
    │   │   └── TreeBadge.tsx        # 类型标签 (决策分支/层级分类)
    │   │
    │   └── cards/
    │       ├── CardStack.tsx        # 卡片堆叠容器
    │       ├── BrowseCard.tsx       # 单张卡片
    │       └── SwipeHint.tsx        # 滑动指示器动画
    │
    └── utils/
        ├── treeUtils.ts             # deriveParent / getTreeChildren / getTreeNode
        ├── weightUtils.ts           # 权重混合算法
        └── format.ts                # 日期/数字格式化
```

## 四、组件复用对照表

原 index.html 中的单块代码 → React 组件的映射：

| 原始代码区域 | 提取为 React 组件 | 复用次数 |
|-------------|-------------------|---------|
| `.status-bar` 结构 | `<StatusBar />` | 1（根布局固定） |
| `.tab-bar` + `.tab-btn` × 4 | `<TabBar />` → 内含 `<TabButton />` × 4 | 1 |
| `#search-global` + `#search-tree` input | `<SearchBar placeholder="..." onChange={fn} />` | 2（搜索视图 + 树搜索） |
| `.btn-primary` / `.btn-outline` | `<Button variant="primary" />` | 7+ |
| `.breadcrumb-bar` 结构 | `<BreadcrumbNav items={[]} onSelect={fn} />` | 1 |
| `#toast` + `toast()` 函数 | `<Toast />` (Portal) + `useToastStore` | 全局 |
| `#dd-panel` + `#dd-handle` | `<DropDownPanel />` → 内含 `<PanelHandle />` | 仅 NavView |
| D3 力导向图 + DAG 流 | `<NavCanvas data={} mode={} />` → `useNavCanvas()` | 1（双模式切换） |
| 搜索结果列表（原搜索换卡片+节点） | `<CardMatchItem />` + `<BoundNodeItem />` | 仅 SearchView |
| 途径点序列（新增） | `<WaypointsBar />` + `<WaypointChip />` | 仅 NavView |
| nav 模式切换（新增） | `<NavModeToggle />` | 仅 NavView |
| `.tree-row` 递归构建 | `<TreeNode node={} level={} />` | 11+ (递归) |
| `.tree-badge` | `<TreeBadge type="branch|hierarchy" />` | 11+ |
| `.browse-card` 堆叠 | `<CardStack cards={[]} />` → `<BrowseCard />` × 3 | 1 |
| 缩放按钮组 `#gz-*` | `<ZoomControls onIn={} onOut={} onReset={} />` | 1 |
| `initDDDrag` 拖拽 | `useDragPanel(ref, stateRef)` | 下拉面板用 |
| `initBrowseSwipe` 滑动 | `useCardSwipe(stackRef)` | 浏览视图用 |
| `buildTree` + `createTreeRowHTML` | `<TreeList data={} />` (递归渲染) | 1 |

## 五、状态管理设计 (Zustand)

### 5.1 viewStore — 视图切换

```typescript
interface ViewState {
  activeView: 'search' | 'nav' | 'browse' | 'tree';
  switchView: (name: ViewState['activeView']) => void;
}
```

约束：`switchView` 调用时自动触发 `panelStore.syncVisibility(name)`。

### 5.2 searchStore — 搜索匹配（替代原 globalStore）

```typescript
interface SearchState {
  query: string;
  matchedCards: CognitiveCard[];
  selectedCardId: string | null;
  boundNodes: NavNode[];            // selectedCard.bound_nodes 查询结果
  selectedNodeId: string | null;
  setQuery: (q: string) => void;    // debounce 300ms 后执行匹配
  selectCard: (id: string) => void; // 副作用: 查询 boundNodes
  selectNode: (id: string) => void;
  enterNav: () => NavNode | null;   // 返回 selectedNode 供 navStore 消费
}
```

### 5.3 panelStore — 下拉面板（仅 NavView 内使用）

```typescript
interface PanelState {
  node: NavNode | null;
  position: 'collapsed' | 'half' | 'full';
  setNode: (node: NavNode) => void;
  clearNode: () => void;
  setPosition: (pos: PanelState['position']) => void;
  syncVisibility: (viewName: string) => void;
}
```

- `setNode` 时若 panel 已展开 → 切换内容，保持 position
- `setNode` 时若 panel 未展开 → position 设为 `'half'`
- 面板按钮操作为"添加为途径点"（调用 `navStore.addWaypoint()`）而非"进入导航"

### 5.4 navStore — 导航视图（路径导航 + 途径点管理 + D3 数据）

```typescript
interface NavState {
  mode: 'overview' | 'station';     // 全览/逐站双模式
  currentNodeId: string;
  waypoints: NavNode[];              // 途径点序列
  init: (nodeId: string, mode?: 'overview' | 'station') => void;
  setMode: (m: 'overview' | 'station') => void;
  addWaypoint: (node: NavNode) => void;
  removeWaypoint: (index: number) => void;
  clearWaypoints: () => void;
  getNextNodes: (nodeId: string) => NextNodeRef[];  // 按权重排序
  getPrevNodes: (nodeId: string) => NextNodeRef[];
  allNavNodes: NavNode[];            // 全部导航节点（力导向图用）
  allEdges: GraphEdge[];             // 全部有向边
}
```

### 5.5 browseStore — 内容浏览（支持途径点进度）

```typescript
interface BrowseState {
  waypoints: NavNode[];             // 从 navStore 复制
  wpIndex: number;                   // 当前途径点索引
  cards: BrowseCard[];               // 当前途径点绑定的认知卡片
  currentIndex: number;              // 当前卡片索引
  initFromWaypoints: (waypoints: NavNode[]) => void;
  nextCard: () => void;
  prevCard: () => void;
  nextWaypoint: () => void;          // 切换到下一站的卡片
}
```

### 5.6 treeStore — 树形管理

```typescript
interface TreeState {
  flatData: TreeNodeData[];
  selectedId: string | null;
  expandedIds: Set<string>;
  searchQuery: string;
  selectNode: (id: string) => void;
  toggleNode: (id: string) => void;
  expandAncestors: (id: string) => void;
  setSearch: (q: string) => void;
}
```

## 六、D3 与 React 集成

使用 **Hook 封装** 模式，D3 负责数学/布局计算与 SVG 操作，React 负责生命周期管理。原 `useForceGraph` 和 `useDagFlow` 两个 Hook **合并为统一的 `useNavCanvas`**。

### 6.1 useNavCanvas — 统一 D3 Hook（力导向 + DAG）

```typescript
function useNavCanvas(
  containerRef: RefObject<HTMLDivElement>,
  mode: 'overview' | 'station',
  data: {
    // 全览模式
    allNodes?: NavNode[];
    allEdges?: GraphEdge[];
    // 逐站模式
    currentNode?: NavNode;
    prevNodes?: NavNode[];
    nextNodes?: NavNode[];
    // 通用
    waypointIds?: Set<string>;      // 已添加途径点，全览模式高亮用
  },
  options: {
    onNodeClick?: (node: NavNode) => void;
    onSelectNext?: (node: NavNode) => void;
  }
): {
  zoomIn: () => void;
  zoomOut: () => void;
  zoomReset: () => void;
}
```

实现要点：
- 内部维护两个独立的 D3 渲染实例（`forceSimulation` + `DAG layout`）
- `mode` 切换时切换可见 SVG group，**不销毁另一个实例**
- 首次进入 `overview` 模式时初始化 `forceSimulation`，预热 300 tick
- `waypointIds` 变化时更新全览图中对应节点的描边/填充样式
- 组件卸载时同时清理两个 D3 实例

### 6.2 关键代码示例

```tsx
// NavCanvas.tsx
const NavCanvas: React.FC<{
  mode: 'overview' | 'station';
  onNodeClick: (n: NavNode) => void;
}> = ({ mode, onNodeClick }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const { allNavNodes, allEdges, currentNode, waypoints } = useNavStore();

  const { zoomIn, zoomOut, zoomReset } = useNavCanvas(
    containerRef,
    mode,
    {
      allNodes: allNavNodes,
      allEdges: allEdges,
      currentNode: currentNode ?? undefined,
      waypointIds: new Set(waypoints.map(w => w.id)),
    },
    { onNodeClick }
  );

  return <div ref={containerRef} className={styles.canvas} />;
};
```

## 七、交互功能迁移清单

| 功能 | 原实现位置 | React 迁移方式 |
|------|----------|---------------|
| 视图切换 | `switchView()` + DOM class 切换 | `viewStore.switchView()` + 条件渲染 |
| 文本搜索 → 卡片匹配 | 原 GlobalView 搜索仅匹配导航节点 | `searchStore.setQuery()` debounce → 模糊匹配 title/description/corpus |
| 绑定节点查询 | 无（原版无此功能） | `searchStore.selectCard()` → 查询 card.bound_nodes → 渲染 BoundNodeList |
| 进入导航 | 面板中"进入导航"→ switchView('nav') | SearchView 底部"进入导航"按钮 → navStore.init(nodeId) |
| 全览模式（力导向图） | `initGlobalView()` | `useNavCanvas(mode='overview')` |
| 逐站模式（DAG 流） | `initNavView()` | `useNavCanvas(mode='station')` |
| 全览/逐站切换 | 无（原版为两个独立视图） | `<NavModeToggle />` → `navStore.setMode()` |
| 下拉面板拖拽 | `initDDDrag()` 全局函数 | `useDragPanel()` Hook，绑定到 PanelHandle ref |
| 三段停靠吸附 | `posFromPct()` + `applyDDPosition()` | `useDragPanel` 内部的 `useEffect` 计算 |
| 面板按钮操作 | "进入导航" | "添加为途径点" → 调用 `navStore.addWaypoint()` |
| 途径点序列管理 | 无（原版不支持多途径点） | `<WaypointsBar />` + `<WaypointChip />` + `navStore` 增删清 |
| 开始浏览 | "开始浏览"→ initCards(label) | "开始浏览"→ `browseStore.initFromWaypoints(waypoints)` |
| 途径点进度浏览 | 无（单次加载全部卡片） | `browseStore.wpIndex` + `nextWaypoint()` 按站切换 |
| 卡片滑动 | `touchstart/touchend/wheel` 监听 | `useCardSwipe(stackRef)` Hook |
| 树折叠/展开 | DOM `data-expanded` + `collapsed` class | React state `expandedIds: Set<string>` |
| 面包屑导航 | 直接操作 DOM | `<BreadcrumbNav>` 受控组件 |
| Toast | 全局 `toast()` 函数 | `<Toast />` + `useToastStore` |
| 键盘快捷键 | `document.addEventListener('keydown')` | React `useEffect` + `viewStore.switchView()` |

## 八、数据模型 TypeScript 类型

```typescript
// ===== 认知卡片 =====
interface CognitiveCard {
  id: string;               // "root/1/1"
  title: string;
  type: 'folder' | 'leaf';
  tag?: string;             // "决策分支" | "层级分类"
  corpus: string[];
  description?: string;
  bound_nodes?: string[];   // 绑定的导航节点 id 列表
  metadata?: {
    created_at?: string;
    updated_at?: string;
  };
}

// ===== 导航节点 =====
interface NextNodeRef {
  target_id: string;
  preset_weight: number;
  browse_weight: number;
  connection_type: 'preset' | 'browse_derived' | 'user_added';
}

interface NavNode {
  id: string;
  label: string;
  description: string;
  bound_cards?: string[];   // 绑定的认知卡片 id 列表
  browse_history?: { from: string; count: number; last_at: string }[];
  next_nodes: NextNodeRef[];
  priority_config?: {
    mode: 'mixed' | 'user_only';
    preset_priority: number;
    browse_priority: number;
    user_overrides: { target_id: string; override_weight: number }[];
  };
}

// ===== 图数据 =====
interface GraphNode extends NavNode {
  r: number;                // 渲染半径
  type: 'nav';
}

interface GraphEdge {
  source: string;
  target: string;
  weight: number;
}

// ===== DAG 流 =====
interface NavFlowData {
  currentNode: { id: string; label: string; desc: string };
  prevNodes: { id: string; label: string; presetWeight: number }[];
  nextNodes: {
    id: string; label: string;
    presetWeight: number;
    browseWeight: number;
  }[];
}

// ===== 浏览卡片 =====
interface BrowseCard {
  title: string;
  desc: string;
  tag: string;
  weight: number;
  cards: number;
  corpus: string[];
  related: { name: string; pos: '前置' | '后置' }[];
}
```

## 九、启动与开发

```bash
# 创建项目
npm create vite@latest knowledge-navigator-react -- --template react-ts
cd knowledge-navigator-react

# 安装依赖
npm install d3 zustand
npm install -D @types/d3

# 启动开发服务器 (自带 HMR 热更新)
npm run dev
```

Vite 内置 HMR，修改 `.tsx` / `.css` 文件后浏览器**即时热更新**，无需手动刷新。

## 十、迁移优先级建议

| 阶段 | 内容 | 产出 |
|------|------|------|
| **P0 基础框架** | App shell、StatusBar、4-Tab（搜索/导航/浏览/管理）、CSS Variables | 可切换的空壳 |
| **P1 共享组件** | SearchBar、Button、Toast、Icon、BreadcrumbNav | 被所有视图引用 |
| **P2 搜索视图** | CardMatchList、CardMatchItem、BoundNodeList、BoundNodeItem、searchStore | 文本搜索 → 卡片匹配 → 节点绑定查询 → 进入导航 |
| **P3 导航视图** | NavCanvas (useNavCanvas)、NavModeToggle、ZoomControls、DropDownPanel、WaypointsBar、WaypointChip、navStore | 全览/逐站双模式 + 多途径点序列管理 |
| **P4 浏览视图** | CardStack、BrowseCard、SwipeHint、useCardSwipe、browseStore | 按途径点顺序浏览绑定卡片 |
| **P5 树形视图** | TreeList、TreeNode、TreeBadge、treeStore | 树管理 + 搜索 |
| **P6 联动打磨** | 视图间数据流转（search → nav → browse 完整链路）、动画过渡、移动端适配 | 完整产品 |
