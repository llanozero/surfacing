# 导航图多文件架构：YAML 目录 + 编号映射 + 跨图跳转

## 版本

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| 1.0 | 2026-07-26 | — | 初始规范；新增第十二章"图即节点：钻入/钻出" |
| 1.1 | 2026-07-28 | — | 重构第十二章 YAML 规范为 type/subgraph_config；新增第十三章 Top 多图加载与状态模型 |

---

## 一、动机

### 1.1 现状问题

当前所有导航节点和认知卡片存放在单个 `backend/data.yaml` 文件中，存在以下问题：

| 问题 | 说明 |
|------|------|
| 单文件膨胀 | 所有主题混在一个 YAML，随着内容增长，文件变大难以维护 |
| 无隔离 | 机器学习、心理学、编程等主题的节点和卡片 ID 命名空间共享，容易冲突 |
| 不可拆分 | 无法按主题独立导入/导出/迁移一份导航图 |
| 无跨图引用 | 无法在不同的知识体系之间建立关联（如"机器学习→贝叶斯定理"引用"数学"图中的概率论节点） |

### 1.2 目标

1. **多 YAML 文件目录**：每个 `.yaml` 文件对应一个独立的导航图（graph），按主题拆分
2. **编号映射**：每个导航图有一个全局唯一编号（graph ID），提供快速查找
3. **跨图跳转**：节点可以引用其他导航图中的节点作为出向连接
4. **跨图绑定**：节点可以绑定其他导航图中的认知卡片

---

## 二、核心概念

### 2.1 导航图（Graph）

一个导航图是一个 YAML 文件，包含一组相关的导航节点和认知卡片。

```
导航图 = 1 个 YAML 文件 = 一组 navigation_nodes + cognitive_cards
```

### 2.2 图编号（Graph ID）

每个导航图有唯一的 `graph_id`，既是文件名前缀，也是跨图引用的命名空间前缀。

```
graph_id 格式: g{序号}  例如: g1, g2, g3
```

### 2.3 跨图引用（Cross-Graph Reference）

用 `graph_id::resource_id` 格式引用其他图中的节点或卡片。

```
跨图节点引用: g2::node-probability-theory
跨图卡片引用: g2::math/probability/bayes
```

本地引用（同图内）可以省略 graph_id 前缀，兼容现有格式：

```
同图节点引用: node-ml-foundation        （等价于 g1::node-ml-foundation）
同图卡片引用: root/1                     （等价于 g1::root/1）
```

---

## 三、YAML 目录结构

### 3.1 目录布局

```
backend/
├── graphs/                          # 导航图 YAML 目录（新建）
│   ├── _manifest.yaml               # 图清单文件
│   ├── g1-ml.yaml                   # 图 1：机器学习
│   ├── g2-math.yaml                 # 图 2：数学基础
│   ├── g3-psychology.yaml           # 图 3：心理学
│   └── ...
├── data.yaml                        # [废弃] 迁移后保留为兼容入口
└── seed.yaml                        # [废弃] 同上
```

### 3.2 清单文件（_manifest.yaml）

```yaml
# 导航图清单：编号 → 文件映射 + 元信息
graphs:
  - graph_id: g1
    file: g1-ml.yaml
    label: 机器学习
    description: 机器学习核心概念与算法导航图
    created_at: '2026-07-20T00:00:00Z'
    node_count: 17
    card_count: 35

  - graph_id: g2
    file: g2-math.yaml
    label: 数学基础
    description: 概率论、线性代数、微积分等数学基础知识
    created_at: '2026-07-25T00:00:00Z'
    node_count: 12
    card_count: 20

  - graph_id: g3
    file: g3-psychology.yaml
    label: 心理学
    description: 认知心理学与思维模型
    created_at: '2026-07-26T00:00:00Z'
    node_count: 8
    card_count: 18

# 图序号计数器（新建图时自动递增）
next_graph_number: 4
```

### 3.3 单图 YAML 格式

与现有 YAML 格式基本一致，新增 `graph_id` 字段：

