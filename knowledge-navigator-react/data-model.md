# 认知导航 — 数据模型定义

## 一、认知卡片（Cognitive Card）

### 扁平存储结构（YAML）

认知卡片以**扁平列表**存储于本地 `.yaml` 文件中。`parent` 和 `children` 不由存储字段维护，而是由算法根据 `id` 的层级特征自动推导。

```yaml
cognitive_cards:
  - id: root/1
    title: 机器学习
    type: folder
    corpus:
      - 机器学习是人工智能的一个子领域，使计算机能够从数据中学习和改进。
      - 主要范式包括监督学习、无监督学习和强化学习。
    tag: 层级分类
    bound_nodes:
      - node-ml-foundation
      - node-ai-intro

  - id: root/1/1
    title: 监督学习
    type: leaf
    corpus:
      - 使用标注数据训练模型，学习从输入到输出的映射函数。
      - 常见算法包括线性回归、逻辑回归、SVM、决策树和神经网络。
    tag: 决策分支
    bound_nodes:
      - node-supervised
      - node-ml-foundation

  - id: root/1/2
    title: 无监督学习
    type: leaf
    corpus:
      - 从未标注数据中发现隐藏的模式和结构。
      - 常见算法包括聚类（K-means）、降维（PCA）和关联规则学习。
    tag: 层级分类
    bound_nodes:
      - node-unsupervised

  - id: root/2
    title: 神经网络
    type: folder
    corpus:
      - 受生物神经网络启发设计的计算模型。
    tag: 层级分类
    bound_nodes:
      - node-nn-foundation
```

### 字段定义

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | 是 | 卡片唯一标识，同时也是层级路径标识。格式如 `root/1`、`root/1/2`。`root` 仅作为根目录标识，不是卡片节点。 |
| `title` | string | 是 | 卡片标题，在树形视图和卡片视图中显示。 |
| `description` | string | 否 | 卡片描述，简短概述卡片内容（1-2 句话）。可为空，由自动生成规则填充。 |
| `corpus` | string[] | 否 | 语料库列表，每个元素是一段语料文本。用于自动生成标题/描述，或作为知识详情展示。 |
| `type` | enum | 是 | 节点类型：`folder`（有子卡片，可展开/折叠）、`leaf`（叶子节点，无子卡片）。 |
| `tag` | string | 否 | 标签，标识子卡片的两种应用场景（见下文）。 |
| `bound_nodes` | string[] | 否 | 绑定到此卡片的导航节点 id 列表。一个卡片可被多个导航节点引用。 |
| `metadata.created_at` | string | 否 | 创建时间（ISO 8601）。 |
| `metadata.updated_at` | string | 否 | 最后更新时间。 |
| `metadata.generated` | boolean | 否 | 是否由语料库或子节点自动生成。 |

> **不存储的字段**：`parent` 和 `children` 不由 YAML 存储，而是由算法在运行时自动推导。

### parent / children 推导算法

算法基于 `id` 的层级路径规则自动建立父子关系：

```
输入卡片列表：
  root/1           → 一级，父级为 root
  root/1/1         → 二级，父级为 root/1
  root/1/2         → 二级，父级为 root/1
  root/2           → 一级，父级为 root
  root/2/1         → 二级，父级为 root/2

推导规则：
  1. 去掉 id 中最后一段 "/数字"，即为 parent。
     root/1/1 → parent = root/1
     root/1   → parent = root
  2. type 为 folder 的卡片，其 children 为所有 parent 等于自身 id 的卡片。
     root/1 → children = [root/1/1, root/1/2]
  3. type 为 leaf 的卡片，children 恒为空数组。
```

```typescript
// 伪代码
function deriveParent(id: string): string {
  const slashIdx = id.lastIndexOf('/');
  if (slashIdx === -1) throw new Error('invalid id');
  return id.substring(0, slashIdx);
}

function deriveChildren(allCards: Card[], parentId: string): string[] {
  return allCards
    .filter(c => deriveParent(c.id) === parentId)
    .map(c => c.id);
}
```

### 树形视图的嵌套结构

尽管 YAML 存储是扁平的，树形管理界面展示时需要拼接为嵌套结构：

```yaml
# 存储（扁平）
- { id: root/1, title: 机器学习 }
- { id: root/1/1, title: 监督学习 }
- { id: root/1/2, title: 无监督学习 }

# 渲染（嵌套，由算法转换）
root/
  └── root/1  机器学习
        ├── root/1/1  监督学习
        └── root/1/2  无监督学习
```

