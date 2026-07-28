# 导航画布多图选择：顶层聚合、引用节点、子图钻入与后端计算

## 版本

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| 1.0 | 2026-07-26 | — | 初始规范 |

---

## 一、概念模型

### 1.1 三层节点类型

导航图中存在三种导航节点：

| 类型 | 字段标识 | 含义 | 出向连线 |
|------|----------|------|----------|
| **普通节点** | 无特殊字段 | 纯当前图的节点，描述知识主题 | 指向本图或其他图的普通节点 |
| **引用节点** | `ref_graph_id` + `ref_node_id` | 引用另一个图中的某个节点，仅展示其描述信息 | 在本图中走另一套独立连接 |
| **子图节点** | `sub_graph_id` + `entry_node_id` | 可钻入到另一个图，入口节点由 entry_node_id 指定 | 在本图中走另一套独立连接（钻出后的后继） |

```yaml
# 普通节点
- id: node-supervised
  label: 监督学习

# 引用节点 — 从另一个图"借"节点的描述，在本图有独立的连接
- id: node-ref-probability
  label: 引用: 概率论基础
  ref_graph_id: g2
  ref_node_id: node-probability-theory
  next_nodes:
    - target_id: node-ml-foundation
      preset_weight: 0.70

# 子图节点 — 可钻入另一个图，钻出后走独立连接
- id: node-math-subgraph
  label: 数学基础全景
  sub_graph_id: g2
  entry_node_id: node-probability-theory
  next_nodes:
    - target_id: node-deep-learning
      preset_weight: 0.60
```

### 1.2 引用节点 vs 子图节点

| 特性 | 引用节点 | 子图节点 |
|------|----------|----------|
| 指定目标图 | `ref_graph_id` | `sub_graph_id` |
| 指定入口节点 | `ref_node_id` | `entry_node_id` |
| 在本图的行为 | 展示目标节点的描述文本 | 展示目标节点的描述 + 钻入按钮 |
| 点击后 | 高亮该节点，展示描述 | 钻入目标图（切换到子图） |
| 出向连接 | 本图定义的 `next_nodes` | 本图定义的 `next_nodes`（钻出后走） |
| 数据来源 | 从目标图拉取目标节点的描述 | 完整切换到目标图 |
| 钻出 | 不适用 | 无后继时自动/手动钻出 |
| 面包屑影响 | 不变 | 追加路径 |

**引用节点的核心用途**：在顶层（top）聚合视图中，当需要引用另一个知识体系中的某个概念但不需要完整钻入时，使用引用节点。引用节点会从目标图中提取目标节点的 `label`、`description`、`bound_cards` 等描述性字段，**去除**其在目标图中的 `next_nodes`（前驱/后继连线），然后在顶层图中定义属于顶层图自己的独立连接。

---

## 二、顶层（top）概念

### 2.1 top 作为虚拟层

顶层是一个**虚拟导航层**，不是由某个 YAML 文件定义的图，而是用户通过多选框选择多个导航图后聚合而成的视图。

```
top（顶层虚拟层）
 ├── 由用户选择要展示的导航图列表决定
 ├── 加载这些图的所有普通节点
 ├── 加载这些图中出现在本图顶层的引用节点的描述数据（从目标图拉取）
 ├── 加载这些图中出现在本图顶层的子图节点（保留钻入能力）
 └── 所有节点的连线在本图内走本图定义
```

### 2.2 top 的边界

- top 没有自己的 YAML 文件
- top 的节点/边数据由后端根据用户勾选的图列表动态计算返回
- top 是面包屑路径的根：`top/g2/node-probability-theory`
- 从顶层钻入子图后，新的层次追加到面包屑路径末尾
- 从子图钻出后回到顶层

---

## 三、多选图机制

### 3.1 选择方式

导航画布上方增加多选框面板，每个图一行（checkbox + 图名 + 节点数概览）：

```
┌─────────────────────────────────────────────────────┐
│  画布范围: [☑ 全选]                                    │
│   ☑ g1 机器学习         (18 节点, 35 卡片)             │
│   ☑ g2 数学基础         (7 节点,  8 卡片)              │
│   ☐ g3 认知心理学       (7 节点, 12 卡片)              │
│                                                       │
│  [应用选择 ▸]  当前: g1,g2 共 25 节点                │
└─────────────────────────────────────────────────────┘
```

- **全选**：勾选所有图（等同于之前的 `__all__`）
- **点选**：每个图独立勾选
- **至少勾选一个**：不可全部取消（至少保留一个）
- **应用**：点击"应用选择"或自动应用（防抖 500ms）后，后端重新计算画布数据