```yaml
# g1-ml.yaml — 机器学习导航图
graph_id: g1
graph_label: 机器学习
graph_description: 机器学习核心概念与算法导航图
entry_node_id: node-ml-foundation  # 本图默认入口节点

cognitive_cards:
  - id: root/1
    title: 机器学习
    type: folder
    tag: 层级分类
    description: 机器学习的核心概念体系
    corpus:
      - 语料内容...
    bound_nodes:
      - node-ml-foundation
      - g2::node-probability-theory         # ← 跨图绑定：引用 g2 中的节点
    metadata:
      created_at: '2026-07-20T00:00:00Z'

navigation_nodes:
  - id: node-ml-foundation
    label: 机器学习基础
    description: 机器学习的基本概念...
    bound_cards:
      - root/1
      - root/1/1
      - g2::math/probability/bayes          # ← 跨图绑定卡片：引用 g2 中的卡片
    next_nodes:
      - target_id: node-supervised
        preset_weight: 0.75
        browse_weight: 0.42
        connection_type: preset
      - target_id: g2::node-probability-theory  # ← 跨图跳转：引用 g2 中的节点
        preset_weight: 0.60
        browse_weight: 0.00
        connection_type: preset
    priority_config:
      mode: mixed
      preset_priority: 0
      browse_priority: 4
```

---

## 四、编号映射

### 4.1 编号规则

| 元素 | 格式 | 示例 | 说明 |
|------|------|------|------|
| 图 ID | `g{序号}` | `g1`, `g2` | 严格递增，不可重用（即使删除图也不回收编号） |
| 本地引用 | `{id}` | `node-ml` | 不带前缀，指当前图内的资源 |
| 跨图引用 | `{graph_id}::{id}` | `g2::node-prob` | 双冒号分隔，graph_id 后跟资源 ID |
| 跨图卡片绑定 | `{graph_id}::{card_id}` | `g2::root/1` | 卡片 ID 可能含 `/`，不影响解析（双冒号是唯一分隔符） |

### 4.2 映射解析

```python
def resolve_graph_ref(ref: str, default_graph: str) -> tuple[str, str]:
    """
    解析跨图引用，返回 (graph_id, resource_id)。
    不带前缀的引用默认属于当前图。
    """
    if '::' in ref:
        graph_id, resource_id = ref.split('::', 1)
        return graph_id, resource_id
    return default_graph, ref
```

### 4.3 ID 命名空间

每个图内的资源 ID 在自己的图内唯一。不同图的资源 ID 可以重复（因为有 graph_id 前缀区分）。

```
g1::node-intro   ≠   g2::node-intro   （两个不同的节点）
```

---

## 五、跨图跳转与绑定

### 5.1 跨图跳转（Cross-Graph Navigation Jump）

节点 A（在图 g1 中）可以跳转到节点 B（在图 g2 中）：

```yaml
# 在 g1 的某个节点的 next_nodes 中：
next_nodes:
  - target_id: g2::node-probability-theory
    preset_weight: 0.60
    browse_weight: 0.00
    connection_type: preset
```

**前端行为**：
- 导航视图中，跨图连接用不同样式标记（如虚线边框 + graph label 前缀）
- 点击跨图节点时，如果用户当前在该节点的原始图中 → 直接跳转
- 如果用户在另一个图中 → 切换到目标图并定位到该节点

### 5.2 跨图卡片绑定（Cross-Graph Card Binding）

节点（在图 g1 中）可以绑定其他图的卡片：

```yaml
# 在 g1 的某个节点的 bound_cards 中：
bound_cards:
  - root/1
  - g2::math/probability/bayes
```

**前端行为**：
- 浏览视图加载卡片时，先在本图查找，再按 graph_id 前缀到目标图查找
- 跨图卡片显示时标注来源图（如 `📎 g2 数学基础`）

### 5.3 解析跨图引用的完整算法

```python
def resolve_card_references(bound_cards: list[str], all_graphs: dict[str, Graph]) -> list[Card]:
    """解析节点绑定的所有卡片（包括跨图），返回完整卡片对象列表。"""
    result = []
    for ref in bound_cards:
        if '::' in ref:
            graph_id, card_id = ref.split('::', 1)
            graph = all_graphs.get(graph_id)
            if graph:
                card = graph.find_card(card_id)
                if card:
                    result.append(card)
        else:
            # 本地引用，默认在当前图查找
            card = current_graph.find_card(ref)
            if card:
                result.append(card)
    return result
```

---

## 六、后端 API 变更

