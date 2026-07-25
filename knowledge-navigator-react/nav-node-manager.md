# 导航节点管理界面 — 功能规范

## 版本

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| 1.0 | 2026-07-25 | — | 初始规范：新增导航节点管理界面，集成在"管理"视图内 |

---

## 一、概述

### 1.1 目标

在现有**管理视图（TreeView — 认知卡片管理）**基础上，增加**导航节点管理**子视图，两者通过子 Tab 切换。用户可在一个入口下完成"卡片管理"和"节点管理"两类操作。

导航节点管理界面允许用户：
- 浏览、搜索所有导航节点
- 编辑节点的基本字段（label、description）
- 管理绑定的认知卡片（bound_cards）
- 配置指向下一节点的连接及权重（next_nodes）
- 查看浏览行为记录（browse_history）

### 1.2 子 Tab 结构

```
管理视图 (TreeView)
│
├── 子 Tab ● 认知卡片   ○ 导航节点
│       │                      │
│       ▼                      ▼
│   卡片树形管理           节点管理界面
│   (现有功能)            (新增功能)
```

子 Tab 位于视图标题下方，两个标签互斥，当前激活标签高亮显示。

---

## 二、UI 交互

### 2.1 界面布局

整体分为左右/上下两栏结构：

```
┌──────────────────────────────────────────┐
│  认知卡片管理                    ← 返回   │  ← TopBar（仅在从 NavView 跳入时显示返回）
├──────────────────────────────────────────┤
│  ○ 认知卡片              ● 导航节点       │  ← 子 Tab 切换器
├───────────────────┬──────────────────────┤
│  节点搜索          │                      │
│  ┌────────────┐   │  ● 机器学习基础       │  ← 当前选中节点的编辑面板
│  │ 🔍 搜索...  │   │  ┌────────────────┐  │
│  └────────────┘   │  │ id: node-ml-..  │  │
│                   │  │ label: 机器学习基础│  │
│  ┌──────────────┐ │  │ desc: 涵盖监督...│  │
│  │ ● 机器学习基础 │ │  ├────────────────┤  │
│  │ ○ 数学基础    │ │  │ 【绑定认知卡片】  │  │
│  │ ○ 概率论     │ │  │ root/1  机器学习 │  │
│  │ ○ 线性代数   │ │  │ root/1/1 监督学习│  │
│  │ ○ 监督学习   │ │  │ [+ 添加]        │  │
│  │ ○ 无监督学习  │ │  ├────────────────┤  │
│  │ ○ ...       │ │  │ 【指向节点权重】  │  │
│  │             │ │  │ node-supervised    │  │
│  │             │ │  │   预设: 0.75       │  │
│  │             │ │  │   浏览: 0.42       │  │
│  │             │ │  │  类型: preset  [✕] │  │
│  │             │ │  │ node-unsupervised   │  │
│  │             │ │  │   预设: 0.60       │  │
│  │             │ │  │   浏览: 0.30       │  │
│  │             │ │  │  类型: preset  [✕] │  │
│  │             │ │  │ [+ 添加指向]       │  │
│  │             │ │  ├────────────────┤  │
│  │             │ │  │ 【浏览记录】     │  │
│  │             │ │  │ 来自 node-prob... │  │
│  │             │ │  │   3 次 · 最后 07-24│  │
│  │             │ │  │ 来自 node-line... │  │
│  │             │ │  │   5 次 · 最后 07-24│  │
│  │             │ │  └────────────────┘  │
│  └──────────────┘ │                      │
│  节点列表          │  编辑面板            │
└───────────────────┴──────────────────────┘
```

### 2.2 交互行为