### 3.2 后端计算流程

```mermaid
flowchart TD
    A[前端 POST 勾选的图 ID 列表] --> B[后端接收 selected_graph_ids]
    B --> C[遍历每个图 ID 加载对应 YAML]
    C --> D[收集所有普通节点 + 边]
    D --> E{存在引用节点?}
    E -->|是| F[解析 ref_graph_id::ref_node_id\n提取描述字段\n丢弃目标图中的连线]
    E -->|否| G
    F --> G[收集子图节点保持原样]
    G --> H[合并/去重]
    H --> I[返回聚合数据:\n{nodes, edges, subgraph_nodes, ref_nodes}]
    I --> J[前端 D3 渲染]
```

#### 新增 API

```
POST /api/graphs/canvas-data
Body: { "selected_graph_ids": ["g1", "g2"] }
Response: {
  "nodes": [ ... ],       // 聚合后的节点列表
  "edges": [ ... ],       // 聚合后的边列表
  "subgraph_nodes": [ ... ], // 子图节点列表（含 sub_graph_id/entry_node_id）
  "ref_nodes": [ ... ],   // 引用节点列表（含 ref_graph_id/ref_node_id）
  "graph_labels": { "g1": "机器学习", "g2": "数学基础" },
  "node_count": 25,
  "edge_count": 32
}
```

### 3.3 引用节点的后端处理

当后端遇到引用节点时：

1. 根据 `ref_graph_id` 找到目标图
2. 根据 `ref_node_id` 找到目标节点
3. **提取以下字段**：`id`、`label`、`description`、`bound_cards`
4. **丢弃以下字段**：`next_nodes`（目标图中的连线）、`browse_history`、`priority_config`
5. **保留本图中引用节点自己的 `next_nodes`**（这是引用节点在本图定义的新连接）
6. 返回的节点中增加标记字段 `_nodeType: 'ref'`

```python
# 后端处理引用节点的伪代码
def resolve_ref_node(node: dict, ref_graph_id: str, ref_node_id: str) -> dict:
    target_graph = store.get_graph(ref_graph_id)
    if not target_graph:
        raise HTTPException(404, f"目标图 {ref_graph_id} 不存在")
    
    target_node = target_graph.get_node(ref_node_id)
    if not target_node:
        raise HTTPException(404, f"节点 {ref_node_id} 不存在")
    
    # 提取描述性字段，丢弃连线
    resolved = {
        "id": node["id"],          # 保留引用节点在本图的 ID
        "label": target_node.get("label", ""),
        "description": target_node.get("description", ""),
        "bound_cards": target_node.get("bound_cards", []),
        "next_nodes": node.get("next_nodes", []),  # 使用本图定义的连线！
        "_nodeType": "ref",
        "_sourceGraphId": ref_graph_id,
        "_sourceNodeId": ref_node_id,
    }
    return resolved
```

---

## 四、画布范围状态管理

### 4.1 状态定义

在 `navStore` 中新增：

```typescript
interface NavStore {
  // ……已有字段……

  /** 当前画布选中的图 ID 列表（多选） */
  selectedGraphIds: string[]
  
  /** 是否全选 */
  selectAll: boolean
  
  /** 设置勾选列表 */
  setSelectedGraphIds: (ids: string[]) => void
  
  /** 切换全选 */
  toggleSelectAll: () => void
  
  /** 切换某个图 */
  toggleGraph: (graphId: string) => void
}
```

### 4.2 初始化

```
- 默认: selectedGraphIds = [activeGraphId]（仅当前活动图）
- 首次进入导航视图: 若 graphs.length > 0, 默认勾选第一个图
- 从钻入状态回到顶层: 恢复钻入前的 selectedGraphIds
```

### 4.3 与钻入/钻出的联动

```
[顶层多图模式]                     ← 用户选择 g1+g2 展示
    │  用户点击子图节点 → drillIn()
    │    → 记下当前 selectedGraphIds 到钻入栈（钻出后恢复）
    │    → 切换到子图单图模式（selectedGraphIds = [subGraphId]）
    v
[子图单图模式]                     ← 面包屑: top/g2
    │  用户钻出 → drillOut()
    │    → 从钻入栈恢复 selectedGraphIds
    v
[顶层多图模式]                     ← 恢复到 g1+g2
```

---

## 五、面包屑导航

### 5.1 路径格式