### 6.1 新增路由：`routers/graphs.py`

前缀: `/api/graphs`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/graphs` | 获取所有图的清单（来自 `_manifest.yaml`） |
| GET | `/api/graphs/{graph_id}` | 获取指定图的完整数据（节点 + 卡片） |
| GET | `/api/graphs/{graph_id}/nodes` | 获取指定图的全部节点 |
| GET | `/api/graphs/{graph_id}/cards` | 获取指定图的全部卡片 |
| GET | `/api/graphs/{graph_id}/nodes/{node_id}` | 获取指定图的单个节点 |
| GET | `/api/graphs/{graph_id}/edges` | 获取指定图的全部边（含跨图边，保留 `graph_id::` 前缀） |
| POST | `/api/graphs` | 新建一个空白的图 YAML 文件 |
| DELETE | `/api/graphs/{graph_id}` | 删除指定图（物理删除 YAML 文件，更新 manifest） |

#### 获取单图

```
GET /api/graphs/g1

Response 200:
{
  "graph_id": "g1",
  "graph_label": "机器学习",
  "navigation_nodes": [ ... ],
  "cognitive_cards": [ ... ]
}
```

#### 获取清单

```
GET /api/graphs

Response 200:
{
  "graphs": [
    {
      "graph_id": "g1",
      "file": "g1-ml.yaml",
      "label": "机器学习",
      "node_count": 17,
      "card_count": 35
    }
  ]
}
```

### 6.2 修改现有路由

#### 全局视图（兼容）

保留现有 `/api/nodes`、`/api/cards`、`/api/graph/edges` 作为聚合视图——从所有图中汇总数据：

```
GET /api/nodes?graph=g1          → 仅 g1 的节点（新增参数）
GET /api/nodes                    → 所有图的节点（去掉 graph_id 前缀后返回）
GET /api/nodes?graph=g1          → 仅 g1 的节点
GET /api/cards?graph=g1          → 仅 g1 的卡片
GET /api/graph/edges?graph=g1    → 仅 g1 的边（跨图边保留前缀）
```

#### 跨图资源解析

```
GET /api/graphs/resolve?ref=g2::node-probability-theory
→ 返回 g2 中的该节点的完整数据

GET /api/graphs/resolve-batch
  body: { "refs": ["g2::node-prob", "g2::root/1"] }
→ 返回两个资源的完整数据数组
```

### 6.3 修改 Store

`backend/app/store.py` 改造：

```python
class DataStore:
    def __init__(self, graphs_dir: str = "graphs"):
        self.graphs_dir = Path(graphs_dir)
        self.manifest: dict = {}
        self.graphs: dict[str, Graph] = {}  # graph_id → Graph
        self.load_all()

    def load_all(self):
        """加载 _manifest.yaml 和所有图 YAML 文件"""
        manifest_path = self.graphs_dir / "_manifest.yaml"
        if manifest_path.exists():
            self.manifest = yaml.safe_load(manifest_path.read_text(encoding='utf-8'))
        else:
            self.manifest = {"graphs": [], "next_graph_number": 1}

        for g in self.manifest["graphs"]:
            gid = g["graph_id"]
            filepath = self.graphs_dir / g["file"]
            self.graphs[gid] = Graph.from_yaml(filepath)

    def create_graph(self, label: str, description: str = "") -> str:
        """新建一个空白图，返回新 graph_id"""
        ...

    def delete_graph(self, graph_id: str):
        """删除图文件并从 manifest 移除"""
        ...

    # ── 聚合查询 ──
    def all_nodes(self, graph_id: str | None = None) -> list[dict]:
        ...

    def all_cards(self, graph_id: str | None = None) -> list[dict]:
        ...
```

---

## 七、前端变更

### 7.1 新增配置 / Store

**`src/config/graphs.ts`** — 当前活动图配置：

```typescript
interface GraphConfig {
  activeGraphId: string  // 当前活动图 ID，默认 'g1'
}

