# 途经点快捷跳转连接 — 功能规范

## 版本

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| 1.0 | 2026-07-25 | — | 初始规范：在导航界面中为有序途经点之间快捷建立跳转连接 |
| 1.1 | 2026-07-25 | — | 权重改为优先级序号（整数，数字越小优先级越高）；灰色分类（无出向边）也可建立连接，统一为 ✚ 蓝色指示器 |
| 1.2 | 2026-07-25 | — | 对齐 design.md 优先级系统：补充浏览优先级推导、混合模式/纯用户模式、拼接规则；移除灰色不可用指示器 |

---

## 一、概述

### 1.1 目标

在**导航视图（NavView）**和**规划视图（PlanView）**中，为有序途经点之间的相邻节点对提供**一键建立跳转连接**的能力。用户无需手动进入节点管理编辑 `next_nodes`，即可快速在途经点之间创建有向连接边，从而直接影响路线规划的权重计算和路径推荐。

### 1.2 设计原则

- **快捷而非编辑**：区别于节点管理界面的详细编辑，此功能专注于"在途经点之间迅速建立连接"
- **视觉提示**：在途经点序列中直观显示哪些相邻对已有连接、哪些缺失（所有缺失均可新建）
- **双向感知**：新建连接后，NavView 画布（力导向图）即刻重绘新增边，PlanView 候选计划即时刷新
- **轻量操作**：一至两次点击完成连接创建，无需弹窗或表单

### 1.3 优先级系统（与整体设计对齐）

优先级系统遵循 `design.md` 定义的权重机制：

- **两种权重来源**：
  - **预设优先级（preset_priority）**：用户手动配置的优先级序号，数字越小优先级越高
  - **浏览优先级（browse_priority）**：基于用户历史浏览跳转频次自动推导的优先级
- **两种导航模式**：
  - **混合模式**：总优先级序列 = 预设优先级 + 浏览优先级（拼接）。优先级顺序为：**用户配置 > 最新浏览记录**，即用户配置的序号排在最前，浏览记录按时间倒序拼接在后
  - **纯用户模式**：仅使用预设优先级，忽略浏览记录
- **序号拼接规则**：所有优先级通过整数序号（1, 2, 3…）排列，数字越小越优先。多个连接可具有相同序号（视为同级优先级）

---

## 二、UI 交互

### 2.1 NavView 途经点序列中的连接指示

在 NavView 底部的 WaypointsBar 中，相邻途经点 Chip 之间增加连接状态指示器：

```
   ①                  ②                   ③                   ④
┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐
│ 机器   │   │ 监督   │   │ 神经   │   │ 深度   │   │ 注意   │   │ 词嵌入 │
│ 学习   │   │ 学习   │   │ 网络   │   │ 学习   │   │ 力机制 │   │        │
│ 基础   │   │        │   │ 基础   │   │        │   │        │   │        │
└────────┘   └────────┘   └────────┘   └────────┘   └────────┘   └────────┘
     │            │            │            │            │
     ▼            ▼            ▼            ▼            ▼
  已连接 ✅    缺失连接 ✚   已连接 ✅    缺失连接 ✚   缺失连接 ✚
  (优先级#1)              (优先级#2)
```

| 指示器 | 含义 | 点击行为 |
|--------|------|----------|
| ✅ 已连接（绿色） | `A.next_nodes` 中存在指向 B 的连接 | 点击弹出轻量编辑浮层（修改优先级 / 删除） |
| ✚ 可新建（蓝色） | `A.next_nodes` 中不存在指向 B 的连接 | 一键创建预设优先级 #1 的连接 + Toast 提示 |

### 2.2 PlanView 计划卡片的连接详情

在 PlanView 的每个 PlanCard 中，展开后的节点序列视图增加连接编辑能力：

