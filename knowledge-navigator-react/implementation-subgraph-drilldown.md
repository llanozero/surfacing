# 分层导航图 & 多选框画布加载 — 实现记录

## 版本

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| 1.0 | 2026-07-28 | — | 初始实现：子图钻入/钻出 + Top 多选框 + 命名空间化 + 面包屑 |

---

## 一、实现范围

本次变更围绕两个核心能力：

1. **子图节点钻入/钻出**：导航节点新增 `type: 'normal' | 'subgraph'`，子图节点通过 `subgraph_config` 指向另一个导航图的入口节点
2. **Top 层多选框加载**：导航界面新增多选 checkbox，用户可勾选多个导航图在同一画布融合渲染

---

## 二、YAML 数据规范

### 子图节点格式

```yaml
# 节点
nodes:
  - id: "node_1"
    label: "用户登录"
    type: "normal"
    properties:
      panel: "LoginPanel"

  - id: "node_2"
    label: "数学基础导航图"
    type: "subgraph"
    subgraph_config:
      target_graph_id: "g2"
      target_entry_node: "node-probability"
    properties:
      panel: "CheckoutPanel"
```

### TypeScript 类型

```typescript
interface SubgraphConfig {
  target_graph_id: string   // 指向目标图 ID
  target_entry_node: string // 入口节点 ID
}

interface NavNode {
  type?: 'normal' | 'subgraph'
  subgraph_config?: SubgraphConfig
  // 向后兼容
  sub_graph_id?: string    // @deprecated
  entry_node_id?: string   // @deprecated
}
```

---

## 三、架构设计

### 面包屑路径

```
top                          → 顶层（多选框可见）
top / g1                     → 钻入 g1 子图
top / g1 / g2                → 嵌套钻入 g2 子图
```

- StatusBar 始终显示 `top` 为根
- 钻入后追加图 ID，钻出后弹出

### 命名空间化

为避免不同 YAML 的 `id` 冲突，全量模式下节点 ID 加前缀：

```
node-ml-foundation   →   g1::node-ml-foundation
node-probability     →   g2::node-probability
```

### 钻入/钻出状态联动

```
[Top 多图模式]  selectedGraphIds = [g1, g2, g3]
    │
    │  钻入 → snapshot ids
    ▼
[子图单图模式]  多选框隐藏，画布仅渲染子图
    │
    │  钻出 → 恢复 snapshot
    ▼
[Top 多图模式]  selectedGraphIds 恢复
```

---

## 四、文件变更清单

### 新增文件

| 文件 | 说明 |
|------|------|
| `src/components/nav/GraphMultiSelect.tsx` | 多选框组件（全选/单图勾选/统计显示） |
| `src/components/nav/GraphMultiSelect.module.css` | 多选框样式 |
| `src/config/graphs.ts` | 图配置：活动图 ID、跨图引用解析、命名空间化工具 |
| `src/store/drillStore.ts` | 钻入栈管理 + 面包屑构建 + selectedGraphIds 快照 |
| `src/store/graphStore.ts` | 多图列表管理 + 钻入/钻出操作 + 图生命周期 |
| `multi-graph-architecture.md` | 多图架构设计文档 |
| `nav-canvas-graph-selector.md` | 画布图选择器设计文档 |
| `implementation-subgraph-drilldown.md` | 本文档 |

### 后端新增

| 文件 | 说明 |
|------|------|
| `backend/app/routers/graphs.py` | `/api/graphs` 路由：图 CRUD、清单、单图查询 |
| `backend/graphs/` | 多 YAML 图文件目录 + manifest |

### 修改文件

| 文件 | 变更 |
|------|------|
| `src/data/types.ts` | 新增 `SubgraphConfig`、`NamespacedNode` 类型；NavNode 增加 `type`、`subgraph_config` |
| `src/data/allNavNodes.ts` | "数学基础"节点改造为 `type: 'subgraph'` |
| `src/store/navStore.ts` | 新增 `selectedGraphIds`、`getCanvasNodes()`、`getCanvasEdges()` |
| `src/components/views/NavView.tsx` | 集成 GraphMultiSelect；钻入/钻出联动快照恢复 |
| `src/components/views/FreeBrowseView.tsx` | 同步子图节点检测与钻入/钻出逻辑 |
| `src/components/layout/StatusBar.tsx` | 面包屑以 `top` 开头；移除旧单选 dropdown |
| `src/components/layout/StatusBar.module.css` | 新增 `.breadcrumbTop` 样式 |
| `src/hooks/useNavCanvas.ts` | 子图节点检测兼容新字段 |
| `src/api/index.ts` | API 层适配多图 `?graph=` 参数 |
| `backend/app/main.py` | 注册 graphs router |
| `backend/app/store.py` | 支持多图加载 + manifest |

---

## 五、验收清单

- [x] 导航界面 NavView 新增多选 checkbox 区域
- [x] 全选/取消全选功能
- [x] 已选图数量 + 节点总数统计
- [x] 钻入子图时多选框自动隐藏
- [x] 面包屑以 `top` 开头，钻入后追加，钻出后回退
- [x] 钻出后恢复钻入前的多选组合
- [x] 节点 ID 命名空间化（`graph_id::node_id`）
- [x] 默认选中全部图
- [x] lite 模式（单图）多选框隐藏
- [x] 编译零 type 错误
- [x] Vite 生产构建通过
