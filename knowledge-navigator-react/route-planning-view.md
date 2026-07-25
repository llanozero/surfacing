# 路线规划界面 — 功能规范

## 版本

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| 1.0 | 2026-07-25 | — | 初始规范：新增路线规划界面，位于导航视图与浏览视图之间 |
| 1.1 | 2026-07-25 | — | 新增途经点排序模式：有序/无序，决定算法是否可自由重排途经点 |

---

## 一、概述

### 1.1 目标

在现有 **导航视图（NavView）** 与 **浏览视图（BrowseView）** 之间插入一个 **路线规划视图（PlanView）**，解决当前"途经点列表仅仅是用户手动添加的无序集合，缺乏路径排序优化"的问题。

用户添加完途经点后，不直接进入浏览，而是先进入规划界面，系统根据导航节点间的连接权重计算多条候选路径，用户从中选择一条，再按该规划的节点顺序进入浏览。

### 1.2 流程变更

```
当前流程:
  NavView (添加途经点) ──[开始浏览]──→ BrowseView

变更后流程:
  NavView (添加途经点) ──[规划路线]──→ PlanView ──[选择规划]──→ BrowseView
                                        │
                                        └──[返回]──→ NavView
```

### 1.3 途经点排序模式

算法规划路线前，需要明确途经点是否保持用户添加的先后顺序。分为两种模式：

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| **无序模式** (Unordered) | 途经点之间没有顺序约束，算法可自由重排所有途经点以最大化累积权重 | 用户只是勾选了一批想学的内容，不关心先后 |
| **有序模式** (Ordered) | 途经点的相对顺序必须保留，算法只能在顺序约束下穿插中间节点，但途经点的先后关系不可逆转 | 用户有明确的学习路径意图，如"先基础 → 再进阶 → 最后应用" |

两种模式共享同一套规划界面，用户在 PlanView 中通过切换器选择当前模式，系统立即按新模式重新生成候选计划。

### 1.4 类比：地图导航

| 认知导航 | 地图导航类比 |
|----------|-------------|
| 用户在 NavView 添加途经点 | 用户在地图上添加多个目的地 |
| 无序模式 | 用户添加多个目的地后选择"系统自动优化顺序" |
| 有序模式 | 用户在导航 App 中手动设置"途经点 1 → 途经点 2 → 途经点 3" |
| 点击"规划路线" | 点击"计算路线" |
| 系统计算多条候选路径（权重排序） | 地图推荐多条路线（最快/最短/避开收费） |
| 用户选择一条路径 | 用户选择推荐路线 |
| 按选定路径的节点顺序进入浏览 | 按规划好的途径点顺序导航 |

---

## 二、UI 交互

### 2.1 界面布局

```
┌──────────────────────────────────────┐
│  ← 返回导航                 路线规划  │  ← TopBar
├──────────────────────────────────────┤
│  途经点排序                          │
│  ● 有序（保持添加顺序）  ○ 无序      │  ← 排序模式切换器
├──────────────────────────────────────┤
│  🧭 途经点 (5 个)                     │
│  ┌──────────────────────────────────┐│
│  │ ① 机器学习基础                   ││  ← 用户添加的原始途经点
│  │ ② 监督学习                       ││  按添加顺序显示
│  │ ③ 神经网络基础                   ││  不可编辑，仅做参考
│  │ ④ 深度学习                       ││
│  │ ⑤ 注意力机制                     ││
│  └──────────────────────────────────┘│
├──────────────────────────────────────┤
│  推荐路线                            │
│  ┌──────────────────────────────────┐│
│  │ ● Plan A  总权重: 3.21  推荐     ││  ← 选中态
│  │   ① 机器学习基础                  ││
│  │   ② 监督学习                     ││
│  │   ③ 神经网络基础                  ││
│  │   ④ 注意力机制                   ││
│  │   ⑤ 深度学习                     ││
│  │   ┌────────────────────┐         ││
│  │   │ 查看详情 >         │         ││
│  │   └────────────────────┘         ││
│  ├──────────────────────────────────┤│
│  │ ○ Plan B  总权重: 2.89           ││  ← 未选中
│  │   ① 机器学习基础                  ││
│  │   ② 神经网络基础                  ││
│  │   ③ 监督学习                     ││
│  │   ④ 深度学习                     ││
│  │   ⑤ 注意力机制                   ││
│  │   ┌────────────────────┐         ││
│  │   │ 查看详情 >         │         ││
│  │   └────────────────────┘         ││
│  ├──────────────────────────────────┤│
│  │ ○ Plan C  总权重: 2.45           ││
│  │   ① 监督学习                     ││
│  │   ② 机器学习基础                  ││
│  │   ③ 神经网络基础                  ││
│  │   ④ 深度学习                     ││
│  │   ⑤ 注意力机制                   ││
│  └──────────────────────────────────┘│
├──────────────────────────────────────┤
│         [开始浏览 (5 站)]             │  ← BottomBar
└──────────────────────────────────────┘
```