function getActiveGraphId(): string { ... }
function setActiveGraphId(id: string): void { ... }
```

**`src/store/graphStore.ts`** — 图管理与切换：

```typescript
interface GraphStore {
  graphs: GraphMeta[]       // 所有图的元信息列表
  activeGraphId: string     // 当前活动图
  setActiveGraph: (id: string) => void
  fetchGraphs: () => Promise<void>  // 从 /api/graphs 拉取清单
}
```

### 7.2 API 层变更

`src/api/index.ts` 中所有路由调用默认传入 `?graph={activeGraphId}` 参数。

跨图资源获取新增：

```typescript
async getCrossGraphNode(ref: string): Promise<NavNode> {
  return this.adapter.get(`/api/graphs/resolve?ref=${encodeURIComponent(ref)}`)
}
```

### 7.3 跨图节点显示

在导航视图、浏览视图中，跨图引用的节点/卡片需标注来源：

```
┌──────────────────────────────────┐
│  概率论基础                       │
│  📎 来自 g2 数学基础               │  ← 跨图来源标注
│  基本概念...                      │
│  [🔊]  [跳转到所属图]              │
└──────────────────────────────────┘
```

全览视图中跨图连接用虚线样式区分：

```
  ● 机器学习基础 ────→ ● 监督学习          （实线，同图）
   │
   └ ─ ─ ─ ─ ─ ─ → ● 概率论基础 [g2]    （虚线 + 标签，跨图）
```

### 7.4 图切换 UI

在 StatusBar 增加图选择器（Dropdown）：

```
┌──────────────────────────────────────────┐
│  12:30  认知导航  [图: 机器学习 ▾]    ⚙   │
│                   ├ 机器学习 (g1)         │
│                   ├ 数学基础 (g2)    ←    │
│                   └ 心理学 (g3)           │
└──────────────────────────────────────────┘
```

切换图时：
1. 后端重新加载对应图的节点列表
2. 全览视图重新渲染当前图的所有节点
3. 保留跨图引用节点的可点击性（跳转时自动切图）

---

## 八、迁移计划

### 8.1 现有数据迁移

1. 将现有 `backend/data.yaml` 中的 `cognitive_cards` 和 `navigation_nodes` 提取为 `g1-ml.yaml`
2. 生成 `_manifest.yaml`，初始只有 `g1`
3. `backend/data.yaml` 保留为向后兼容的入口（启动时自动迁移到 g1）

### 8.2 迁移脚本

```python
# migrate_to_graphs.py
import yaml
from pathlib import Path

data = yaml.safe_load(Path("data.yaml").read_text(encoding='utf-8'))

g1 = {
    "graph_id": "g1",
    "graph_label": "机器学习",
    "graph_description": "从现有 data.yaml 迁移",
    "cognitive_cards": data["cognitive_cards"],
    "navigation_nodes": data["navigation_nodes"],
}

Path("graphs/g1-ml.yaml").write_text(
    yaml.safe_dump(g1, allow_unicode=True, sort_keys=False),
    encoding='utf-8',
)

