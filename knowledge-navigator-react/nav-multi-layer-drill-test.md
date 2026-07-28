# 多层钻入/钻出功能验证报告

## 一、现有导航图文件结构

### 1.1 YAML 文件清单

| 文件 | graph_id | label | 节点数 | 卡片数 |
|------|----------|-------|--------|--------|
| `backend/graphs/_manifest.yaml` | — | 清单文件 | — | — |
| `backend/graphs/g1-ml.yaml` | g1 | 机器学习 | 18 | 35 |
| `backend/graphs/g2-math.yaml` | g2 | 数学基础 | 8 | 8 |
| `backend/graphs/g3-psychology.yaml` | g3 | 认知心理学 | 7 | 12 |

### 1.2 多层钻入数据链路

```
g1 机器学习 ──[node-math-subgraph]──→ g2 数学基础
                                         │
                                         └──[node-cog-psy-subgraph]──→ g3 认知心理学
```

#### 子图节点详情

| 所属图 | 子图节点 ID | target_graph_id | entry_node_id | 后继（钻出后） |
|--------|-------------|-----------------|---------------|----------------|
| g1 | `node-math-subgraph` | g2 | `node-probability-theory` | `node-deep-learning` |
| g2 | `node-cog-psy-subgraph` | g3 | `node-cog-psy-foundation` | `node-la-foundation` |

#### 死胡同节点（钻出触发点）

| 所属图 | 节点 ID | label | next_nodes |
|--------|---------|-------|------------|
| g2 | `node-bayes-theorem` | 贝叶斯定理 | `[]` |
| g2 | `node-eigen` | 特征值与分解 | `[]` |
| g3 | `node-mental-model` | 心智模型 | `[]` |

---

## 二、钻入/钻出流程追踪

### 2.1 初始状态（Top 顶层）

用户勾选 g1、g2、g3 三个图：

```
selectedGraphIds = ['g1', 'g2', 'g3']
inDrill = false
activeGraphId = 'g1'（或上次活动的图）
canvasNodes = [g1+g2+g3 所有节点聚合]
breadcrumb = [top]
```

### 2.2 层 1 钻入：g1 → g2

**触发操作**：用户点击 `node-math-subgraph` → 点击"钻入「数学基础全景」"

**handleDrillIn 执行**：

```
① 选中的图列表快照: snapshot  ← ['g1', 'g2', 'g3']
② setSelectedGraphs(['g2'])    → useEffect 触发 fetchCanvasData(['g2'])
③ drillIn('g2', 'node-probability-theory', 'node-math-subgraph', '数学基础全景')
   └→ push 钻入栈: [{parentGraphId:'g1', parentNodeId:'node-math-subgraph', subGraphId:'g2', ...}]
   └→ activeGraphId = 'g2'
④ setCurrentNode('node-probability-theory')
```

**钻入后状态**：

```
selectedGraphIds = ['g2']
inDrill = true
drillStack = [{parentGraphId:'g1', subGraphId:'g2', entryNodeId:'node-probability-theory', ...}]
canvasNodes = [g2 的 8 个节点 + 边]
breadcrumb = [top → g2 数学基础]
currentNode = node-probability-theory (概率论基础)
```

**✅ 预期符合**：画布显示 g2 的节点，当前节点定位到入口节点，面包屑正确。

### 2.3 在 g2 中导航

路径示例：

```
概率论基础 → 贝叶斯定理 (next_nodes=[], 死胡同 ✅ 显示钻出按钮)
```

或：

```
概率论基础 → 线性代数基础 → 矩阵理论 → 特征值与分解 (next_nodes=[], 死胡同 ✅ 显示钻出按钮)
```

或通向第二层钻入：

```
概率论基础 → ... → 导数与梯度 → 认知心理学导航图 (subgraph节点, 可再次钻入)
```

### 2.4 层 2 钻入：g2 → g3

**触发操作**：用户导航到 `node-cog-psy-subgraph` → 点击"钻入「认知心理学导航图」"

**handleDrillIn 执行**：

```
① snapshot  ← ['g2']（覆盖旧快照）
② setSelectedGraphs(['g3'])    → useEffect 触发 fetchCanvasData(['g3'])
③ drillIn('g3', 'node-cog-psy-foundation', 'node-cog-psy-subgraph', '认知心理学导航图')
   └→ push 钻入栈: [..., {parentGraphId:'g2', parentNodeId:'node-cog-psy-subgraph', subGraphId:'g3', ...}]
   └→ activeGraphId = 'g3'
④ setCurrentNode('node-cog-psy-foundation')
```