### 2.2 交互行为

| ID | 功能 | 触发方式 | 预期行为 |
|----|------|----------|----------|
| PL-01 | 进入规划视图 | NavView 点击"规划路线" | 加载途经点 → 执行路径算法 → 渲染候选计划列表 |
| PL-02 | 切换排序模式 | 点击有序/无序标签 | 切换激活态 → 清空当前候选列表 → 按新模式重新执行算法 → 刷新候选计划 |
| PL-03 | 候选计划展示 | 进入视图或切换模式后自动完成 | 列出 2-4 条候选路线，每项显示: 总权重、节点序列 |
| PL-04 | 计划选中 | 点击计划行 | 高亮选中行，展开节点序列明细 |
| PL-05 | 查看详情 | 点击"查看详情" | 展开该计划的详细节点卡片信息（绑定认知卡片预览） |
| PL-06 | 切换计划 | 点击另一计划行 | 切换选中，高亮转移 |
| PL-07 | 开始浏览 | 点击"开始浏览" | 按所选计划的节点顺序初始化 BrowseView |
| PL-08 | 返回导航 | 点击"← 返回导航" | 回到 NavView，保留途经点不变 |
| PL-09 | 重新规划 | 点击"重新规划" | 按当前排序模式重新执行路径算法 |

### 2.3 关键细节

- **默认模式**：首次进入时默认**无序模式**，算法自由排列途经点
- **模式切换开关**：位于途经点列表上方，两个标签互斥，当前激活标签高亮
- **切换即重算**：切换排序模式后自动清空当前候选计划列表，立即按新模式重新执行算法并刷新
- **选中保持**：切换模式后若之前选中的计划在新列表中仍然存在（相同序列），保持其选中态；否则清空选中
- **默认选中**：总权重最高的计划默认选中
- **推荐标识**：总权重最高的计划标注"推荐"标签
- **节点序列展示**：每个计划显示 ① ② ③ ... 带箭头的节点序列，节点名为导航节点的 `label`
- **权重显示**：总权重保留 2 位小数
- **空途经点**：若途经点少于 2 个，进入界面时提示"至少需要 2 个途经点才能规划路线"，并提供返回按钮
- **无连接权重**：若途经点之间无直接连接，算法退化为保持用户添加顺序作为唯一计划

---

## 三、路径规划算法

### 3.1 算法输入

```typescript
type WaypointMode = 'ordered' | 'unordered'

interface PlanInput {
  waypoints: NavNode[]       // 用户添加的原始途经点（始终按添加顺序传入）
  weightMode: 'mixed' | 'user_only'  // 权重模式，取自 NavView 的当前设置
  waypointMode: WaypointMode         // 途经点排序模式
}
```

### 3.2 排序模式对算法的影响

两种模式的核心区别在于算法对途经点的排列自由度不同。

| 维度 | 无序模式 | 有序模式 |
|------|----------|----------|
| 排列自由度 | 完全自由 | 保持用户添加时的相对顺序 |
| 算法效果 | 追求全局最优权重 | 在顺序约束下寻找局部最优 |
| 适用场景 | 用户随意添加了一堆节点，想看看最佳学习路线 | 用户有明确的递进意图（如入门→进阶→应用） |
| 计划的 sequence 与原始 order 的关系 | 可以完全不同 | 途经点的先后关系与原列表一致 |

**有序模式的约束规则**：
```
原始途经点添加顺序: [W₀, W₁, W₂, ..., Wₙ]

任意有效计划的 sequence 必须满足:
  index_of(W₀) < index_of(W₁) < index_of(W₂) < ... < index_of(Wₙ)
  
即: 途经点中原先排在前面的，在任何候选计划中也必须排在前面。
算法可以在途经点之间插入中间跳转节点（导航图中未选为途经点的节点），
但途经点之间的相对顺序不可逆转。
```