```
┌──────────────────────────────────────────────────┐
│ ● Plan A  优先级路径  推荐                      │
│                                                   │
│  ┌─────┐  ✅#1   ┌─────┐  ✚#1   ┌─────┐       │
│  │ 机器 │ ─────→  │ 监督 │ ─────→  │ 神经 │ ...   │
│  │ 学习 │         │ 学习 │  (新建)  │ 网络 │       │
│  │ 基础 │         │      │         │ 基础 │       │
│  └─────┘         └─────┘         └─────┘       │
│                                                   │
│  优先级详情: #1 + #1 + ... = 3 级路径            │
│                                                   │
│  ┌────────────────────┐ ┌────────────────────┐    │
│  │ 连接操作面板       │ │                    │    │
│  │ 机器学习基础→监督学│ │ 监督学习→神经网络   │    │
│  │ 习                 │ │ 基础                │    │
│  │ 优先级: [#1]       │ │ 优先级: [#1]       │    │
│  │ 类型: [preset ▼]   │ │ 类型: [preset ▼]   │    │
│  │ [保存] [删除]      │ │ [保存] [删除]      │    │
│  └────────────────────┘ └────────────────────┘    │
└──────────────────────────────────────────────────┘
```

### 2.3 交互行为

| ID | 功能 | 触发方式 | 预期行为 |
|----|------|----------|----------|
| QC-01 | 查看连接状态 | WaypointsBar 或 PlanCard 序列渲染 | 相邻节点对之间显示连接状态指示器（✅/✚/⚠️） |
| QC-02 | 一键新建连接 | 在 NavView 点击 ✚ 指示器 | 在 `A.next_nodes` 中追加一项 `{target_id:B.id, preset_priority:1, connection_type:'user_added'}` → Toast "已建立跳转连接" |
| QC-03 | 编辑已有连接 | 在 NavView 点击 ✅ 指示器 | 弹出轻量浮层（InlinePopover），允许修改 preset_priority / connection_type |
| QC-04 | 删除连接 | 在轻量浮层中点击"删除" | 从 `A.next_nodes` 中移除对 B 的引用 → Toast "已删除跳转连接" |
| QC-05 | PlanView 批量新建 | 在 PlanCard 的节点序列中点击 ✚ | 与 QC-02 行为一致，建立连接后该段优先级生效，计划总优先级即时刷新 |
| QC-06 | PlanView 编辑连接 | 在 PlanCard 的展开详情中修改优先级/类型 | 更新 `A.next_nodes` 中的对应项，候选计划重新排序 |
| QC-07 | 全选所有缺失连接 | 点击"补齐所有缺失连接"按钮 | 遍历途经点序列中所有相邻对，对缺失连接的逐一创建（批量 QC-02） |
| QC-08 | 画布同步 | 任何连接新增/编辑/删除 | 调 navStore.syncFromSource() → 力导向图重绘新增/删除/更新的边 |

### 2.4 轻量编辑浮层（InlinePopover）

```
┌───────────────────┐
│ 机器学习基础 → 监督学习 │
│                    │
│ 优先级: [#1]       │  ← 整数输入框（数字越小优先级越高）
│ 连接类型: [preset ▼]│
│                    │
│ [保存]    [删除]    │
└───────────────────┘
```

- 浮层定位在指示器附近（移动端底部弹出，桌面端气泡定位）
- 优先级使用整数输入框（数字越小优先级越高，默认 #1）
- 连接类型下拉：preset / user_added / browse_derived
- 点击浮层外部自动保存并关闭

---

## 三、数据流

### 3.1 核心操作：建立连接

```typescript
/**
 * 在 from 节点的 next_nodes 中添加一条指向 to 节点的连接。
 * 若已存在则跳过（不覆盖），返回 false。
 * 若新建则同步到所有数据源。
 */
function ensureConnection(from: NavNode, to: NavNode): boolean {
  if (from.next_nodes.some((e) => e.target_id === to.id)) return false

  const ref: NextNodeRef = {
    target_id: to.id,
    preset_priority: 1,
    connection_type: 'user_added',
  }

  // 写回共享数据源
  from.next_nodes.push(ref)
  navNodeMap.set(from.id, from)

  // 同步 NavStore（画布边重绘）
  useNavStore.getState().syncFromSource()

  // 若有 PlanStore 候选计划则刷新
  const ps = usePlanStore.getState()
  if (ps.sourceWaypoints.length > 0) {
    ps.replan()
  }

  return true
}
```