| ID | 功能 | 触发方式 | 预期行为 |
|----|------|----------|----------|
| NM-01 | 切换子 Tab | 点击"认知卡片" / "导航节点" 标签 | 切换显示内容，保持搜索查询不变 |
| NM-02 | 节点搜索 | 输入框输入 | 在节点 label 和 description 中模糊匹配，过滤列表 |
| NM-03 | 节点选中 | 点击节点列表行 | 高亮选中行 → 右侧编辑面板加载该节点的完整字段 |
| NM-04 | 编辑 label | 点击 label 字段 | 变为可编辑输入框，修改后自动保存 |
| NM-05 | 编辑 description | 点击描述区域 | 变为可编辑文本框，修改后自动保存 |
| NM-06 | 添加绑定卡片 | 点击 [+ 添加] | 弹出认知卡片选择器（搜索模式），选中后加入列表 |
| NM-07 | 移除绑定卡片 | 点击卡片项上的 [✕] | 从 bound_cards 列表中移除该项 |
| NM-08 | 添加指向节点 | 点击 [+ 添加指向] | 弹出导航节点选择器，选择目标 + 填写预设/浏览权重 |
| NM-09 | 编辑指向权重 | 点击预设/浏览权重数值 | 变为可编辑输入框，修改后自动保存 |
| NM-10 | 编辑连接类型 | 点击类型下拉 | 切换 preset / browse_derived / user_added |
| NM-11 | 删除指向节点 | 点击指向项上的 [✕] | 从 next_nodes 列表中移除该项 |
| NM-12 | 浏览记录查看 | 展开"浏览记录"区域 | 显示从各节点跳转来的次数和最后时间 |
| NM-13 | 返回导航 | 点击"← 返回" | 仅当从 NavView 跳入时显示，返回 NavView |

### 2.3 关键细节

- **布局适配**：移动端（< 480px）节点列表和编辑面板上下排列，节点列表在上方（可折叠）；桌面端左右排列
- **自动保存**：所有编辑操作即时生效，无需"保存"按钮。每次修改直接更新内存中的数据（持久化由未来 YAML 文件写入功能实现）
- **空状态**：无选中节点时右侧显示"请从列表中选择一个导航节点"
- **搜索即过滤**：搜索时节点列表实时过滤，选中自动跳到第一个匹配项（若当前选中不匹配则清空）
- **只读字段**：`id` 字段只读显示，不可编辑（导航节点 id 作为标识不应被随意修改）

---

## 三、数据流

### 3.1 NavNodeStore（新增）

```typescript
// store/navNodeStore.ts

interface NavNodeStore {
  // 列表
  allNodes: NavNode[]           // 全部导航节点（来源: allNavNodes）
  searchQuery: string           // 搜索关键词
  filteredNodes: NavNode[]      // 过滤后列表

  // 编辑选中
  selectedNodeId: string | null
  editingNode: NavNode | null   // 当前编辑的节点副本

  // 子 Tab
  activeSubTab: 'cards' | 'nodes'  // 'cards' = 认知卡片管理, 'nodes' = 导航节点管理

  // 方法
  setActiveSubTab: (tab: 'cards' | 'nodes') => void
  setSearchQuery: (q: string) => void
  selectNode: (id: string) => void
  updateField: <K extends keyof NavNode>(field: K, value: NavNode[K]) => void
  addBoundCard: (cardId: string) => void
  removeBoundCard: (cardId: string) => void
  addNextNode: (ref: NextNodeRef) => void
  updateNextNode: (targetId: string, field: string, value: number | string) => void
  removeNextNode: (targetId: string) => void
}
```

### 3.2 数据源

所有导航节点数据来自 `src/data/allNavNodes.ts` 中的 `allNavNodes` 数组：

| 字段 | 来源 | 可编辑 |
|------|------|--------|
| `id` | 节点标识 | ❌ 只读 |
| `label` | 节点名称 | ✅ |
| `description` | 节点描述 | ✅ |
| `bound_cards` | 绑定的认知卡片 id 列表 | ✅ 增删 |
| `browse_history` | 浏览跳转记录 | ❌ 只读（由浏览行为自动生成） |
| `next_nodes` | 出向连接列表 | ✅ 增删改 |
| `priority_config` | 权重优先级配置 | ⏳ 后续版本 |

### 3.3 与现有视图的关系

