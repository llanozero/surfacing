# 多选框折叠 & 面包屑迁移 — 实现记录

## 版本

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| 1.0 | 2026-07-28 | — | 多选框折叠、面包屑移至导航界面、默认不勾选、空画布 |

---

## 一、变更内容

### 1.1 多选框折叠

- 默认**折叠**状态（仅显示标题栏"画布图加载 ▸" + 已选数量）
- 点击标题栏展开/折叠
- 展开时箭头变为 ▾，折叠时 ▸
- 折叠状态下已选图数量仍然可见

### 1.2 默认不勾选

- 移除自动初始化（原来的 `useEffect` 在首次加载时自动全选）
- 初始状态 `selectedGraphIds = []`，画布无数据
- 用户**主动勾选**后，画布才加载对应图的节点

### 1.3 面包屑迁移

- 面包屑导航从 `StatusBar` 移至 `NavView`（导航界面）
- 使用已有的 `BreadcrumbNav` 共享组件
- 顶层显示 `top`，钻入后显示完整路径：`top / g1 / g2`
- StatusBar 简化为仅显示时间 + 标题 + 设置按钮

### 1.4 空画布占位

- 未勾选任何图时，画布区显示占位提示："请在上方选择要加载的导航图"
- 画布 D3 收到空节点数组，安全渲染空 SVG

---

## 二、文件变更清单

| 文件 | 变更 |
|------|------|
| `src/components/nav/GraphMultiSelect.tsx` | 新增折叠状态 `collapsed`；移除自动全选 effect；header 改为可点击按钮 |
| `src/components/nav/GraphMultiSelect.module.css` | header 改为按钮样式 + hover；新增 `.arrow` 折叠指示器 |
| `src/components/views/NavView.tsx` | 集成 `BreadcrumbNav`；计算 `breadcrumbItems`；新增 `hasCanvasData` 空画布逻辑；`inDrill` 替代 `isInDrill()` |
| `src/components/views/NavView.module.css` | 新增 `.emptyCanvas` 占位提示样式 |
| `src/components/layout/StatusBar.tsx` | **移除所有面包屑逻辑**；仅保留时间 + 标题 + TTS 设置 |
| `multi-graph-architecture.md` | 更新设计文档（已在上次完成） |
| `nav-canvas-graph-selector.md` | 更新设计文档（已在上次完成） |
| `implementation-subgraph-drilldown-v2.md` | 本文档 |

---

## 三、行为对比

| 场景 | v1 (旧) | v2 (新) |
|------|---------|---------|
| 初始化 | 自动全选所有图 | 默认不勾选，画布为空 |
| 多选框 | 始终展开 | 默认折叠，可点击展开 |
| 面包屑 | StatusBar 顶部栏 | NavView 导航界面内 |
| 无图 | 画布仍渲染数据 | 画布显示占位提示 |
| 勾选变化 | 画布即时更新 | 画布即时更新 |

---

## 四、验收清单

- [x] 多选框默认折叠，点击展开/折叠
- [x] 初始不勾选，画布为空 + 占位提示
- [x] 勾选任一图后画布立即加载数据
- [x] 全选/取消全选正常工作
- [x] 面包屑在 NavView 中显示，含 `top` 根路径
- [x] 钻入后面包屑追加，钻出后回退
- [x] StatusBar 不再显示面包屑
- [x] 编译零 type 错误
- [x] Vite 生产构建通过