### 3.2 连接状态查询

```typescript
type ConnectionStatus = 'connected' | 'missing' | 'unavailable'

function getConnectionStatus(fromId: string, toId: string): {
  status: ConnectionStatus
  ref?: NextNodeRef
} {
  const from = getNavNode(fromId)
  if (!from) return { status: 'unavailable' }

  const ref = from.next_nodes.find((e) => e.target_id === toId)
  if (ref) return { status: 'connected', ref }

  // 无论节点是否有出向连接，均允许建立连接，状态统一为 'missing'
  return { status: 'missing' }
}
```

### 3.3 批量补齐

```typescript
function fillAllMissing(waypoints: NavNode[]): number {
  let count = 0
  for (let i = 0; i < waypoints.length - 1; i++) {
    const from = getNavNode(waypoints[i].id)
    const to = getNavNode(waypoints[i + 1].id)
    if (from && to && ensureConnection(from, to)) count++
  }
  return count
}
```

### 3.4 NavNodeStore 扩展方法

向 `navNodeStore.ts` 增加三个方法（或单独新建 `quickConnectUtils.ts`）：

```typescript
// store/navNodeStore.ts 扩展 或 utils/quickConnectUtils.ts

interface QuickConnectActions {
  /** 为一对相邻节点建立连接（若已存在不做任何事） */
  ensureQuickConnection: (fromId: string, toId: string) => boolean
  /** 查询相邻节点的连接状态 */
  getConnectionStatus: (fromId: string, toId: string) => ConnectionStatusResult
  /** 批量补齐途经点序列中所有缺失的连接 */
  fillAllMissingConnections: (waypoints: NavNode[]) => number
}
```

---

## 四、组件变更

### 4.1 WaypointsBar 增强

在现有 `WaypointsBar.tsx` 的基础上，在相邻 Chip 之间插入连接状态指示器：

```tsx
// WaypointsBar.tsx（增强）
interface WaypointsBarProps {
  waypoints: NavNode[]
  onRemove: (index: number) => void
  showConnections?: boolean         // 是否显示连接指示器（默认 true）
  onQuickConnect?: (fromId: string, toId: string) => void   // 新建连接回调
  onEditConnection?: (fromId: string, toId: string) => void // 编辑连接回调
}
```

渲染逻辑：

```tsx
{waypoints.map((wp, i) => (
  <React.Fragment key={wp.id}>
    <WaypointChip
      index={i}
      node={wp}
      onRemove={() => onRemove(i)}
    />

    {/* 连接指示器（在 Chip 之间） */}
    {i < waypoints.length - 1 && showConnections && (
      <ConnectionIndicator
        fromId={wp.id}
        toId={waypoints[i + 1].id}
        onConnect={onQuickConnect}
        onEdit={onEditConnection}
      />
    )}
  </React.Fragment>
))}
<WaypointChip type="add" />
```

### 4.2 ConnectionIndicator 组件（新增）

```tsx
// components/nav/ConnectionIndicator.tsx
interface ConnectionIndicatorProps {
  fromId: string
  toId: string
  onConnect?: (fromId: string, toId: string) => void
  onEdit?: (fromId: string, toId: string) => void
}

// 内部使用 getConnectionStatus 判断状态，渲染不同样式
// ✅ 绿色 → 点击触发 onEdit（弹出轻量编辑浮层）
// ✚ 蓝色 → 点击触发 onConnect（一键新建）
// ⚠️ 灰色 → 理论上不再出现（所有缺失连接均为 ✚ 蓝色），保留备用
```

### 4.3 ConnectionEditPopover 组件（新增）