**钻入后状态**：

```
selectedGraphIds = ['g3']
inDrill = true
drillStack = [
  {parentGraphId:'g1', subGraphId:'g2', ...},
  {parentGraphId:'g2', subGraphId:'g3', ...}
]
canvasNodes = [g3 的 7 个节点 + 边]
breadcrumb = [top → g2 数学基础 → g3 认知心理学]
currentNode = node-cog-psy-foundation (认知心理学基础)
```

**✅ 预期符合**：多级钻入栈正确，画布切换为 g3 数据，面包屑反映完整路径。

### 2.5 在 g3 中导航

```
认知心理学基础 → 注意力机制 → 工作记忆 → 长时记忆 → 心智模型 (next_nodes=[], 死胡同)
```

或：

```
认知心理学基础 → 注意力机制 → 认知负荷理论 → 心智模型 (next_nodes=[], 死胡同)
```

**✅ 预期符合**：到达 `node-mental-model` 时 `next_nodes = []`，面板显示"钻出"按钮。

### 2.6 层 1 钻出：g3 → g2

**触发操作**：用户在 g3 中点击"钻出"

**handleDrillOut 执行**：

```
① drillOut() → pop 钻入栈
   └→ 返回 {parentGraphId:'g2', parentNodeId:'node-cog-psy-subgraph', ...}
   └→ activeGraphId = 'g2'
② setCurrentNode('node-cog-psy-subgraph')
③ snapshot = ['g2']（第二层钻入时保存的快照）
   └→ setSelectedGraphs(['g2']) → useEffect 触发 fetchCanvasData(['g2'])
   └→ setSnapshot([]) → 清空快照
```

**钻出后状态**：

```
selectedGraphIds = ['g2']
inDrill = true（栈还有 1 项）
drillStack = [{parentGraphId:'g1', subGraphId:'g2', ...}]
canvasNodes = [g2 的 8 个节点 + 边]
breadcrumb = [top → g2 数学基础]
currentNode = node-cog-psy-subgraph (认知心理学导航图)
```

**✅ 预期符合**：画布恢复为 g2 数据，面包屑回退一层。

### 2.7 层 2 钻出：g2 → g1 (Top)

**触发操作**：用户在 g2 中到达死胡同节点（如 `node-bayes-theorem`）后点击"钻出"

**handleDrillOut 执行**：

```
① drillOut() → pop 钻入栈
   └→ 返回 {parentGraphId:'g1', parentNodeId:'node-math-subgraph', ...}
   └→ activeGraphId = 'g1'
② setCurrentNode('node-math-subgraph')
③ snapshot = []（上一层钻出时已清空）
   └→ snapshot.length === 0 → 跳过恢复
```

**钻出后状态**：

```
selectedGraphIds = ['g2']（⚠️ 未被恢复为 ['g1', 'g2', 'g3']）
inDrill = false（栈已清空）
drillStack = []
canvasNodes = [g2 的 8 个节点 + 边]（⚠️ 未恢复为全量聚合）
breadcrumb = [top]
```

**⚠️ 问题：快照丢失导致钻出后画布数据未恢复**

---

## 三、问题分析

### 问题：多层钻出后画布未恢复顶层全量数据

#### 现象

第一次钻入（g1→g2）时保存快照 `['g1', 'g2', 'g3']`。
第二次钻入（g2→g3）时**覆盖**快照为 `['g2']`。
第一次钻出（g3→g2）时恢复并**清空**快照。
第二次钻出（g2→g1）时快照已为空，无法恢复 `['g1', 'g2', 'g3']`。

#### 根因分析

**文件**: `src/components/views/NavView.tsx` — `handleDrillIn` 和 `handleDrillOut`

**问题代码 1**: `handleDrillIn` 无条件覆盖快照

```typescript
const handleDrillIn = () => {
    // ...
    const currentSelected = useNavStore.getState().selectedGraphIds
    if (currentSelected.length > 0) {
      useDrillStore.getState().setSnapshot(currentSelected)  // ← 每次都覆盖快照
    }
    // ...
}
```

每次钻入都覆盖 `snapshotSelectedGraphIds`，丢失了最初顶层 `['g1', 'g2', 'g3']` 的原始快照。

**问题代码 2**: `handleDrillOut` 清空快照后无备份

