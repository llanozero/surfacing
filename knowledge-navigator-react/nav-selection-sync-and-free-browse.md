# 选中节点同步与自由分支浏览 — 功能规范

## 版本

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| 1.0 | 2026-07-26 | — | 初始规范：全览/逐站选中状态统一 + 单途经点自由分支浏览 |

---

## 一、概述

### 1.1 目标

解决导航界面中两个问题：

1. **全览与逐站视图选中节点不同步**：当前 `selectedNodeId`（全览高亮）与 `currentNodeId`（逐站中心）是两个独立状态，切换模式后选中丢失。需要统一为**同一个选中节点**，两种模式共享。

2. **单途经点入自由分支浏览**：选择单个途经点后增加按钮，进入自由分支浏览模式——不依赖规划序列，用户可直接在导航节点的前驱/后继之间自由跳转浏览，区别于原固定顺序卡片式浏览。

### 1.2 当前问题对照

| 问题 | 当前行为 | 期望行为 |
|------|----------|----------|
| 全览点击节点 → 切换逐站 | 逐站中心仍是旧的 currentNodeId | 全览选中节点即逐站目标中心 |
| 逐站点击前驱/后继 → 切换全览 | 全览高亮仍停留在之前的 selectedNodeId | 逐站中心即全览选中高亮 |
| 单途经点浏览 | 提示"至少需要 2 个途经点才能规划路线" | 增加"自由分支浏览"按钮，直接进入分支视图 |
| 固定顺序浏览 | 只能按规划序列前进/后退 | 自由模式下可按前驱/后继任意跳转 |

---

## 二、选中节点状态统一

### 2.1 方案：两个字段合一语义

不删除 `selectedNodeId` 与 `currentNodeId`，改为让两者**保持自动同步**——点击节点时同时更新两个字段：

```
┌────────────────────────────────────────────────┐
│               NavStore                          │
│                                                  │
│  selectedNodeId ── 全览高亮（视觉）              │
│       │                                          │
│       │ 全览模式点击时同步                        │
│       ▼                                          │
│  currentNodeId ── 逐站中心（导航锚点）           │
│                                                  │
│  两者始终指向同一个节点 ID                       │
└────────────────────────────────────────────────┘
```

### 2.2 点击处理变更

```typescript
// NavView.tsx — handleNodeClick 统一更新两个字段

const setCurrentNode = useNavStore((s) => s.setCurrentNode)
const setSelectedNode = useNavStore((s) => s.setSelectedNode)

const handleNodeClick = (node: NavNode) => {
  setPanelNode(node)

  // ★ 两字段同步：全览模式下更新 currentNodeId，逐站模式下更新 selectedNodeId
  setCurrentNode(node.id)
  setSelectedNode(node.id)
}
```

不再按 mode 分流，始终同时更新两个字段。

### 2.3 边界行为

| 场景 | 行为 |
|------|------|
| 全览中点击节点 | `selectedNodeId` + `currentNodeId` 均更新为该节点 |
| 立即切换到逐站 | 中心节点为新点击的节点，前驱/后继重绘 |
| 逐站中点击前驱节点 | `currentNodeId` + `selectedNodeId` 均更新 |
| 切换到全览 | 新点击的节点保持选中高亮 |
| 起始无选中时 | 默认以 `allNavNodes[0]` 初始化两个字段 |
| 途经点列表变更 | 不影响选中同步（仅影响画布高亮优先级） |

### 2.4 NavStore 变更

```typescript
interface NavStore {
  // ... 现有字段
  currentNodeId: string
  selectedNodeId: string | null
}

// 初始化：两个字段指向同一节点
export const useNavStore = create<NavStore>((set, get) => ({
  currentNodeId: 'node-ml-foundation',
  selectedNodeId: null,  // 首次进入全览时无选中高亮，但默认中心已存在

  setCurrentNode: (nodeId) => {
    if (getNavNode(nodeId)) set({ currentNodeId: nodeId })
  },

  setSelectedNode: (nodeId) => set({ selectedNodeId: nodeId }),
  // ...
}))
```

> 注意：`setCurrentNode` 与 `setSelectedNode` 是两个独立 action，由调用方（NavView 的 `handleNodeClick`）同时调用两者来完成同步。

### 2.5 useNavCanvas 适配

现有逻辑不需大改，`applyNodeStyles` 依赖 `data.selectedNodeId`，`renderStation` 依赖 `data.currentNode`——两者现在指向同一个节点，各自正常响应。

```typescript
// useNavCanvas — 现有 effect 监督 selectedNodeId 变化（全览高亮刷新）
useEffect(() => {
  applyNodeStyles()
}, [data.selectedNodeId, data.waypointIds, applyNodeStyles])

// 现有 effect 监督 currentNode 变化（逐站重绘）
useEffect(() => {
  if (mode === 'station') renderStation()
}, [mode, data.currentNode, data.prevNodes, data.nextNodes, renderStation])
```