### 层级路径规则

- `root` — 根目录标识，非卡片节点，不参与匹配和导航
- `root/1` — 一级卡片
- `root/1/2` — 二级卡片（root/1 的子卡片）
- `root/1/2/1` — 三级卡片，以此类推

### tag 的两种语义

| tag 值 | 场景 | 说明 |
|--------|------|------|
| `"决策分支"` | 分支决策（i叉决策树） | 子卡片是并列的选择分支，用户在导航中需从多项中择一 |
| `"层级分类"` | 上下级包含关系 | 子卡片是父卡片的下位概念，表达"属于/包含"关系 |

### 自动生成规则

1. **语料库 → 标题/描述**：系统通过 LLM 或 NLP 摘要从 `corpus` 列表提取关键信息，填充 `title` 和 `description`。
2. **子节点 → 父节点**：当父卡片 `corpus` 为空时，可聚合子卡片的 `title` 和 `description`，反向生成父卡片内容。
3. 自动生成时 `metadata.generated` 设为 `true`，后续可手动编辑覆盖。

---

## 二、导航节点（Navigation Node）

导航节点是导航路径中的"站点"（waypoint），连接认知卡片与导航方向。**不使用 `path` 命名**。

### YAML Schema

```yaml
navigation_nodes:
  - id: node-ml-foundation
    label: 机器学习基础
    description: 涵盖监督学习、无监督学习与强化学习的核心概念与算法基础。
    bound_cards:
      - root/1
      - root/3
    browse_history:
      - from: node-probability
        count: 3
        last_at: 2026-07-24T09:30:00Z
      - from: node-linear-algebra
        count: 5
        last_at: 2026-07-24T08:15:00Z
    next_nodes:
      - target_id: node-supervised
        preset_weight: 0.75
        browse_weight: 0.42
        connection_type: preset
      - target_id: node-unsupervised
        preset_weight: 0.60
        browse_weight: 0.30
        connection_type: preset
      - target_id: node-reinforcement
        preset_weight: 0.40
        browse_weight: 0.25
        connection_type: preset
    priority_config:
      mode: mixed
      preset_priority: 0
      browse_priority: 1
      user_overrides: []
    metadata:
      created_at: 2026-07-20T14:00:00Z
      updated_at: 2026-07-24T09:30:00Z
```

### 字段定义

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | 是 | 导航节点唯一标识，如 `node-ml-foundation`。 |
| `label` | string | 是 | 节点显示名称。 |
| `description` | string | 否 | 节点描述信息。 |
| `bound_cards` | string[] | 否 | 绑定的认知卡片 id 列表。用户搜索匹配时通过卡片找到此节点。 |
| `browse_history` | array | 否 | 浏览记录详情，记录从哪些节点跳转过来及频次。 |
| `next_nodes` | array | 是 | 出向连接列表，定义当前节点可以跳转到的下一节点及权重。 |
| `priority_config` | object | 否 | 权重优先级配置（见下文）。 |
| `metadata` | object | 否 | 元数据。 |

### next_nodes 子字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `target_id` | string | 是 | 目标导航节点 id。 |
| `preset_weight` | number | 是 | 此连接的预设权重。 |
| `browse_weight` | number | 否 | 此连接的浏览行为权重。 |
| `connection_type` | enum | 是 | `preset`（预设连接）、`user_added`（用户手动建立）、`browse_derived`（浏览行为自动生成）。 |

### 权重优先级配置

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `mode` | enum | 是 | `mixed`（混合模式，合并预设+浏览）、`user_only`（纯用户模式，仅用预设）。 |
| `preset_priority` | number | 是 | 预设权重在总权重序列中的起始序号（默认 0，优先级最高）。 |
| `browse_priority` | number | 否 | 浏览权重在总权重序列中的起始序号（默认接在预设之后）。 |
| `user_overrides` | array | 否 | 用户手动覆盖特定连接的权重。优先级高于 preset_priority 和 browse_priority。每项：`{target_id, override_weight}`。 |

**权重合成算法**（`mode === "mixed"` 时）：