manifest = {
    "graphs": [{
        "graph_id": "g1",
        "file": "g1-ml.yaml",
        "label": "机器学习",
        "description": "从现有 data.yaml 迁移",
        "node_count": len(g1["navigation_nodes"]),
        "card_count": len(g1["cognitive_cards"]),
    }],
    "next_graph_number": 2,
}
Path("graphs/_manifest.yaml").write_text(
    yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False),
    encoding='utf-8',
)
```

### 8.3 启动兼容

`store.py` 启动时：
1. 如果 `graphs/_manifest.yaml` 存在 → 加载多图模式
2. 如果只有 `data.yaml` → 自动执行迁移脚本，然后加载多图模式

---

## 九、验收标准

- [ ] 后端可加载 `graphs/_manifest.yaml` 中列出的所有图 YAML 文件
- [ ] `_manifest.yaml` 中的 `graph_id` → 文件名映射正确
- [ ] 跨图节点引用 `g2::node-xxx` 格式正确解析和显示
- [ ] 跨图卡片绑定 `g2::card-id` 格式在浏览视图中正确加载
- [ ] 跨图连接在全览视图中以虚线样式显示并标注来源图
- [ ] 图切换器可切换活动图，导航视图随切换重新渲染
- [ ] `GET /api/graphs` 返回所有图的元信息列表
- [ ] `DELETE /api/graphs/{graph_id}` 物理删除文件并更新 manifest
- [ ] 旧 `data.yaml` 在启动时自动迁移为新图格式
- [ ] 同图内引用（不带前缀）保持正常工作
- [ ] 编译零错误

---

## 十、代码变更清单

### 10.1 后端（5 个文件）

| 文件 | 变更 |
|------|------|
| `backend/graphs/_manifest.yaml` | **新建** — 图清单 |
| `backend/graphs/g1-ml.yaml` | **新建** — 第一个导航图（迁移自 data.yaml） |
| `backend/app/store.py` | 改造：支持多图加载、聚合查询、迁移 |
| `backend/app/routers/graphs.py` | **新建** — 图管理 API |
| `backend/app/main.py` | 注册 graphs router |

### 10.2 前端（8 个文件）

| 文件 | 变更 |
|------|------|
| `src/config/graphs.ts` | **新建** — 活动图配置 |
| `src/store/graphStore.ts` | **新建** — 图管理状态 |
| `src/api/index.ts` | 所有路由默认带 `?graph=xxx` 参数 |
| `src/components/layout/StatusBar.tsx` | 新增图切换 Dropdown |
| `src/components/views/NavView.tsx` | 跨图连接虚线样式 + 来源图标签 |
| `src/components/panel/DropDownPanel.tsx` | 跨图节点显示来源标注 |
| `src/components/cards/BrowseCard.tsx` | 跨图卡片显示来源标注 |
| `src/components/views/FreeBrowseView.tsx` | 跨图节点前驱/后继显示来源标注 |

---

## 十一、边界情况

| 场景 | 行为 |
|------|------|
| 引用的图不存在 | Toast 提示"目标图已删除"；降级为显示节点 ID 文本，不渲染链接 |
| 引用的图资源 ID 在目标图中不存在 | Toast 提示"节点/卡片已不存在"；同级降级 |
| 用户删除一个图 | 扫描所有其他图的引用，将失效引用标记为 `external_missing`；前端显示为灰色 |
| 两个图各自定义了同名节点 ID | 正确隔离：`g1::node-intro` 和 `g2::node-intro` 是两个独立节点 |
| 跨图引用形成循环 | 允许循环（用户可自由跳转），不做检测或阻断 |
| manifest 文件损坏或不存在 | 回退到单文件模式，加载 `data.yaml`（向后兼容） |

---

## 十二、图即节点：导航图的钻入/钻出

### 12.1 动机

在跨图引用的基础上，进一步将"一整个导航图"抽象为一个特殊导航节点（子图节点）。它允许：

- **分层导航**：父图中的节点点击后"钻入"子图内部
- **无固定出口**：子图内没有预设的出口节点，浏览到死胡同时自动钻出
- **复用任意图**：同一个图可以作为不同父图节点的入口（多对多）

典型场景：一个"数学基础"导航图，同时被"机器学习"和"计算机视觉"两个图的特殊节点引用，用户从不同入口钻入后看到的是同一个数学图的不同起始节点。

### 12.2 子图节点（Subgraph Node）

节点通过 `type` 字段区分普通节点与子图节点：

```typescript
interface NavNode {
  id: string
  label: string
  type: 'normal' | 'subgraph'   // 节点类型
  properties?: {
    panel?: string               // 关联的面板组件名
  }
  description: string
  bound_cards?: string[]
  next_nodes: NextNodeRef[]      // 普通节点的出向 / 子图节点钻出后的后继
  // ...

  /** ── 子图节点专用配置 ── */
  subgraph_config?: {
    target_graph_id: string      // 指向的目标图 ID，如 'g2'
    target_entry_node: string    // 在目标图中的入口节点 ID，如 'node-probability-theory'
  }
}
```

### 12.3 YAML 表示

子图节点在 YAML 中的写法：

```yaml
# 在 g1-ml.yaml 中
navigation_nodes:
  - id: node-math-foundation
    label: 数学基础导航图
    type: subgraph                     # ← 标记为子图节点
    description: 钻入概率论、线性代数、微积分等数学基础知识体系
    subgraph_config:
      target_graph_id: g2             # 指向目标图
      target_entry_node: node-probability-theory  # 入口节点
    properties:
      panel: CheckoutPanel
    # next_nodes 只在钻出后被激活——表示退出子图后的流向
    next_nodes:
      - target_id: node-deep-learning
        preset_weight: 0.70
        browse_weight: 0.00
        connection_type: preset