### 2.6 对现有文档的覆盖

本文 §2 的同步方案**覆盖** `nav-canvas-node-interaction.md` §4.1 中"两个字段分开管理"的设计。如已实现按 mode 分流的 `handleNodeClick`，应改为同时 set 两个字段。

---

## 三、自由分支浏览模式

### 3.1 触发条件

在导航界面底部操作栏中，当**途经点个数 = 1** 时，「规划路线」按钮旁新增「自由分支浏览」按钮：

```
  ┌─────────────────────────────────────────────────────────┐
  │ 途径点: [机器学习基础]                                   │
  │                                                         │
  │  [清空途径点]  [自由分支浏览 →]  [规划路线 (1 站)]      │
  │                                          ↑ disabled     │
  └─────────────────────────────────────────────────────────┘
```

- 途经点 = 0：「自由分支浏览」与「规划路线」均 disabled
- 途经点 = 1：「自由分支浏览」可用（primary 样式），「规划路线」disabled
- 途经点 ≥ 2：「自由分支浏览」隐藏或 disabled，「规划路线」可用

### 3.2 自由分支浏览视图

点击「自由分支浏览」进入专门的分支浏览视图，与现有固定顺序浏览（BrowseView）走不同路径：

```
分支浏览视图布局：

  ┌───────────────────────────────────────────────────┐
  │  ← 返回导航                                         │
  │                                                     │
  │  ┌───────────────────────┐                         │
  │  │  当前节点: 机器学习基础  │    ← 标题区             │
  │  │  描述: ...             │                         │
  │  └───────────────────────┘                         │
  │                                                     │
  │  ┌── 关联卡片 ──────────────────────────────────┐  │
  │  │  [卡片 1]  [卡片 2]  [卡片 3]                 │  │
  │  │  ← 左右滑动翻卡（与现有 CardStack 相同）       │  │
  │  └───────────────────────────────────────────────┘  │
  │                                                     │
  │  ──── 分支跳转 ──────────────────────────────────   │
  │                                                     │
  │  前驱节点 ────────────────────────────────────────  │
  │  ┌───────────────────────┐                         │
  │  │  [数学基础]    权重 0.80│   ← 可点击跳转          │
  │  │  [线性代数]    权重 0.65│                         │
  │  └───────────────────────┘                         │
  │                                                     │
  │  后继节点 ────────────────────────────────────────  │
  │  ┌───────────────────────┐                         │
  │  │  [监督学习]    权重 0.92│   ← 可点击跳转          │
  │  │  [无监督学习]  权重 0.88│                         │
  │  │  [强化学习]    权重 0.75│                         │
  │  └───────────────────────┘                         │
  │                                                     │
  │  [添加为途经点]  [设为当前节点]                      │
  └───────────────────────────────────────────────────┘
```

### 3.3 数据结构

在 navStore 中新增分支浏览状态：

```typescript
interface NavStore {
  // ... 现有字段

  /** 自由分支浏览模式是否激活 */
  freeBrowseActive: boolean

  /** 切换自由分支浏览模式 */
  setFreeBrowse: (active: boolean) => void
}
```

在 browseStore 中新增独立字段以区分固定浏览与自由浏览：

```typescript
interface BrowseStore {
  // ... 现有字段（固定顺序浏览）

  /** 浏览模式: 'sequential' | 'free' */
  browseMode: 'sequential' | 'free'

  /** 自由分支浏览的当前节点 */
  freeNodeId: string | null

  /** 前驱节点列表（带权重排序） */
  prevBranchNodes: NextNodeItem[]

  /** 后继节点列表（带权重排序） */
  nextBranchNodes: NextNodeItem[]

  /** 进入自由分支浏览 */
  enterFreeBrowse: (nodeId: string) => void

  /** 自由模式：跳转到前驱/后继节点 */
  jumpToNode: (targetId: string) => void

  /** 退出自由分支浏览，回到导航 */
  exitFreeBrowse: () => void
}
```

### 3.4 流程

```
用户点击「自由分支浏览」
    │
    ▼
NavView: setFreeBrowse(true)
    │
    ▼
切换视图为 FreeBrowseView（新路由或 BrowseView 的模式分支）
    │
    ▼
FreeBrowseView 初始化：
  1. 以当前选中节点（selectedNodeId/currentNodeId）为起始节点
  2. 加载该节点的绑定卡片（调用 cardsForWaypoint 或后端 /api/browse/cards）
  3. 加载前驱列表（getPrevNodes）和后继列表（getNextNodes）
  4. 进入分支浏览循环
```