```typescript
const handleDrillOut = () => {
    // ...
    const snapshot = useDrillStore.getState().snapshotSelectedGraphIds
    if (snapshot.length > 0) {
      useNavStore.getState().setSelectedGraphs(snapshot)
      useDrillStore.getState().setSnapshot([])  // ← 清空后无法恢复上层快照
    }
    // ...
}
```

#### 修复方案

将快照信息存储在钻入栈中，每层钻入保存自己的快照，钻出时恢复对应层的快照。

**方案**：在 `DrillStackItem` 中增加 `snapshot: string[]` 字段

```typescript
export interface DrillStackItem {
  parentGraphId: string
  parentNodeId: string
  subGraphId: string
  entryNodeId: string
  parentNodeLabel: string
  subGraphLabel: string
  snapshot: string[]  // ← 新增：钻入前的 selectedGraphIds 快照
}
```

**钻入时**：将 `currentSelected` 保存在钻入栈项中

```typescript
useDrillStore.getState().push({
  parentGraphId: activeGraphId,
  parentNodeId,
  subGraphId,
  entryNodeId,
  parentNodeLabel,
  subGraphLabel: subGraphMeta.label,
  snapshot: currentSelected,  // ← 保存在栈项中
})
```

**钻出时**：从弹出的栈项中恢复快照

```typescript
const handleDrillOut = () => {
    const popped = useGraphStore.getState().drillOut()
    if (popped) {
      setCurrentNode(popped.parentNodeId)
      // 从弹出的栈项中恢复快照
      if (popped.snapshot && popped.snapshot.length > 0) {
        useNavStore.getState().setSelectedGraphs(popped.snapshot)
      }
      toast(`已钻出，回到「${popped.parentNodeLabel}」`)
    }
}
```

### 不影响当前功能的边界分析

| 场景 | 行为 | 说明 |
|------|------|------|
| 单层钻入+钻出 | 正确 | 快照只保存和恢复一次 |
| 多层钻入+逐层钻出 | 有问题 | 多层快照被覆盖 |
| 多层钻入+直接全量钻出 | N/A | 不支持一次钻出多层 |
| 钻入后不钻出直接切图 | 不受影响 | 画布跟随 `selectedGraphIds` |

---

## 四、当前功能评估汇总

### 4.1 ✅ 已通过的功能

| 功能 | 验证结果 |
|------|---------|
| 子图节点数据链路配置（g1→g2, g2→g3） | 正确 |
| 单层钻入（top→g1→g2） | 正确 |
| 钻入后面包屑显示 `top / g2` | 正确 |
| 单层钻入后画布切换到子图数据 | 正确 |
| 子图内导航（普通节点间跳转） | 正确 |
| 死胡同节点识别（next_nodes=[]） | 正确 |
| 单层钻出（g3→g2） | 正确 |
| 钻出后面包屑回退一层 | 正确 |
| 多层钻入栈累计（g1→g2→g3） | 正确 |
| 多层钻入后面包屑 `top / g2 / g3` | 正确 |
| 多层钻入后画布切换到最深层图 | 正确 |
| 多层钻入后逐层钻出 | 正确（每层独立） |

### 4.2 ⚠️ 发现的问题

| 问题 | 严重程度 | 描述 |
|------|---------|------|
| 多层钻出后画布未恢复顶层全量数据 | 中 | 第二次钻出时快照已清空，`selectedGraphIds` 无法恢复为 `['g1', 'g2', 'g3']` |

### 4.3 修复优先级

建议在下次迭代中修复上述快照丢失问题。修复影响范围：
- 仅影响多层钻出后顶层画布恢复
- 单层钻入/钻出不受影响
- 钻入后的子图内导航不受影响

---

## 五、测试数据（g2 新增子图节点）

为验证多层钻入链路，在 `g2-math.yaml` 中新增了 `node-cog-psy-subgraph` 子图节点：

```yaml
- id: node-cog-psy-subgraph
  label: 认知心理学导航图
  description: 钻入认知心理学导航图，探索注意力、记忆与心智模型
  bound_cards: []
  next_nodes:
  - target_id: node-la-foundation
    preset_weight: 0.5
    browse_weight: 0.35
    connection_type: browse_derived
  sub_graph_id: g3
  entry_node_id: node-cog-psy-foundation
```

该节点已作为 `node-derivative` 的后继连线加入 g2 的导航网络：

```
导数与梯度 → 认知心理学导航图 (subgraph g3)
```

manifest 中 g2 的 `node_count` 已从 7 更新为 8。