```

目标图 `g2-math.yaml` 无需做任何改造，它本身就是独立的导航图：

```yaml
# g2-math.yaml（完全独立，不感知自己被引用）
graph_id: g2
graph_label: 数学基础
entry_node_id: node-probability-theory
navigation_nodes:
  - id: node-probability-theory
    label: 概率论基础
    type: normal
    next_nodes:
      - target_id: node-bayes-theorem
        preset_weight: 0.80
        browse_weight: 0.00
        connection_type: preset
  - id: node-bayes-theorem
    label: 贝叶斯定理
    type: normal
    next_nodes: []     # ← 钻出触发点：无后继 → 自动钻出
```

### 12.4 钻入/钻出语义

#### 钻入（Drill In）

用户在主图（g1）中看到"数学基础导航图"节点，点击后：

```
[主图 g1]                                          [子图 g2]
                                                              ● node-probability-theory（入口）
  ● 机器学习基础                                             /  \
   │                                                        /    \
   │   [点击]                                                 ● binom   ● bayes
   ▼                                                        │
  ● 数学基础导航图 (target=g2, entry=node-probability)         │
    │                                                        ● laplace（无后继 → 自动钻出）
   │ next_nodes=[↓ deep-learning]                           │
   ▼                                                         │
  ● 深度学习                                                │
                                                              │
                                                              ▼
                                                [钻出回到主图 g1]
                                                      ● 深度学习
```

**钻入过程**：
1. 用户点击子图节点（`type === 'subgraph'`），面板显示 **[钻入子图]** 按钮
2. 将 `subgraph_config.target_graph_id` 压入路径栈
3. 面包屑追加该 ID：`top / g2`
4. 前端切换到目标图（g2），定位到入口节点（`node-probability-theory`）
5. 正常浏览子图内的节点和卡片

#### 钻出（Drill Out）

当用户在子图内浏览时，如果到达一个没有 `next_nodes` 的节点（出度为 0）：

1. 面板显示 **[钻出子图]** 按钮
2. 自动钻出回父图，定位到**子图节点的第一个 `next_nodes` 后继节点**
3. 面包屑路径回退一层：`top`
4. 如果子图节点本身也没有后继 → 停留在父图的子图节点位置，Toast 提示"已钻出子图，当前节点无后继"

```
[子图 g2 内部死胡同]            →        [自动钻出回主图 g1]

  ● laplace（next_nodes=[]）             ● 深度学习（子图节点之后的第一个后继）
```

**钻出条件**（任意满足其一即可钻出）：
1. 当前节点 `next_nodes` 为空数组（出度为 0）
2. 用户手动点击"钻出"按钮
3. 后端返回的浏览序列到达终点

#### 多级钻入（嵌套）

子图节点可以嵌套——g2 中的节点也可以引用 g3 作为子图：

```
g1 → [子图节点→g2] → g2 → [子图节点→g3] → g3
```

钻入路径显示（基于 graph_id）：

```
top / g1 / g2 / g3
```

或携带图 label：

```
top / 机器学习 / 数学基础 / 认知心理学
```

钻出时逐级返回：

```
g3（无后继）→ 钻出到 g2 → 继续浏览 g2 → g2 也无后继 → 钻出到 g1 → 回到 top 顶层
```

### 12.5 子图节点与跨图引用的关系

| 特性 | 跨图引用（§五） | 子图节点（§十二） |
|------|----------------|-------------------|
| 引用范围 | 单个节点/卡片 | 整个导航图 |
| 是否需要目标图改造 | 否 | 否（目标图完全独立） |
| 入口点 | 固定为被引用的节点 | 可指定 `entry_node_id` |
| 浏览结束后 | 留在目标图 | 自动钻出回父图 |
| 出口点 | 不适用 | 子图节点的 `next_nodes` |
| 典型场景 | 临时跳到另一个节点 | 分层、分主题的深度探索 |

**两者可以组合使用**：
- 在子图内部，节点仍然可以使用 `g2::xxx` 跨图引用其他图的资源
- 钻出后，父图节点可以使用 `g1::xxx` 引用还留在子图中的资源

### 12.6 前端实现

#### 钻入路径指示器

StatusBar 在钻入状态下显示路径面包屑：

```
┌──────────────────────────────────────────────┐
│  top / g1 机器学习 / g2 数学基础     [钻出]  │
└──────────────────────────────────────────────┘
```

- 默认顶层为 `top`，顶层显示的是用户通过画布多选框加载的导航图集合
- 路径中的每一步可点击（跳转到对应图）
- 右侧"钻出"按钮可手动触发钻出

#### 子图节点在父图中的渲染

```
  ● 机器学习基础
   │
   ▼
  ╔════════════════════╗     ← 用带边框的"卡片式"节点外观
  ║  📂 数学基础导航图   ║       区分普通节点
  ║  钻入概率论、线性代数 ║
  ║  [🔊] [🔽 钻入]   ║
  ╚════════════════════╝
   │
   ▼
  ● 深度学习