### 3.5 分支跳转

用户点击前驱或后继节点后：

```
当前: 机器学习基础
用户点击后继「监督学习」
    │
    ▼
FreeBrowseView 执行 jumpToNode('node-supervised-learning')
    │
    ├── 更新 freeNodeId = 'node-supervised-learning'
    ├── 重新加载该节点的绑定卡片
    ├── 重新计算前驱列表 ← 现在指向机器学习基础等
    └── 重新计算后继列表 ← 神经网络基础等
```

每次跳转后视图刷新，前驱/后继列表随之更新为新节点的相邻节点。

### 3.6 操作按钮

| 按钮 | 位置 | 说明 |
|------|------|------|
| 「添加为途经点」 | 底部 | 将当前节点加入 navStore 的 waypoints 列表 |
| 「设为当前节点」 | 底部 | 更新 navStore 的 currentNodeId/selectedNodeId |
| 「← 返回导航」 | 顶部 | 退出自由分支浏览，回到导航界面 |

### 3.7 与视图切换的交互

| 操作 | 行为 |
|------|------|
| 自由浏览中切换到搜索/规划/管理 | 退出自由浏览模式，保持当前节点选中 |
| 从其他视图返回导航 | 不自动恢复自由浏览模式 |
| 自由浏览中清空途经点 | 不影响自由浏览模式（自由浏览不依赖途经点列表） |
| 自由浏览中点击「规划路线」 | 退出自由浏览，进入规划视图 |

### 3.8 路由设计

自由分支浏览视图作为独立组件或 BrowseView 的分支模式：

**方案 A（推荐）：独立视图组件**

```typescript
// 新增 src/components/views/FreeBrowseView.tsx
const FreeBrowseView: React.FC = () => { ... }
```

在 App.tsx 中注册视图切换（现有 viewStore 的 view 类型扩展）：

```typescript
type ViewType = 'search' | 'nav' | 'plan' | 'browse' | 'tree' | 'free-browse'
```

**方案 B：BrowseView 内部模式**

```typescript
// BrowseView.tsx — 根据 browseMode 渲染不同内容
if (browseMode === 'free') {
  return <FreeBrowseContent ... />
}
// 原有顺序浏览逻辑
```

---

## 四、代码变更摘要

### 4.1 NavStore

```typescript
// src/store/navStore.ts — 新增 freeBrowseActive 字段
interface NavStore {
  // ... 现有
  freeBrowseActive: boolean
  setFreeBrowse: (active: boolean) => void
}

// 初始值
freeBrowseActive: false,

// action
setFreeBrowse: (active) => set({ freeBrowseActive: active }),
```

### 4.2 NavView — 按钮条件渲染

```typescript
// NavView.tsx — 底部按钮新增

<Button
  variant="primary"
  size="sm"
  onClick={handleFreeBrowse}
  disabled={waypoints.length === 0}
  style={{ display: waypoints.length === 1 ? 'inline-flex' : 'none' }}
>
  自由分支浏览
</Button>

const handleFreeBrowse = () => {
  if (waypoints.length === 0) return
  // 以第一个途经点为起始节点
  const startNode = waypoints[0]
  setFreeBrowse(true)
  switchView('free-browse')
}
```

### 4.3 FreeBrowseView 组件

```typescript
// src/components/views/FreeBrowseView.tsx（新增）

interface FreeBrowseViewProps {
  startNode: NavNode
  onJump: (node: NavNode) => void
  onExit: () => void
}
```

核心逻辑：
1. 渲染当前节点的标题/描述
2. 渲染当前节点的绑定卡片（CardStack 可复用）
3. 渲染前驱/后继节点列表（点击触发跳转）
4. 底部操作按钮

### 4.4 FreeBrowseView 模块样式

```css
/* FreeBrowseView.module.css（新增） */

.branchSection {
  margin-top: 12px;
  padding: 10px 14px;
  background: #1e293b;
  border-radius: 10px;
}

.branchTitle {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 8px;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.branchItem {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s;
}

.branchItem:hover {
  background: rgba(6, 182, 212, 0.1);
}

.branchLabel {
  flex: 1;
  color: #e2e8f0;
  font-size: 14px;
}

.branchWeight {
  color: #94a3b8;
  font-size: 12px;
}
```

### 4.5 BrowseStore 扩展