```
管理视图 (TreeView)
  ├── 子 Tab: 认知卡片 → TreeList (现有)
  └── 子 Tab: 导航节点 → NodeListView + NodeEditPanel (新增)

导航视图 (NavView)
  └── [节点管理] 按钮 → 管理视图并切到导航节点子 Tab
      (方便用户在导航中直接跳转到节点编辑)
```

### 3.4 编辑操作的数据变更

所有编辑操作直接修改 NavNodeStore 中的 `allNodes` 数组：

```
用户编辑字段
       │
       ▼
在 allNodes 中找到对应节点并更新字段
       │
       ▼
更新 editingNode 副本（保持与源同步）
       │
       ▼
同步到 allNavNodes（全局数据源）
```

当前阶段数据变更仅作用在内存中。后续持久化到 YAML 文件时，将统一通过 `data-saver` 模块写入。

---

## 四、组件结构

### 4.1 组件树

```
TreeView (增强)
  │
  ├── SubTabBar (新增: 认知卡片 / 导航节点)
  │
  ├── [认知卡片子 Tab] → 现有 TreeList + BreadcrumbNav + SearchBar + FAB
  │
  └── [导航节点子 Tab] → NodeManagementView (新增)
       │
       ├── NodeList (新增: 左侧节点列表)
       │   ├── SearchBar（过滤节点列表）
       │   └── NodeListItem (新增: 单行节点项)
       │
       └── NodeEditPanel (新增: 右侧编辑面板)
            ├── NodeBasicFields (新增: 基本字段编辑)
            ├── BoundCardEditor (新增: 绑定卡片管理)
            ├── NextNodeEditor (新增: 指向节点权重编辑)
            └── BrowseHistoryViewer (新增: 浏览记录查看)
```

### 4.2 组件接口

```typescript
// NodeListItemProps
interface NodeListItemProps {
  node: NavNode
  isSelected: boolean
  onClick: () => void
  highlight?: string      // 搜索高亮关键词
}

// NodeEditPanelProps
interface NodeEditPanelProps {
  node: NavNode           // 当前编辑的节点
}

// BoundCardEditorProps
interface BoundCardEditorProps {
  boundCardIds: string[]   // 绑定的卡片 id 列表
  onAdd: (cardId: string) => void
  onRemove: (cardId: string) => void
}

// NextNodeEditorProps
interface NextNodeEditorProps {
  nextNodes: NextNodeRef[]
  allNodeIds: string[]     // 用于选择目标节点的候选项
  onAdd: (ref: NextNodeRef) => void
  onUpdate: (targetId: string, field: string, value: number | string) => void
  onRemove: (targetId: string) => void
}

// BrowseHistoryViewerProps
interface BrowseHistoryViewerProps {
  browseHistory: { from: string; count: number; last_at: string }[]
}
```

### 4.3 目录结构

```
components/
  tree/
    ├── ... (现有: TreeList, TreeNode, TreeBadge)
    └── SubTabBar.tsx + .module.css       ← 新增：子 Tab 切换器
  node-mgr/                               ← 新增目录
    ├── NodeManagementView.tsx + .module.css  ← 导航节点管理主容器
    ├── NodeList.tsx + .module.css            ← 节点列表
    ├── NodeListItem.tsx + .module.css        ← 单行节点
    ├── NodeEditPanel.tsx + .module.css       ← 编辑面板
    ├── NodeBasicFields.tsx + .module.css     ← 基本字段
    ├── BoundCardEditor.tsx + .module.css     ← 绑定卡片编辑
    ├── NextNodeEditor.tsx + .module.css      ← 指向节点权重编辑
    ├── BrowseHistoryViewer.tsx + .module.css ← 浏览记录查看
    └── NodeSelector.tsx + .module.css        ← 节点/卡片选择弹窗

store/
  ├── navNodeStore.ts               ← 新增：节点管理状态
  └── ...
```

### 4.4 App 注册

管理视图的 TabBar 标签（"管理"）保持不动，仅在 TreeView 内部通过子 Tab 切换。