```

#### 钻出检测

在浏览序列中，当用户 `nextWaypoint()` 或 `prevCard()` 触发时，检查当前节点是否有 `next_nodes`。如果为空且当前在子图内部 → 触发钻出。

```typescript
// 浏览状态机中增加钻出检测
function checkDrillOut(currentNode: NavNode, drillStack: DrillStack): boolean {
  if (drillStack.length === 0) return false        // 不在子图内
  if (currentNode.next_nodes.length > 0) return false // 还有后继

  // 无后继 → 钻出
  const parent = drillStack.pop()!
  switchGraph(parent.graphId)
  setCurrentNode(parent.exitNodeId)
  return true
}
```

### 12.7 钻入/钻出状态管理

**`src/store/drillStore.ts`** — 钻入栈管理：

```typescript
interface DrillStackItem {
  parentGraphId: string       // 钻入前的图
  parentNodeId: string        // 钻入前的子图节点 ID（钻出后回到此节点）
  subGraphId: string          // 钻入的目标图
  entryNodeId: string         // 目标图中的入口节点
}

interface BreadcrumbItem {
  label: string               // 显示名称，如 "top" / "g1" / "机器学习"
  graphId: string             // 图 ID
  nodeId?: string             // 当前聚焦的节点 ID（可选）
}

interface DrillStore {
  stack: DrillStackItem[]     // 钻入栈（支持多级嵌套）
  breadcrumb: BreadcrumbItem[] // 面包屑路径，默认 ["top"]
  push: (item: DrillStackItem) => void
  pop: () => DrillStackItem | null
  peek: () => DrillStackItem | null
  clear: () => void
  isInDrill: () => boolean
}
```

### 12.8 后端支持

后端新增以下查询能力：

```
# 查询一个节点是否是子图节点（用于前端的特殊渲染）
GET /api/graphs/{graph_id}/nodes/{node_id}
→ 返回完整节点数据，包含 sub_graph_id / entry_node_id（如存在）

# 给定一个图的所有子图节点（用于全览视图特殊标记）
GET /api/graphs/{graph_id}/subgraph-nodes
→ 返回该图中所有 sub_graph_id 不为空的节点列表

# 批量解析钻入路径（用于构建面包屑导航）
POST /api/graphs/resolve-drill-path
  body: { "graph_ids": ["g1", "g2"] }
→ 返回图的 label 和入口节点 label
```

### 12.9 验收标准

- [ ] 子图节点在 YAML 中定义 `sub_graph_id` + `entry_node_id` 后，前端识别为特殊节点
- [ ] 点击子图节点切换目标图并定位到入口节点
- [ ] 子图内节点无后继时自动钻出回父图
- [ ] 面包屑导航显示完整钻入路径
- [ ] 支持多级嵌套钻入（图A→图B→图C）
- [ ] 目标图无需任何额外配置（完全独立）
- [ ] 钻出后继由子图节点的 `next_nodes` 决定
- [ ] 父图全览视图中子图节点以特殊样式渲染

---

## 十三、顶层 Top 多图加载与导航状态模型

### 13.1 Top 顶层语义

顶层 `top` 是面包屑的根路径，表示用户位于画布的最外层——没有钻入任何子图。顶层显示的导航节点，取决于用户通过**多选框**选择的导航图集合。

### 13.2 YAML 数据规范（完整示例）

每个 YAML 文件代表一个独立图元（Graph Schema）：

```yaml
# nav_graph_aaa.yaml
graph_id: "aaa_id"
name: "主流程导航图"
version: "1.0.0"
entry_node_id: "node_1"     # 本图默认入口节点