```typescript
// src/store/browseStore.ts — 新增自由浏览相关

interface BrowseStore {
  // ... 现有

  /** 自由分支浏览状态 */
  browseMode: 'sequential' | 'free'
  freeNodeId: string | null
  freeCards: BrowseCard[]
  freePrevNodes: NextNodeItem[]
  freeNextNodes: NextNodeItem[]

  enterFreeBrowse: (startNode: NavNode) => void
  jumpToNode: (targetId: string) => void
  exitFreeBrowse: () => void
}

// 实现
enterFreeBrowse: (startNode) => {
  set({
    browseMode: 'free',
    freeNodeId: startNode.id,
    freeCards: cardsForWaypoint(startNode),
    freePrevNodes: getPrevNodes(startNode.id),
    freeNextNodes: getNextNodes(startNode.id),
  })
},

jumpToNode: (targetId) => {
  const target = getNavNode(targetId)
  if (!target) return
  set({
    freeNodeId: target.id,
    freeCards: cardsForWaypoint(target),
    freePrevNodes: getPrevNodes(target.id),
    freeNextNodes: getNextNodes(target.id),
  })
},

exitFreeBrowse: () => {
  set({
    browseMode: 'sequential',
    freeNodeId: null,
    freeCards: [],
    freePrevNodes: [],
    freeNextNodes: [],
  })
}
```

### 4.6 后端 API 适配

完整模式（pro）下，自由分支浏览需新增 API：

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/browse/free/start` | 以节点 ID 开始自由浏览 |
| POST | `/api/browse/free/jump/{target_id}` | 跳转到目标节点 |

#### POST /api/browse/free/start

**请求体：** `{"node_id": "node-ml-foundation"}`

**响应 200：**
```json
{
  "ok": true,
  "current_node_id": "node-ml-foundation",
  "current_node_label": "机器学习基础",
  "cards": [ ... ],
  "prev_nodes": [ ... ],
  "next_nodes": [ ... ]
}
```

#### POST /api/browse/free/jump/{target_id}

**请求体：** 无

**响应 200：** 同上（返回新节点的全部上下文）

---

## 五、验收标准

- [ ] 全览模式点击节点后切换到逐站模式，中心节点为新点击的节点
- [ ] 逐站模式点击前驱/后继节点后切换到全览模式，选中高亮为新点击的节点
- [ ] 两种模式任意切换，选中节点保持一致
- [ ] 途经点 = 1 时，「自由分支浏览」按钮显示且可用
- [ ] 途经点 = 0 时，「自由分支浏览」按钮 disabled
- [ ] 途经点 ≥ 2 时，「自由分支浏览」按钮隐藏或 disabled
- [ ] 自由分支浏览视图展示当前节点的绑定卡片（可左右翻卡）
- [ ] 自由分支浏览视图展示前驱节点列表（带标签和权重）
- [ ] 自由分支浏览视图展示后继节点列表（带标签和权重）
- [ ] 点击前驱/后继节点，视图刷新为新节点的绑定卡片和相邻节点
- [ ] 「添加为途经点」将当前节点加入途经点列表
- [ ] 「返回导航」退出自由分支浏览，回到导航界面
- [ ] 自由分支浏览过程中，选中节点在导航画布上持续高亮
- [ ] 所有 TypeScript 类型定义正确，编译零错误

---

## 六、与现有功能的兼容性

| 现有功能 | 兼容性 | 说明 |
|----------|--------|------|
| nav-canvas-node-interaction.md | ⚠️ 覆盖 §4.1 | 原"两个字段分开管理"改为"两个字段同步更新" |
| 逐站视图单击更新 | ✅ 增强 | 删除 mode 分流，始终同步双字段 |
| 全览三态样式 | ✅ 不变 | applyNodeStyles 逻辑不变 |
| 固定顺序浏览（BrowseView） | ✅ 不变 | 不受自由分支浏览影响 |
| 路线规划（PlanView） | ✅ 不变 | 仅新增单途经点时的替代入口 |
| 途经点序列操作 | ✅ 不变 | 增删改途径点逻辑不变 |
| 下拉面板 | ✅ 不变 | handleNodeClick 始终调用 setPanelNode |

---

## 七、边界情况

| 场景 | 行为 |
|------|------|
| 选中节点后节点因搜索/数据变更消失 | 清除选中状态，回退到默认锚点节点 |
| 自由浏览中起始节点被删除 | 退出自由浏览，返回导航 |
| 自由浏览中从前驱跳到前驱再跳回 | 正常支持，每次跳转刷新完整上下文 |
| 自由浏览中途经点列表为空 | 不影响自由浏览（两者独立状态） |
| 固定顺序浏览进行中进入自由浏览 | 两者独立，互不影响 |
| 自由浏览中点击「规划路线」 | 需退出自由浏览，且途经点 ≥ 2 时才可用 |
| 完整模式（pro）下自由分支浏览失败 | 降级为轻量派生（与 browseStore 现有降级策略一致） |

---

*本文档定义了导航界面中两个问题的解决方案：选中节点状态的全览/逐站同步，以及单途经点进入自由分支浏览的能力。*