```typescript
// App.tsx — 无需变更。TreeView 内部处理子路由
const viewMap: Record<ViewName, React.FC> = {
  search: SearchView,
  nav: NavView,
  plan: PlanView,
  browse: BrowseView,
  tree: TreeView,   // ← TreeView 内部通过子 Tab 切换卡片/节点管理
}
```

---

## 五、编辑面板详解

### 5.1 基本字段编辑（NodeBasicFields）

```
┌─────────────────────────────────┐
│  id: node-ml-foundation   (只读) │
│  label: [机器学习基础      ]    │  ← 可编辑输入框
│  description:                    │
│  [涵盖监督学习、无监督学习...]   │  ← 可编辑文本域
│    2-4 行                        │
└─────────────────────────────────┘
```

- `id` 以灰色文字显示，不可修改
- `label` 为单行输入框
- `description` 为多行文本域（2-4 行高度，自动换行）

### 5.2 绑定卡片编辑（BoundCardEditor）

```
┌─────────────────────────────────┐
│ 【绑定认知卡片】                  │
│  ├ root/1  机器学习           [✕] │
│  ├ root/1/1 监督学习          [✕] │
│  └ [+ 添加]                      │
│    ┌──────────────────────┐      │
│    │ 🔍 搜索卡片...       │      │  ← 点击 [+ 添加] 后弹出
│    ├──────────────────────┤      │
│    │ ○ 机器学习           │      │
│    │ ○ 神经网络           │      │
│    │ ● 深度学习           │      │
│    │ ○ ...               │      │
│    └──────────────────────┘      │
└─────────────────────────────────┘
```

- 列表中每项显示认知卡片的 `id` 和 `title`
- 点击 [✕] 移除绑定
- 点击 [+ 添加] 弹出 NodeSelector（搜索模式，仅显示认知卡片）
- NodeSelector 中选中卡片后自动加入列表，弹窗关闭

### 5.3 指向节点权重编辑（NextNodeEditor）

```
┌─────────────────────────────────┐
│ 【指向节点权重】                  │
│  ├ 监督学习 (node-supervised)    │
│  │  预设: [0.75        ]        │  ← 可编辑数值 (0-1)
│  │  浏览: [0.42        ]        │  ← 可编辑数值 (0-1)
│  │  类型: [preset ▼]    [✕]    │  ← 下拉选择 + 删除
│  ├ 无监督学习 (node-unsupervised)│
│  │  预设: [0.60        ]        │
│  │  浏览: [0.30        ]        │
│  │  类型: [preset ▼]    [✕]    │
│  └ [+ 添加指向]                  │
│    ┌──────────────────────┐      │
│    │ 目标节点: [ 选择 ▼]   │      │  ← 点击 [+ 添加指向] 后弹出
│    │ 预设权重: [0.50]     │      │
│    │ 浏览权重: [0.30]     │      │
│    │ 连接类型: [preset ▼]  │      │
│    │ [确认]  [取消]       │      │
│    └──────────────────────┘      │
└─────────────────────────────────┘
```

- 预设权重和浏览权重的输入范围：0.00 ~ 1.00，步进 0.01
- 连接类型选项：preset（预设）/ browse_derived（浏览衍生）/ user_added（用户添加）
- 添加弹窗中"目标节点"下拉列表为当前**未被添加**的其他导航节点

### 5.4 浏览记录查看（BrowseHistoryViewer）

```
┌─────────────────────────────────┐
│ 【浏览记录】             共 8 次  │
│  ├ 来自: 线性代数                │
│  │  次数: 5  · 最后: 2026-07-24  │
│  │  08:15                        │
│  ├ 来自: 概率论                  │
│  │  次数: 3  · 最后: 2026-07-24  │
│  │  09:30                        │
│  │                               │
│  │  (浏览记录由用户行为自动生成)   │  ← 灰色小字提示只读
└─────────────────────────────────┘
```