1. 从 `user_overrides` 中查找指定 `target_id` 的覆盖权重，如果有则直接使用。
2. 若无覆盖，则按 `preset_priority` 和 `browse_priority` 拼接：
   - 首先按 `preset_weight` 对 `next_nodes` 降序排列
   - 然后在序列尾部按 `browse_weight` 对 `next_nodes` 降序排列并拼接
   - 最终生成带序号的完整权重序列：`[{target_id, seq: 0}, {target_id, seq: 1}, ...]`

---

## 三、导航会话（Navigation Session）

用于在视图间传递状态的运行时数据结构。支持**多途径点路线规划**。

```yaml
current_node_id: node-ml-foundation
search_query: 监督学习
matched_card_id: root/1/1
selected_node_id: node-supervised
route_plan:
  waypoints:                          # 途径点序列（有序列表）
    - node-ml-foundation
    - node-supervised
    - node-deep-learning
  total_weight: 0.85
  mode: mixed
  nav_mode: overview                  # 导航视图模式: overview(全览) | station(逐站)
browse_wp_index: 0                    # 当前浏览的途径点索引
browse_index: 0
browse_direction: up
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `current_node_id` | string | 当前所在导航节点 id（route_plan 的锚点）。 |
| `search_query` | string | 用户在搜索视图输入的搜索文本。 |
| `matched_card_id` | string | 搜索匹配到的认知卡片 id。 |
| `selected_node_id` | string | 用户在搜索视图中选定的导航节点 id（进入 NavView 的入口）。 |
| `route_plan.waypoints` | string[] | **途径点序列**，有序的导航节点 id 列表。用户可在 NavView 中点击多个节点添加为途径点。 |
| `route_plan.total_weight` | number | 整体路线的固定加权总和（仅用于展示，不参与 D3 渲染）。 |
| `route_plan.mode` | enum | 权重模式：`mixed`、`user_only`。 |
| `route_plan.nav_mode` | enum | NavView 当前显示模式：`overview`（力导向全览图）、`station`（DAG 逐站流）。 |
| `browse_wp_index` | number | 内容浏览视图中当前所在的途径点序号。 |
| `browse_index` | number | 内容浏览视图中当前途径点下的卡片序号。 |
| `browse_direction` | enum | 内容浏览滑动方向：`up`（上滑为下一节点）、`down`（下滑为下一节点）。 |

---

## 四、界面间的数据流

```
┌─────────────────────────────────────────────────────────────────────┐
│                       搜索视图 (Search View)                        │
│  输入搜索 → 匹配认知卡片(card.title/card.description/card.corpus)    │
│  → 选中卡片 → 查询绑定的导航节点(card.bound_nodes)                  │
│  → 选中导航节点 → 点击「进入导航」                                  │
│  → 传递: { matched_card_id, selected_node_id, search_query }       │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       导航视图 (Nav View)                            │
│  模式: 全览(力导向图) / 逐站(DAG流)                                  │
│  点击画布节点 → 下拉面板 → 添加为途径点                              │
│  途径点序列: [node-A] → [node-B] → [node-C]                         │
│  → 点击「开始浏览」→ 传递 waypoints[] + nav_mode                    │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       内容浏览 (Browse View)                         │
│  按途径点顺序加载绑定卡片: 第 X/Y 站                                  │
│  data = waypoints[wpIndex].bound_cards → 卡片堆叠 → 上下滑动切换     │
│  → 「下一站」→ wpIndex+1 → 加载下一途径点卡片                       │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                       树形管理 (Tree View)                           │
│  独立于导航流程，负责认知卡片的 CRUD 操作                            │
│  扁平 YAML 存储 → 算法自动推导 parent/children → 拼接为嵌套树        │
│  root 仅为根目录标识，不是卡片节点                                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 五、设计原则

1. **认知卡片是知识单元，导航节点是航线坐标** — 卡片负责"是什么"，节点负责"走向哪里"。
2. **数据以 YAML 文件为中心** — 所有数据以扁平列表存储在本地 `.yaml` 文件，支持手动编辑和版本控制。
3. **父子关系由算法推导** — 存储不含 `parent`/`children` 字段，运行时从 `id` 层级路径自动计算，避免数据冗余和不一致。
4. **权重可溯源** — 每个权重都明确标记来源（预设/浏览/用户覆盖），合成算法透明。
5. **无 `path` 命名** — 导航节点 id 使用 `node-` 前缀，认知卡片使用 `root/` 层级路径，语义清晰互不混淆。