**有序模式下算法的生成策略**：
1. 先以有序约束为硬边界，将问题拆解为"相邻途经点对之间的子路径规划"
2. 对每对相邻途经点 (Wᵢ → Wᵢ₊₁)，查找导航图中权重最高的连接路径（可能经过中间节点）
3. 若直接连接权重 > 0，序列保持 Wᵢ → Wᵢ₊₁
4. 若直接连接权重 = 0，查找 Wᵢ 到 Wᵢ₊₁ 的间接路径（经过 1 个中间节点中转）
5. 拼接所有子路径形成完整序列
6. 最终输出的计划数量较少（通常 1-2 条），因为自由度被约束

**无序模式下算法的生成策略**（与现有描述一致）：
1. 将途经点视为一个集合，枚举或贪心搜索最优排列
2. 详见下文的具体算法实现

### 3.3 连接权重查询

算法依赖导航节点间的 `next_nodes` 连接。给定导航节点 A 到 B 的权重查询：

```typescript
/**
 * 查询从 from 到 to 的合成权重。
 * 查找 from.next_nodes 中 target_id === to.id 的连接，
 * 按当前 weightMode 取 preset_weight 或 (preset + browse 合成)。
 * 若无直接连接则返回 0。
 */
function getConnectionWeight(from: NavNode, to: NavNode, mode: 'mixed' | 'user_only'): number
```

### 3.4 算法一：贪心前进（Greedy Forward）

> 适用模式：**仅无序模式**。有序模式下不使用此算法（见 §3.2 有序模式生成策略）。

每次从当前节点出发，选择通向**剩余未访问途经点**中权重最高的连接，直到所有途经点都被访问。

```
输入: waypoints = [W₀, W₁, W₂, ..., Wₙ]

1. 从 W₀ 出发，current = W₀，visited = {W₀}
2. 循环直到 visited 包含所有途经点:
   a. 在所有 visited 之外的目标中，找 max(getConnectionWeight(current, Wᵢ))
   b. 若最大权重 > 0，则 Wᵢ 加入序列，current = Wᵢ
   c. 若最大权重 === 0 (无直接连接)，则按剩余添加顺序尝试补偿
3. 输出完整序列

特点:
  - O(n²) 复杂度
  - 偏向权重高的局部最优
  - 无法保证全局最优
```

### 3.5 算法二：全排列最优（Permutation Optimal）

> 适用模式：**仅无序模式**。有序模式下不使用此算法。

对于途经点数量 ≤ 7 时，枚举所有排列，计算每条路径的**累积权重和**，取总权重最高的前 3 条。

```
累积权重和 = Σᵢ₌₀ⁿ⁻¹ getConnectionWeight(seq[i], seq[i+1])

特点:
  - O(n!) 复杂度，限制 n ≤ 7（n=7 时 5040 种排列，前端可承受）
  - 保证全局最优解
  - 当 n > 7 时自动降级为贪心算法
```

### 3.6 算法三：衔接优先（Connection Priority）

> 适用模式：**仅无序模式**。与有序模式中的子路径拼接概念不同。

对于途经点之间**存在连接边但权重未显式区分**的情况，优先排列出"连续连接"最多的路径。

```
1. 构建途经点之间的有向权重图
2. 从每个途经点作为起点尝试 DFS，追踪累积权重
3. 取累积权重最高的前 3 条不重复路径

特点:
  - 类似旅行商问题的近似解
  - 适用于途经点之间有稀疏连接图的场景
```

### 3.7 候选计划生成策略

系统根据当前 `waypointMode` 选择不同的生成路径：

**无序模式**（与 §1.0 一致）：
| 策略 | 优先级 | 说明 |
|------|--------|------|
| Permutation Optimal | 最高 | n ≤ 7 时取 Top 2 |
| Greedy Forward | 中 | 始终生成 1 条 |
| Connection Priority | 低 | 当 Permutation 不可用时作为补充 |

**有序模式**：
| 策略 | 优先级 | 说明 |
|------|--------|------|
| Sub-path Stitching | 唯一 | 相邻途经点对之间查找最优子路径，拼接为完整序列 |

有序模式下自由度低，通常只生成 1-2 条差异较小的计划（如是否插入中间跳转节点）。

去重规则：若两条计划的节点序列完全一致，仅保留一条。

### 3.8 算法输出