- 完全只读展示，不可编辑
- 按 `last_at` 倒序排列
- 每项显示：来源节点 label、跳转次数、最后跳转时间
- 底部灰色小字提示"浏览记录由用户行为自动生成"

---

## 六、与现有视图的联动

### 6.1 从 NavView 跳转到节点编辑

在 NavView 的下拉面板（DropDownPanel）中增加"管理"入口：

```
DropDownPanel (展开态)
  ├── 节点标题 / 描述
  ├── 绑定卡片列表
  ├── 指向节点列表
  ├── [添加为途径点]  ← 现有
  └── [编辑节点]      ← 新增：跳转到管理视图并选中此节点
```

```typescript
// DropDownPanel 中新增操作
const handleEditNode = () => {
  if (!node) return
  useNavNodeStore.getState().selectNode(node.id)
  useNavNodeStore.getState().setActiveSubTab('nodes')
  useViewStore.getState().switchView('tree')
}
```

### 6.2 TabBar 动效

当从 NavView 点击"编辑节点"跳转到管理视图时，原本处于非激活态的"管理"Tab 变为激活态，与正常的 Tab 切换行为一致。

---

## 七、验收标准

- [ ] 管理视图顶部显示"认知卡片"和"导航节点"两个子 Tab，点击切换
- [ ] 导航节点子 Tab 显示节点列表（左侧/上方）和编辑面板（右侧/下方）
- [ ] 节点搜索支持模糊匹配 label 和 description
- [ ] 点击节点行，编辑面板加载该节点的完整字段
- [ ] 编辑 label 和 description 即时生效
- [ ] 绑定卡片列表展示 card id + title，可添加和移除
- [ ] 指向节点列表展示目标节点、预设权重、浏览权重和连接类型，可增删改
- [ ] 权重输入范围 0.00-1.00，超出时自动纠正
- [ ] 浏览记录只读展示，按时间倒序排列
- [ ] 从 NavView 下拉面板"编辑节点"可跳转到管理视图并自动选中该节点
- [ ] 移动端布局适配（列表和编辑面板上下排列）
- [ ] 所有 TypeScript 类型定义正确，编译零错误

---

## 八、与现有功能的兼容性

| 现有功能 | 兼容性 | 说明 |
|----------|--------|------|
| TreeView 认知卡片管理 | ✅ 不变 | 作为子 Tab 保留 |
| TreeView 搜索/面包屑/FAB | ✅ 不变 | 仅在卡片子 Tab 中显示 |
| NavView 下拉面板 | ✅ 扩展 | 新增"编辑节点"按钮 |
| NavNode 数据源 | ✅ 不变 | 编辑直接修改 allNavNodes 内存数据 |
| TabBar 4 个 Tab | ✅ 不变 | 管理 Tab 保持不变 |
| 键盘快捷键 1-4 | ✅ 不变 | 不涉及 |

---

## 九、边界情况

| 场景 | 行为 |
|------|------|
| 导航节点列表为空 | 显示"暂无导航节点"空状态 |
| 搜索无匹配 | 显示"未找到匹配的导航节点" |
| 未选中节点 | 编辑面板显示"请从列表中选择一个导航节点" |
| 权重输入超出范围 (0-1) | 失焦时自动 clamp 到 [0, 1] |
| 重复添加同一绑定卡片 | 添加时检查是否已存在，重复则忽略并提示 |
| 添加指向节点时选中自身 | 下拉列表排除当前节点自身 |
| 从 NavView 跳入后退回 | 保持子 Tab 为"导航节点"，不清空选中 |

---

## 十、后续可扩展方向

1. **YAML 持久化** — 编辑操作写入本地 YAML 文件，支持版本控制
2. **优先级配置编辑** — 支持编辑 priority_config 字段（mode、预设排序号、浏览排序号、用户覆盖）
3. **新增/删除导航节点** — 支持创建新节点和删除已有节点
4. **撤销/重做** — 编辑历史记录，支持 Ctrl+Z 撤销
5. **批量编辑** — 多选节点后批量修改相同字段