```tsx
// components/nav/ConnectionEditPopover.tsx
interface ConnectionEditPopoverProps {
  fromId: string
  toId: string
  initialRef: NextNodeRef
  fromLabel: string
  toLabel: string
  onSave: (fromId: string, toId: string, ref: NextNodeRef) => void
  onDelete: (fromId: string, toId: string) => void
  onClose: () => void
}
```

浮层包含：
- from → to 标题（只读）
- preset_priority 整数输入框（#1 最高，数字越大优先级越低）
- connection_type 下拉（preset / user_added / browse_derived）
- [保存] [删除] 两个按钮
- 点击外部调用 onClose

### 4.4 PlanCard 序列视图增强

在 `PlanCard.tsx` 的节点序列展示中，增加连接状态显示和编辑功能：

```tsx
// PlanCard.tsx（增强：在节点序列中显示连接）
{plan.sequence.map((node, i) => (
  <React.Fragment key={node.id}>
    <NodeBadge label={node.label} />
    {i < plan.sequence.length - 1 && (
      <ConnectionIndicator
        fromId={node.id}
        toId={plan.sequence[i + 1].id}
        onConnect={handleQuickConnect}
        onEdit={handleEditConnection}
      />
    )}
  </React.Fragment>
))}
```

在 `PlanCard.tsx` 的展开详情中增加连接编辑面板（PlanDetail 增强），可编辑 preset_priority 和切换连接类型。

### 4.5 批量操作按钮

在 WaypointsBar 右侧和 PlanView 底部操作区增加"补齐连接"按钮：

```tsx
// WaypointsBar.tsx 或 NavView.tsx
{waypoints.length >= 2 && (
  <Button
    variant="ghost"
    size="sm"
    onClick={() => {
      const count = fillAllMissingConnections(waypoints)
      toast(`已建立 ${count} 条跳转连接`)
    }}
  >
    补齐连接
  </Button>
)}
```

---

## 五、目录结构变更

```
src/
├── components/nav/
│   ├── WaypointsBar.tsx              ← 修改：增加连接指示器渲染
│   ├── WaypointsBar.module.css       ← 修改：连接指示器布局样式
│   ├── ConnectionIndicator.tsx       ← 新增：连接状态指示器组件
│   ├── ConnectionIndicator.module.css← 新增
│   └── ConnectionEditPopover.tsx     ← 新增：轻量编辑浮层
│   └── ConnectionEditPopover.module.css ← 新增
│
├── components/plan/
│   ├── PlanCard.tsx                  ← 修改：节点序列增加连接指示器
│   ├── PlanCard.module.css          ← 修改
│   ├── PlanDetail.tsx               ← 修改：增加连接编辑面板
│   └── PlanDetail.module.css        ← 修改
│
├── utils/
│   └── quickConnectUtils.ts         ← 新增：ensureConnection / getConnectionStatus / fillAllMissing
│
├── store/
│   └── navNodeStore.ts              ← 扩展：添加 ensureQuickConnection 等方法
```

---

## 六、实现方案

### 6.1 quickConnectUtils.ts