```typescript
interface RoutePlan {
  id: string              // 'plan-0', 'plan-1', ...
  label: string           // 'Plan A', 'Plan B', ...
  sequence: NavNode[]     // 按规划顺序排列的导航节点
  totalWeight: number     // 累积权重和
  algorithm: string       // 'permutation' | 'greedy' | 'connection' | 'subpath'
  isRecommended: boolean  // 总权重最高者标记为推荐
}

interface PlanOutput {
  plans: RoutePlan[]
  sourceWaypoints: NavNode[]  // 原始途经点（参考用）
  waypointMode: WaypointMode  // 生成时的途经点排序模式
}
```

---

## 四、数据流

### 4.1 ViewName 扩展

```typescript
// viewStore 中扩展视图名称
type ViewName = 'search' | 'nav' | 'plan' | 'browse' | 'tree'
//                      新增 ↑
```

- `plan` 视图**不加入底部 TabBar**（它是 NavView → BrowseView 的过渡界面，不作为独立 Tab）
- 键盘快捷键保持不变（1-4），plan 视图可通过 2 返回 NavView，3 进入 BrowseView

### 4.2 PlanStore（新增）

```typescript
// store/planStore.ts

type WaypointMode = 'ordered' | 'unordered'

interface PlanStore {
  // 输入
  sourceWaypoints: NavNode[]    // 来自 NavView 的原始途经点
  waypointMode: WaypointMode    // 当前排序模式（默认 'unordered'）

  // 算法结果
  plans: RoutePlan[]            // 候选计划列表
  selectedPlanId: string | null // 当前选中计划

  // 方法
  /** 设置排序模式，自动重新生成计划 */
  setWaypointMode: (mode: WaypointMode) => void
  /** 从途经点生成候选路线计划 */
  generatePlans: (waypoints: NavNode[], weightMode: 'mixed' | 'user_only') => void
  /** 选中某条计划 */
  selectPlan: (id: string) => void
  /** 按所选计划的 sequence 初始化 BrowseView */
  enterBrowse: () => NavNode[]
  /** 重置状态 */
  reset: () => void
}
```

### 4.3 跨视图数据流

```
SearchView                     NavView                     PlanView                      BrowseView
    │                             │                           │                              │
    │ 搜索 → 选中卡片               │                           │                              │
    │ → 选中节点 → 进入导航          │                           │                              │
    │                             │                           │                              │
    │ [进入导航] ──────────────→   │                           │                              │
    │                             │                           │                              │
    │                   添加途经点 [W₀, W₁, W₂, W₃]           │                              │
    │                             │                           │                              │
    │                   [规划路线] ───────────────────→       │                              │
    │                             │  传入: waypoints[]         │                              │
    │                             │   + weightMode             │                              │
    │                             │   + waypointMode(默认无序)  │                              │
    │                             │                           │                              │
    │                             │                  ┌──────────────────┐                   │
    │                             │                  │ 排序模式切换器    │                   │
    │                             │        有序 ←───→│ ●无序  ○有序    │                   │
    │                             │                  │ 切换自动重算     │                   │
    │                             │                  └──────────────────┘                   │
    │                             │                           │                              │
    │                             │                  算法计算候选计划                          │
    │                             │    无序模式: 自由排列途经点                              │
    │                             │                  Plan A: W₀→W₂→W₁→W₃  权重 3.21          │
    │                             │                  Plan B: W₀→W₁→W₂→W₃  权重 2.89          │
    │                             │    有序模式: 保持添加顺序                                │
    │                             │                  Plan A: W₀→W₁→W₂→W₃  权重 2.89          │
    │                             │                  Plan B: W₀→W₁→(中间)→W₂→W₃  权重 2.45   │
    │                             │                           │                              │
    │                             │                  用户选中 Plan A                          │
    │                             │                           │                              │
    │                             │              [开始浏览] ───────────────────→             │
    │                             │              传入: PlanA.sequence[]                       │
    │                             │                     → initFromSequence(seq)               │
    │                             │                           │        按规划顺序加载绑定卡片          │
    │                             │                           │        第 1/5 站: W₀           │
    │                             │                           │        ...                    │
    │                             │                           │        第 5/5 站: W₃           │
    │                             │                           │                              │
    │                             │    [← 返回导航] ←───────────────────                     │
    │                             │   保留原始途经点           │                              │
```

### 4.4 NavView → PlanView 的触发变更

NavView 中的"开始浏览"按钮改为"规划路线"：

```typescript
// NavView.tsx 变更
// 原有:
<Button onClick={handleStartBrowse}>开始浏览 ({waypoints.length} 站)</Button>

// 变更后:
<Button onClick={handleGoPlan}>规划路线 ({waypoints.length} 站)</Button>
```