```
顶层路径:  top
钻入 g2:  top / g2 数学基础
钻入 g3:  top / g2 数学基础 / g3 认知心理学
```

### 5.2 在 drillStore 中扩展

```typescript
// drillStore.ts
export const TOP_GRAPH_ID = 'top'

export interface DrillStackItem {
  /** 钻入前的画布范围（用于钻出后恢复） */
  prevSelectedGraphIds: string[]
  
  /** 钻入前的图 */
  parentGraphId: string
  
  /** 钻入前的子图节点 ID */
  parentNodeId: string
  
  /** 钻入的子图 */
  subGraphId: string
  
  /** 入口节点 */
  entryNodeId: string
  
  /** 父节点 label */
  parentNodeLabel: string
  
  /** 子图 label */
  subGraphLabel: string
}
```

### 5.3 面包屑 UI

```
┌──────────────────────────────────────────────────────────┐
│  认知导航                                                   │
│  [面包屑]  top › g2 数学基础 › g3 认知心理学      [钻出]   │
├──────────────────────────────────────────────────────────┤
```

- 顶层显示为 `top`
- 每一级点击可跳转到对应图的顶层视图
- 右侧蓝色钻出按钮

---

## 六、引用节点前端渲染

### 6.1 画布上的引用节点

引用节点在 D3 画布上的视觉样式与普通节点不同：

```
  普通节点:       引用节点:          子图节点:
  ┌────────┐     ┌────────┐        ╔════════╗
  │ 监督学习│     │ ↻ 概率论│        ║ 📂 数学 ║
  │        │     │  基础  │        ║  基础  ║
  └────────┘     │ └ g2   │        ║ └ g1   ║
                  └────────┘        ╚════════╝
```

- **引用节点**：圆圈轮廓用**虚线**，右下角标注来源图 `└ {图ID}`
- **子图节点**：方框/卡片式轮廓（与普通圆形区分），带 📂 图标

### 6.2 DropDownPanel 中的引用节点

当用户点击引用节点时，下拉面板显示：

```
┌─────────────────────────────────────────┐
│  ↻ 概率论基础（来自 g2 数学基础）        │
│  ───────────────────────────────────── │
│  随机变量、概率分布与贝叶斯推断。         │
│                                         │
│  绑定卡片:                               │
│  · root/math/1/1 随机变量与分布          │
│  · root/math/1/2 贝叶斯定理              │
│                                         │
│  [跳转到源图]  [添加为途径点]             │
└─────────────────────────────────────────┘
```

- 标题显示 `↻` 图标 + 来源图标签
- "跳转到源图"按钮：直接切换到该引用节点所在的目标图

---

## 七、API 设计

### 7.1 POST /api/graphs/canvas-data

请求体：

```json
{
  "selected_graph_ids": ["g1", "g2"],
  "resolve_refs": true
}
```

响应：

```json
{
  "nodes": [
    { "id": "node-supervised", "label": "监督学习", "description": "...", "next_nodes": [...], "_nodeType": "normal", "_sourceGraphId": "g1" },
    { "id": "node-ref-probability", "label": "概率论基础", "description": "...", "next_nodes": [...], "_nodeType": "ref", "_sourceGraphId": "g2", "_sourceNodeId": "node-probability-theory" },
    { "id": "node-math-subgraph", "label": "数学基础全景", "description": "...", "next_nodes": [...], "_nodeType": "subgraph", "sub_graph_id": "g2", "entry_node_id": "node-probability-theory", "_sourceGraphId": "g1" }
  ],
  "edges": [
    { "source": "node-ref-probability", "target": "node-ml-foundation", "weight": 0.7, "_edgeType": "ref" },
    { "source": "node-math-subgraph", "target": "node-deep-learning", "weight": 0.6, "_edgeType": "subgraph" }
  ],
  "graph_labels": { "g1": "机器学习", "g2": "数学基础" },
  "node_count": 25,
  "edge_count": 32
}
```

### 7.2 新增字段说明

返回的每个节点额外增加 `_` 前缀的内部字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `_nodeType` | `'normal'` `'ref'` `'subgraph'` | 节点类型标记 |
| `_sourceGraphId` | string | 该节点所属的原始图 ID |
| `_sourceGraphLabel` | string | 该节点所属的原始图标签 |
| `_sourceNodeId` | string | 引用节点：被引用的原始节点 ID |

返回的每条边额外增加：

| 字段 | 类型 | 说明 |
|------|------|------|
| `_edgeType` | `'normal'` `'ref'` `'subgraph'` | 边的类型标记 |