```typescript
import type { NavNode, NextNodeRef } from '../data/types'
import { getNavNode, navNodeMap, allNavNodes } from '../data/allNavNodes'
import { useNavStore } from '../store/navStore'
import { usePlanStore } from '../store/planStore'

export type ConnectionStatus = 'connected' | 'missing' | 'unavailable'

export interface ConnectionStatusResult {
  status: ConnectionStatus
  ref?: NextNodeRef
}

/**
 * 查询 fromId → toId 的连接状态
 */
export function getConnectionStatus(
  fromId: string,
  toId: string,
): ConnectionStatusResult {
  const from = getNavNode(fromId)
  if (!from) return { status: 'unavailable' }
  const ref = from.next_nodes.find((e) => e.target_id === toId)
  if (ref) return { status: 'connected', ref }
  // 无论节点是否有出向连接，均允许建立连接，状态统一为 'missing'
  return { status: 'missing' }
}

const DEFAULT_PRIORITY = 1

/**
 * 在 from 的 next_nodes 中建立指向 to 的连接（不存在时新建）。
 * 返回 true 表示新建成功，false 表示已存在或无效。
 */
export function ensureQuickConnection(fromId: string, toId: string): boolean {
  if (fromId === toId) return false
  const from = getNavNode(fromId)
  const to = getNavNode(toId)
  if (!from || !to) return false
  if (from.next_nodes.some((e) => e.target_id === toId)) return false

  from.next_nodes.push({
    target_id: toId,
    preset_priority: DEFAULT_PRIORITY,
    connection_type: 'user_added' as const,
  })

  // 同步共享数据源
  navNodeMap.set(fromId, from)
  syncAfterMutation()

  return true
}

/**
 * 更新已有连接
 */
export function updateQuickConnection(
  fromId: string,
  toId: string,
  updates: Partial<Pick<NextNodeRef, 'preset_priority' | 'connection_type'>>,
): boolean {
  const from = getNavNode(fromId)
  if (!from) return false
  const idx = from.next_nodes.findIndex((e) => e.target_id === toId)
  if (idx < 0) return false

  from.next_nodes[idx] = { ...from.next_nodes[idx], ...updates }
  navNodeMap.set(fromId, from)
  syncAfterMutation()
  return true
}

/**
 * 删除连接
 */
export function removeQuickConnection(fromId: string, toId: string): boolean {
  const from = getNavNode(fromId)
  if (!from) return false
  const lenBefore = from.next_nodes.length
  from.next_nodes = from.next_nodes.filter((e) => e.target_id !== toId)
  if (from.next_nodes.length === lenBefore) return false

  navNodeMap.set(fromId, from)
  syncAfterMutation()
  return true
}

/**
 * 批量补齐途经点序列中所有缺失的连接
 */
export function fillAllMissingConnections(waypoints: NavNode[]): number {
  let count = 0
  for (let i = 0; i < waypoints.length - 1; i++) {
    if (ensureQuickConnection(waypoints[i].id, waypoints[i + 1].id)) {
      count++
    }
  }
  return count
}

/** 变更后同步所有依赖方 */
function syncAfterMutation(): void {
  useNavStore.getState().syncFromSource()
  const ps = usePlanStore.getState()
  if (ps.sourceWaypoints.length > 0) {
    ps.replan()
  }
}
```

### 6.2 一键新建的默认优先级

| 场景 | 默认 preset_priority | 说明 |
|------|---------------------|------|
| 从未建立过连接 | 1 | 新建连接默认最高优先级 |
| 连接被删除后重新建立 | 原有 priority 值不变 | 避免因重建设置导致优先级序列变更 |

### 6.3 浏览优先级（browse_priority）

在**混合模式**下，`browse_priority` 由系统根据 `browse_history` 自动推算：

```typescript
/**
 * 根据浏览历史推导浏览优先级。
 * 历史中 count 越高的目标节点，优先级数字越小（越优先）。
 * 推导出的优先级拼接在用户预设优先级之后。
 */
function deriveBrowsePriority(
  fromId: string,
  history: BrowseRecord[],
): Map<string, number> {
  // 筛选从 fromId 出发的浏览记录，按 count 降序排列
  const records = history
    .filter((r) => r.from === fromId)
    .sort((a, b) => b.count - a.count)

  const result = new Map<string, number>()
  // 起始序号 = 预设优先级最大序号 + 1
  let seq = 1
  for (const r of records) {
    if (!result.has(r.to)) {
      result.set(r.to, seq++)
    }
  }
  return result
}
```

> 优先级数字说明：**数字越小优先级越高**。#1 为最高优先级，#2 次之，以此类推。多个连接的优先级数字可以相同（表示同级优先级）。在路径规划排序时，所有连接按预设优先级数字升序排列。总优先级序列 = 预设优先级 + 浏览优先级（拼接）。

### 6.4 连接指示器样式