```typescript
const handleGoPlan = () => {
  if (waypoints.length < 2) {
    toast('至少需要 2 个途经点才能规划路线')
    return
  }
  const planStore = usePlanStore.getState()
  planStore.generatePlans(waypoints, useNavStore.getState().mode)
  // waypointMode 默认 'unordered'，用户在 PlanView 中可切换
  switchView('plan')
}
```

### 4.5 PlanView → BrowseView 的初始化

```typescript
// PlanView.tsx
const handleStartBrowse = () => {
  const sequence = usePlanStore.getState().enterBrowse()
  if (sequence.length === 0) return
  useBrowseStore.getState().initFromSequence(sequence)
  switchView('browse')
}
```

### 4.6 browseStore.initFromSequence（新增方法）

当前 browseStore 的 `initFromWaypoints` 按途经点原始顺序加载卡片。新增 `initFromSequence` 方法，接受规划后的节点序列：

```typescript
interface BrowseStore {
  // ... 现有字段保持不变

  /** 按规划后的节点序列初始化浏览（替代 initFromWaypoints 的部分场景） */
  initFromSequence: (sequence: NavNode[]) => void
  // initFromWaypoints 保持不动（直接进入浏览时仍可用）
}
```

`initFromSequence` 与 `initFromWaypoints` 的区别：

| 方法 | 输入 | 用途 |
|------|------|------|
| `initFromWaypoints` | 原始途经点数组 | 直接进入浏览（无规划环节的快速路径） |
| `initFromSequence` | 规划后的节点序列 | 经过规划视图后进入浏览 |

实现上二者逻辑相同：复制序列 → wpIndex 置 0 → 加载第一站卡片 → currentIndex 置 0。

---

## 五、组件结构

### 5.1 PlanView 组件树

```
plan/
  ├── PlanView.tsx              ← 新增：规划视图主组件
  ├── PlanView.module.css       ← 新增
  ├── WaypointModeToggle.tsx    ← 新增：有序/无序模式切换器
  ├── WaypointModeToggle.module.css
  ├── PlanCard.tsx              ← 新增：单个计划卡片
  ├── PlanCard.module.css       ← 新增
  └── PlanDetail.tsx            ← 新增：计划详情展开
  └── PlanDetail.module.css     ← 新增
```

```
<PlanView>
  <TopBar>
    <Button variant="ghost" onClick={backToNav}>← 返回导航</Button>
    <h2>路线规划</h2>
  </TopBar>

  {/* 途经点排序模式切换 */}
  <WaypointModeToggle mode={waypointMode} onChange={setWaypointMode} />

  {/* 原始途经点参考区 */}
  <section className="source-waypoints">
    <h3>🧭 途经点 ({waypoints.length} 个)</h3>
    <WaypointList>
      {waypoints.map((wp, i) => (
        <WaypointChip key={wp.id} index={i} node={wp} />
      ))}
    </WaypointList>
  </section>

  {/* 候选计划列表 */}
  <section className="plan-list">
    <h3>推荐路线</h3>
    {plans.map(plan => (
      <PlanCard
        key={plan.id}
        plan={plan}
        isSelected={plan.id === selectedPlanId}
        onSelect={() => selectPlan(plan.id)}
      >
        <PlanCardHeader>
          <Radio checked={isSelected} />
          <PlanLabel>{plan.label}</PlanLabel>
          <TotalWeight>{plan.totalWeight}</TotalWeight>
          {plan.isRecommended && <Badge>推荐</Badge>}
        </PlanCardHeader>
        <SequenceFlow nodes={plan.sequence} />
        <CollapsibleDetail>
          <PlanDetail plan={plan} />
        </CollapsibleDetail>
      </PlanCard>
    ))}
  </section>

  {/* 底部操作 */}
  <BottomBar>
    <Button variant="outline" onClick={replan}>
      重新规划
    </Button>
    <Button variant="primary" onClick={startBrowse} disabled={!selectedPlanId}>
      开始浏览 ({selectedPlan?.sequence.length ?? 0} 站)
    </Button>
  </BottomBar>
</PlanView>
```

### 5.2 PlanCard 接口

```typescript
interface PlanCardProps {
  plan: RoutePlan
  isSelected: boolean
  onSelect: () => void
}
```

### 5.3 App 注册

```typescript
// App.tsx — 新增 plan 视图条件渲染
const viewMap: Record<ViewName, React.FC> = {
  search: SearchView,
  nav: NavView,
  plan: PlanView,     // ← 新增
  browse: BrowseView,
  tree: TreeView,
}
```