# 节点定义
nodes:
  - id: "node_1"
    label: "用户登录"
    type: "normal"           # 普通导航节点
    properties:
      panel: "LoginPanel"

  - id: "node_2"
    label: "商品结算"
    type: "subgraph"         # 子图节点
    subgraph_config:
      target_graph_id: "bbb_id"       # 关联的子图 YAML 的 graph_id
      target_entry_node: "sub_node_1" # 钻入时跳转的子图入口节点
    properties:
      panel: "CheckoutPanel"

# 连线定义（支持有向有环）
edges:
  - id: "edge_1_2"
    source: "node_1"
    target: "node_2"
    label: "登录成功"

  - id: "edge_2_1"
    source: "node_2"
    target: "node_1"
    label: "取消结算（有环）"
```

### 13.3 多选框加载机制

顶层 `top` 显示的导航节点，由多选框控制：

- **全选** → 加载所有导航图 YAML，在同一画布中渲染所有图的节点和边
- **勾选多个** → 加载选中的多个 YAML 到同一画布
- **勾选一个** → 仅加载该图

#### 命名空间化（Namespacing）

为防止不同 YAML 中的 `id` 冲突，加载时对全局数据做命名空间化：

| 机制 | 说明 |
|------|------|
| **全局节点唯一键** | `{graph_id}::{node_id}`（例如 `aaa_id::node_1`） |
| **跨图连线渲染** | 当 `node.type === 'subgraph'` 时，画布自动绘制虚线连接当前子图节点与子图的入口节点（`bbb_id::sub_node_1`） |
| **画布分组（Group/Cluster）** | 在渲染引擎中，将同一个 YAML 内的节点包裹在一个 Group 中，展示为子图容器 |

#### 状态机：钻入/钻出

```
用户勾选 [g1, g2] → top 画布渲染 g1+g2 全部节点

用户点击 g1 中的子图节点 → drillIn()
  breadcrumb: ["top", "g1"] → ["top", "g1", "bbb_id"]
  画布切换到子图 bbb_id 的单图模式

用户到达无后继节点 → 自动钻出 或 手动钻出
  breadcrumb: ["top", "g1", "bbb_id"] → ["top", "g1"]
  画布恢复到 top 的多图融合模式
```

### 13.4 统一状态管理模型

```typescript
const navigationState = {
  // 当前选择加载的所有图 YAML 数据字典
  graphs: {
    "aaa_id": { /* YAML 导出的对象 */ },
    "bbb_id": { /* YAML 导出的对象 */ }
  },

  // 多选框选中的加载项
  selectedGraphIds: ["aaa_id", "bbb_id"],

  // 当前处于顶层(top)还是子图中
  breadcrumb: ["top", "aaa_id", "bbb_id"],

  // 当前激活/聚焦的节点（全局唯一ID）
  currentNodeId: "bbb_id::sub_node_1",

  // 钻入栈
  drillStack: DrillStackItem[]
}
```

### 13.5 验收标准

- [ ] 顶层 `top` 多选框可勾选多个导航图，画布同时渲染它们的节点和边
- [ ] 全选选项可一键加载所有导航图
- [ ] 节点 ID 做命名空间化处理，不同图间 ID 不冲突
- [ ] 子图节点在画布上显示为特殊样式，面板上显示 **[钻入子图]** 按钮
- [ ] 钻入后面包屑显示 `top / g1 / g2` 链路
- [ ] 无后继节点自动显示 **[钻出子图]** 按钮
- [ ] 钻出后面包屑回退一层
- [ ] 多级嵌套钻入正确

---

## 十四、扩展考虑（V2，暂不实现）

- **图版本控制**：每个图 YAML 文件可附带 `version` 字段，支持导入导出时做版本比对
- **图依赖声明**：`_manifest.yaml` 中声明图之间的依赖关系，用于完整性检查
- **共享卡片池**：跨图共享的卡片不放属于任何特定图，而是存放在 `_shared.yaml` 中
- **图模板**：新建图时可选择从模板生成（包含基础节点骨架）

---

*本文档定义了导航图多文件架构，涵盖 YAML 目录结构、编号映射方案、跨图引用机制、后端 API 及前端跨图显示方案。*