```css
/* ConnectionIndicator.module.css */
.indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
  margin: 0 2px;
}

.connected {
  background: #e6f7e6;
  color: #52c41a;
  border: 1px solid #b7eb8f;
}
.connected:hover {
  background: #d9f7be;
}

.missing {
  background: #e6f7ff;
  color: #1890ff;
  border: 1px solid #91d5ff;
}
.missing:hover {
  background: #bae7ff;
}

.unavailable {
  background: #f5f5f5;
  color: #d9d9d9;
  border: 1px solid #e8e8e8;
  cursor: not-allowed;
}
```

---

## 七、连接变更后的连锁反应

```
用户通过 ConnectionIndicator 建立/编辑/删除连接
    │
    ▼
quickConnectUtils.ensureQuickConnection() / updateQuickConnection() / removeQuickConnection()
    │
    ├─ 1. 修改 allNavNodes 中的对应节点（共享数据源）
    ├─ 2. 更新 navNodeMap
    ├─ 3. 调用 navStore.syncFromSource()
    │       │
    │       ├─ 3a. allNavNodes 引用刷新
    │       ├─ 3b. allEdges 边集重算 → 力导向图重绘新边/移除的边
    │       └─ 3c. Canvas 节点渲染更新
    │
    ├─ 4. 若 PlanStore 有活跃途经点，调用 planStore.replan()
    │       │
    │       ├─ 4a. 候选计划按新边重新计算优先级排序
    │       ├─ 4b. 计划列表重新渲染，总优先级路径更新
    │       └─ 4c. 推荐计划可能变更（最高优先级路径切换）
    │
    └─ 5. Toast 提示操作结果
```

---

## 八、验收标准

- [ ] WaypointsBar 中相邻途经点 Chip 之间显示连接状态指示器
- [ ] 已有连接时显示 ✅ 绿色指示器，hover 显示优先级编号
- [ ] 无连接时显示 ✚ 蓝色指示器（无论节点是否有出向边，均可建立连接）
- [ ] 点击 ✚ 一键建立连接，预设优先级 #1，类型 user_added
- [ ] 点击 ✅ 弹出轻量编辑浮层，可修改 preset_priority / connection_type
- [ ] 编辑浮层中点击"删除"移除连接
- [ ] 连接新建/编辑/删除后，NavView 力导向图即时重绘边
- [ ] 连接新建/编辑/删除后，PlanView 候选计划刷新（优先级排序）
- [ ] "补齐连接"按钮一键为所有缺失相邻对建立连接
- [ ] PlanCard 节点序列也显示连接状态指示器
- [ ] PlanCard 展开详情中可编辑连接的优先级和类型
- [ ] 优先级使用整数输入框，数字越小优先级越高
- [ ] 删除连接后途经点序列和候选计划同步更新
- [ ] 批量补齐后 Toast 显示"已建立 X 条跳转连接"
- [ ] TypeScript 编译零错误

---

## 九、边界情况

| 场景 | 行为 |
|------|------|
| 重复点击同一 ✚ | 第二次 detect 已存在，不重复添加，Toast "连接已存在" |
| 节点 from === to（同一节点） | 不建立自环连接，函数返回 false |
| 在 WaypointsBar 中删除一个途经点 | 其关联的连接指示器也随之消失，无需清理 |
| 补齐连接时某些对已存在 | 跳过已存在的，仅统计新建立的 |
| 一条连接被删除后，画布上的边消失 | syncFromSource 重新推导 allEdges，移除的边不再包含 |
| 连接类型由 preset 改为 user_added | 优先级排序时按对应类型规则处理 |
| PlanView 中编辑连接优先级后返回 NavView | 连接变更已写入共享数据源，NavView 画布重绘 |
| 途经点数量变化（增/删） | 连接指示器数量和位置随之自动适配 |
| 多个连接优先级数字相同 | 视为同级优先级，排序时按途经点序列自然顺序排列 |
| 优先级输入为负数或 0 | 自动 clamp 为 1（最高优先级） |