---

## 六、目录结构变更

```
knowledge-navigator-react/src/
  components/
    plan/                              ← 新增目录
      ├── PlanView.tsx
      ├── PlanView.module.css
      ├── WaypointModeToggle.tsx        ← 新增
      ├── WaypointModeToggle.module.css ← 新增
      ├── PlanCard.tsx
      ├── PlanCard.module.css
      ├── PlanDetail.tsx
      └── PlanDetail.module.css
  store/
    ├── planStore.ts                   ← 新增：PlanStore（含 waypointMode）
    ├── browseStore.ts                 ← 扩展：initFromSequence
    ├── viewStore.ts                   ← 扩展：ViewName 加入 'plan'
    └── ...
  utils/
    ├── routePlanner.ts                ← 新增：路径规划算法（含 ordered/unordered 分支）
    └── ...
  App.tsx                              ← 修改：注册 PlanView
```

---

## 七、验收标准

- [ ] NavView 中"开始浏览"按钮改为"规划路线"，途经点 ≥ 2 时可用
- [ ] 点击"规划路线"进入 PlanView，显示原始途经点列表
- [ ] PlanView 顶部显示排序模式切换器（有序 / 无序），默认无序
- [ ] 切换排序模式后自动清空候选列表并按新模式重新生成计划
- [ ] 无序模式下途经点可被自由排列，Plan A/B/C 序列顺序可能不同于添加顺序
- [ ] 有序模式下途经点保持添加先后关系，Plan 序列中 W₀ 始终在 W₁ 之前
- [ ] 有序模式下相邻途经点间无直接连接时，尝试查找中间跳转节点
- [ ] PlanView 显示 2-4 条候选路线计划（无序模式）或 1-2 条（有序模式），总权重最高的默认选中并带"推荐"标签
- [ ] 每条计划显示有序节点序列（① → ② → ③ ...）
- [ ] 点击计划行切换选中态
- [ ] 点击"查看详情"展开该计划的节点预览
- [ ] 点击"开始浏览"按所选计划的节点顺序进入 BrowseView
- [ ] 点击"← 返回导航"回到 NavView，途经点保持不变
- [ ] 途经点 < 2 时提示"至少需要 2 个途经点"
- [ ] PlanView 不显示在底部 TabBar 中
- [ ] 键盘快捷键 2 → NavView，3 → BrowseView
- [ ] 所有 TypeScript 类型定义正确，编译零错误

---

## 八、与现有功能的兼容性

| 现有功能 | 兼容性 | 说明 |
|----------|--------|------|
| NavView 途经点添加/删除 | ✅ 不变 | 仅按钮文案变更 |
| NavView 全览 / 逐站模式 | ✅ 不变 | 权重模式传入 PlanStore |
| BrowseView 卡片浏览 | ✅ 扩展 | 新增 initFromSequence，逻辑与 initFromWaypoints 一致 |
| TabBar 4 个 Tab | ✅ 不变 | plan 是过渡视图，不加入 TabBar |
| 键盘快捷键 1-4 | ✅ 不变 | plan 视图由内部按钮控制跳转 |
| D3 力导向图 / DAG 流 | ✅ 不变 | 不影响画布渲染 |

---

## 九、边界情况

| 场景 | 行为 |
|------|------|
| 途经点 = 2 个，无序模式 | 计算 A→B 和 B→A 两种排列的权重，若两种权重均为 0 则按添加顺序 |
| 途经点 = 2 个，有序模式 | 只能保持 A→B，若直接连接权重 = 0 则尝试查找 A 到 B 的间接路径 |
| 途经点 > 7 个，无序模式 | Permutation 算法不启用，仅用 Greedy + Connection 生成计划 |
| 途经点 > 7 个，有序模式 | 不受影响，子路径拼接算法复杂度为 O(n)，始终可用 |
| 有序模式下相邻途经点无任何连接 | 在序列中标记"无直接路径"，保留原始顺序但累积权重记为 0 |
| 所有途经点之间无直接连接 | 提示"途经点之间缺少直接连接路径"，无序模式仅提供按添加顺序的唯一计划 |
| 多条计划序列相同 | 去重，仅保留一条 |
| 从 PlanView 返回 NavView 后再次进入 | 重新执行生成（途经点可能已变更），waypointMode 重置为默认 'unordered' |
| 规划途中切换 Tab | 返回 NavView，保留途经点，清空 planStore 状态 |