---

## 八、边界情况

| 场景 | 行为 |
|------|------|
| 用户取消勾选所有图 | 自动勾选上一次勾选的最后一个图，Toast 提示"至少需要选择一个图" |
| 引用节点的目标图不存在 | 该节点降级为显示 ID 文本，Toast 提示"目标图 xxx 已不存在" |
| 引用节点的目标节点不存在 | 该节点降级为显示 ID 文本，Toast 提示"目标节点 xxx 已不存在" |
| 钻入后勾选的图变化 | 钻入时锁定 selectedGraphIds（快照到钻入栈），钻出后恢复 |
| 新增/删除图后 | 重新拉取图列表，自动更新勾选框列表，移除已不存在的图 ID |
| 引用节点形成循环引用 | 允许（类似网页超链接），后端不做循环检测 |
| lite 模式（无后端） | 多选面板隐藏，不可选图 |

---

## 九、验收标准

- [ ] 导航画布上方多选框面板可独立勾选/取消每个图
- [ ] "全选"勾选所有图，"应用选择"触发后端计算
- [ ] `POST /api/graphs/canvas-data` 返回聚合后的节点和边
- [ ] 引用节点从目标图提取描述字段，丢弃原图连线，使用本图的新连线
- [ ] 引用节点在画布上用虚线轮廓+来源标注渲染
- [ ] 子图节点在画布上用卡片式边框+📂图标渲染
- [ ] 钻入时 selectedGraphIds 快照到钻入栈，钻出后恢复
- [ ] 面包屑显示 `top / g2 数学基础 / g3 认知心理学` 层级
- [ ] 面包屑中每一步可点击回到对应图的顶层视图
- [ ] 编译零错误

---

## 十、代码变更清单

### 10.1 后端

| 文件 | 变更 |
|------|------|
| `backend/app/routers/graphs.py` | 新增 `POST /api/graphs/canvas-data` 端点 |
| `backend/app/store.py` | `Graph` 类新增 `get_node_ref()` 方法（提取引用节点描述字段，丢弃连线） |

### 10.2 前端

| 文件 | 变更 |
|------|------|
| `src/store/navStore.ts` | 新增 `selectedGraphIds`、`selectAll` 及相关方法 |
| `src/store/drillStore.ts` | `DrillStackItem` 增加 `prevSelectedGraphIds` 字段 |
| `src/config/graphs.ts` | 新增 `TOP_GRAPH_ID` 常量 |
| `src/components/views/NavView.tsx` | 新增多选框面板、面包屑显示、应用选择按钮 |
| `src/components/views/NavView.module.css` | 多选框面板样式 |
| `src/hooks/useNavCanvas.ts` | 按节点 `_nodeType` 渲染不同样式（引用节点虚线、子图节点方框） |
| `src/components/panel/DropDownPanel.tsx` | 引用节点显示"跳转到源图"按钮 |
| `src/api/index.ts` | 新增 `fetchCanvasData` 方法 |

---

## 十一、数据流示例

### 完整链路：顶层多图 → 钻入 → 钻出

```
1. 用户进入导航视图
   → NavView 加载
   → 默认勾选 activeGraphId（g1）
   → POST /api/graphs/canvas-data { selected_graph_ids: ["g1"] }
   → 后端返回 g1 的所有节点和边
   → D3 渲染

2. 用户勾选 g2，点击"应用选择"
   → navStore.selectedGraphIds = ["g1", "g2"]
   → POST /api/graphs/canvas-data { selected_graph_ids: ["g1", "g2"], resolve_refs: true }
   → 后端聚合 g1 + g2 的数据
   → 遇到引用节点：从目标图提取描述，使用本图连线
   → 返回聚合数据
   → D3 重新渲染

3. 用户点击子图节点"数学基础全景"
   → 钻入栈记录: { prevSelectedGraphIds: ["g1","g2"], parentGraphId: "top", subGraphId: "g2", entryNodeId: "node-probability-theory" }
   → selectedGraphIds = ["g2"]
   → 面包屑: top › g2 数学基础
   → D3 切换到 g2 单图模式

4. 用户在 g2 中浏览到 node-bayes-theorem（无后继）
   → 底部出现"钻出"按钮
   → 用户点击钻出
   → 从钻入栈恢复: selectedGraphIds = ["g1", "g2"]
   → 面包屑: top
   → D3 恢复顶层多图渲染
```

---

*本文档定义了导航画布多图选择机制，涵盖顶层聚合、引用节点处理、子图钻入与后端计算。*
