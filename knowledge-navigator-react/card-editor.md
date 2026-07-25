# 认知卡片编辑面板 — 功能规范

## 版本

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| 1.0 | 2026-07-25 | — | 初始规范：在管理视图中为认知卡片增加字段编辑面板 |

---

## 一、概述

### 1.1 目标

在现有**管理视图（TreeView）**的"认知卡片"子 Tab 中，增加卡片编辑面板。用户在树形列表中点击一张卡片，右侧/下方展开编辑面板，可修改卡片的全部字段。

当前管理视图的认知卡片子 Tab 仅有树形浏览和搜索功能，新增编辑能力后，用户无需切换视图即可完成卡片数据的增删改。

### 1.2 可编辑字段

| 字段 | 类型 | 可编辑 | 说明 |
|------|------|--------|------|
| `id` | string | ❌ 只读 | 卡片标识，由层级路径决定（如 root/1/1） |
| `title` | string | ✅ | 卡片标题 |
| `type` | enum | ✅ | folder / leaf |
| `tag` | string | ✅ | 标签：层级分类 / 决策分支 |
| `description` | string | ✅ | 卡片描述（1-2 句话） |
| `corpus` | string[] | ✅ 增删改 | 语料库列表，每条语料一段文本 |
| `bound_nodes` | string[] | ✅ 增删 | 绑定的导航节点 id 列表 |
| `metadata` | object | ⏳ 后续 | 创建/更新时间等 |

---

## 二、UI 交互

### 2.1 界面布局

在现有树形列表右侧（桌面端）或下方（移动端）增加编辑面板。

```
┌─────────────────────────────────────────┐
│  认知卡片管理                            │
├─────────────────────────────────────────┤
│  ○ 认知卡片              ○ 导航节点      │  ← 子 Tab
├──────────────────┬──────────────────────┤
│  🔍 搜索卡片...    │                      │
│                   │  ● 监督学习           │  ← 选中卡片的编辑面板
│  ┌─────────────┐  │  ┌─────────────────┐ │
│  │ 📁 机器学习  │  │  │ id: root/1/1    │ │
│  │  ├ 📄 监督学习│  │  │ title: [监督学习] │ │
│  │  ├ 📄 无监督..│  │  │ type: [leaf ▼]  │ │
│  │  └ 📄 强化学习│  │  │ tag: [决策分支 ▼]│ │
│  │ 📁 神经网络  │  │  │ description:      │ │
│  │ 📁 深度学习  │  │  │ [使用标注数据训练..]│ │
│  │ ...          │  │  ├─────────────────┤ │
│  └─────────────┘  │  │ 【语料库】        │ │
│  树形列表          │  │ ├ 使用标注数据... [✕]│ │
│                   │  │ ├ 常见算法包括... [✕]│ │
│                   │  │ └ [+ 新增语料]    │ │
│                   │  ├─────────────────┤ │
│                   │  │ 【绑定导航节点】  │ │
│                   │  │ node-supervised [✕]│ │
│                   │  │ [+ 添加绑定]    │ │
│                   │  └─────────────────┘ │
│                   │                      │
└───────────────────┴──────────────────────┘
```

### 2.2 交互行为

| ID | 功能 | 触发方式 | 预期行为 |
|----|------|----------|----------|
| CE-01 | 选中卡片编辑 | 树形列表中点击卡片行 | 高亮选中行 → 右侧编辑面板加载该卡片的全部字段 |
| CE-02 | 编辑 title | 点击 title 输入框 | 修改后自动保存到内存数据源 |
| CE-03 | 切换 type | 点击 type 下拉 | folder / leaf 切换，修改后自动保存 |
| CE-04 | 编辑 tag | 点击 tag 下拉或输入 | 层级分类 / 决策分支 或自定义输入 |
| CE-05 | 编辑 description | 点击描述文本域 | 修改后自动保存 |
| CE-06 | 新增语料 | 点击 [+ 新增语料] | 在 corpus 数组末尾添加空行，进入编辑态 |
| CE-07 | 编辑语料 | 点击语料文本区域 | 变为可编辑文本框，支持多行文本 |
| CE-08 | 删除语料 | 点击语料项上的 [✕] | 从 corpus 数组中移除该项 |
| CE-09 | 拖动排序语料 | 长按语料项拖拽 | 调整语料在数组中的顺序 |
| CE-10 | 添加绑定节点 | 点击 [+ 添加绑定] | 弹出导航节点选择器，选择后加入 bound_nodes |
| CE-11 | 移除绑定节点 | 点击节点项上的 [✕] | 从 bound_nodes 列表中移除该项 |
| CE-12 | 折叠/展开编辑面板 | 移动端点击切换按钮 | 编辑面板折叠/展开，适应小屏 |

### 2.3 关键细节

- **自动保存**：所有编辑操作即时生效，无需"保存"按钮。每次修改直接更新内存中的 `cognitiveCards` 数组
- **树列表与面板联动**：点击树中卡片 → 编辑面板加载；编辑面板中修改字段 → 树列表中的标题等同步更新
- **选中保持**：搜索过滤时，若当前选中的卡片仍在过滤结果中，保持选中和编辑面板状态
- **未选中状态**：无选中卡片时右侧显示"请从树中选择一张认知卡片"
- **语料排序**：支持拖拽调整语料的先后顺序（影响自动生成标题/描述时的优先级）
- **空语料**：corpus 为空时显示"暂无语料，点击下方添加"，[+ 新增语料] 按钮始终可见

---

## 三、数据流

### 3.1 CardEditStore（新增或并入 treeStore）

```typescript
// store/cardEditStore.ts

interface CardEditStore {
  // 编辑选中
  editingCardId: string | null
  editingCard: CognitiveCard | null   // 当前编辑的卡片副本

  // 方法
  /** 选中卡片开始编辑 */
  selectCard: (id: string) => void
  /** 更新标量字段 */
  updateField: <K extends keyof CognitiveCard>(field: K, value: CognitiveCard[K]) => void
  /** 语料库操作 */
  addCorpusItem: (text?: string) => void
  updateCorpusItem: (index: number, text: string) => void
  removeCorpusItem: (index: number) => void
  reorderCorpus: (fromIndex: number, toIndex: number) => void
  /** 绑定节点操作 */
  addBoundNode: (nodeId: string) => void
  removeBoundNode: (nodeId: string) => void
}
```

### 3.2 数据源

所有编辑操作直接修改 `src/data/cards.ts` 中的 `cognitiveCards` 数组：

```
用户编辑字段
       │
       ▼
在 cognitiveCards 中找到对应卡片并更新字段
       │
       ▼
更新 editingCard 副本（保持与源同步）
       │
       ▼
树列表中的卡片标题、图标等同步刷新
```

### 3.3 编辑面板与树列表的通信

```
TreeView
  │
  ├── SubTabBar
  │
  ├── [认知卡片子 Tab]
  │     │
  │     ├── SearchBar
  │     ├── BreadcrumbNav
  │     ├── TreeList
  │     │     └── TreeNode ← 点击触发 cardEditStore.selectCard(id)
  │     │                     → 高亮行 + 加载编辑面板
  │     │
  │     └── CardEditPanel (新增) ← 编辑字段触发 cardEditStore.updateField
  │
  └── [导航节点子 Tab] → NodeManagementView (现有)
```

---

## 四、组件结构

### 4.1 组件树

```
views/
  TreeView.tsx          ← 增强：新增 CardEditPanel 条件渲染
  TreeView.module.css   ← 增强：左右两栏布局样式

tree/
  ├── TreeList.tsx       ← 微调：选中时回调 selectCard
  ├── TreeNode.tsx
  ├── TreeBadge.tsx
  └── SubTabBar.tsx      ← 已有

card-mgr/               ← 新增目录
  ├── CardEditPanel.tsx + .module.css        ← 编辑面板主容器
  ├── CardBasicFields.tsx + .module.css      ← 基本字段（title, type, tag, desc）
  ├── CorpusEditor.tsx + .module.css          ← 语料库编辑（增删改+拖拽排序）
  ├── BoundNodesEditor.tsx + .module.css         ← 绑定节点编辑
  └── NodeSelector.tsx + .module.css         ← 复用 navNodeManager 的 NodeSelector
```

### 4.2 组件接口

```typescript
// CardEditPanelProps
interface CardEditPanelProps {
  card: CognitiveCard
}

// CardBasicFieldsProps
interface CardBasicFieldsProps {
  card: CognitiveCard
  onUpdateField: <K extends keyof CognitiveCard>(field: K, value: CognitiveCard[K]) => void
}

// CorpusEditorProps
interface CorpusEditorProps {
  corpus: string[]
  onAdd: (text?: string) => void
  onUpdate: (index: number, text: string) => void
  onRemove: (index: number) => void
  onReorder: (fromIndex: number, toIndex: number) => void
}

// BoundNodesEditorProps
interface BoundNodesEditorProps {
  boundNodeIds: string[]
  onAdd: (nodeId: string) => void
  onRemove: (nodeId: string) => void
}
```

### 4.3 目录结构变更

```
knowledge-navigator-react/src/
  components/
    card-mgr/                            ← 新增目录
      ├── CardEditPanel.tsx
      ├── CardEditPanel.module.css
      ├── CardBasicFields.tsx
      ├── CardBasicFields.module.css
      ├── CorpusEditor.tsx
      ├── CorpusEditor.module.css
      └── BoundNodesEditor.tsx
      └── BoundNodesEditor.module.css
    node-mgr/
      └── NodeSelector.tsx              ← 共享给 card-mgr 使用
    views/
      ├── TreeView.tsx                  ← 增强：左右两栏 + CardEditPanel
      └── TreeView.module.css           ← 增强
  store/
    ├── cardEditStore.ts                ← 新增：卡片编辑状态
    └── ...
```

---

## 五、编辑面板详解

### 5.1 基本字段编辑（CardBasicFields）

```
┌─────────────────────────────────┐
│  id: root/1/1            (只读)  │
│  title: [监督学习           ]    │  ← 单行输入
│  type:   [leaf         ▼]       │  ← 下拉: folder / leaf
│  tag:    [决策分支      ▼]       │  ← 下拉: 层级分类 / 决策分支
│  description:                   │
│  [使用标注数据训练模型，学习从    │  ← 多行文本域 (2-4 行)
│   输入到输出的映射函数。]        │
└─────────────────────────────────┘
```

- `id` 灰色只读文字
- `type` 切换时自动校验：切换为 leaf 时清空 children（触发确认提示）
- `tag` 以下拉为主，但允许用户输入自定义值

### 5.2 语料库编辑（CorpusEditor）

```
┌─────────────────────────────────┐
│ 【语料库】                   3 条 │
│                                 │
│ ┌─ 1 ─────────────────────────┐ │
│ │ 使用标注数据训练模型，学习     │ │  ← 可编辑多行文本
│ │ 从输入到输出的映射函数。       │ │
│ │                         [✕] │ │
│ └──────────────────────────────┘ │
│ ┌─ 2 ─────────────────────────┐ │
│ │ 常见算法包括线性回归、逻辑     │ │
│ │ 回归、SVM、决策树和神经网络。  │ │
│ │                         [✕] │ │
│ └──────────────────────────────┘ │
│                                 │
│ [+ 新增语料]                     │  ← 点击后在末尾追加空白条目
│                                 │
│ (语料用于自动生成标题/描述       │  ← 底部提示
│  及向量模型匹配)                 │
└─────────────────────────────────┘
```

- 每条语料独立的多行文本框
- 每条语料右侧有 [✕] 删除按钮
- 每条语料左侧有拖拽手柄（≡）用于拖动排序
- 新增时在末尾追加一行空文本框，自动聚焦
- 底部灰色小字提示语料用途

### 5.3 绑定节点编辑（BoundNodesEditor）

```
┌─────────────────────────────────┐
│ 【绑定导航节点】             2 个 │
│  ├ node-supervised    监督学习 [✕]│
│  ├ node-ml-foundation 机器学习 [✕]│
│  │                               │
│  [+ 添加绑定]                     │
└─────────────────────────────────┘
```

- 列表每项显示 `nodeId` + `label`（从 allNavNodes 查询）
- 点击 [✕] 移除绑定
- 点击 [+ 添加绑定] 弹出 NodeSelector（复用 node-mgr 中的组件），搜索模式，仅显示导航节点

---

## 六、与现有功能的兼容性

| 现有功能 | 兼容性 | 说明 |
|----------|--------|------|
| TreeView 树形浏览 | ✅ 扩展 | 点击行新增编辑面板联动，原有展开/折叠不受影响 |
| TreeView 搜索过滤 | ✅ 不变 | 搜索后选中卡片仍可编辑 |
| TreeView 面包屑 | ✅ 不变 | 不影响 |
| 导航节点管理 | ✅ 不变 | 作为另一个子 Tab 独立存在 |
| cognitiveCards 数据源 | ✅ 不变 | 编辑直接修改内存数组 |
| 搜索视图卡片匹配 | ✅ 同步 | 编辑卡片字段后，搜索匹配结果即时反映变更 |

---

## 七、验收标准

- [ ] 认知卡片子 Tab 中点击树列表卡片行，右侧/下方展开编辑面板
- [ ] 编辑面板加载卡片的完整字段（id 只读，其余可编辑）
- [ ] 编辑 title/description 即时生效，树列表标题同步更新
- [ ] type 下拉切换 folder / leaf
- [ ] tag 下拉 + 自定义输入
- [ ] 语料库可新增、编辑、删除，支持拖拽排序
- [ ] 新增语料时自动追加空行并聚焦
- [ ] 绑定节点列表展示 nodeId + label，可添加和移除
- [ ] 添加绑定节点时弹出 NodeSelector，搜索过滤后选中加入
- [ ] 无选中卡片时显示"请从树中选择一张认知卡片"
- [ ] 移动端布局适配（列表和编辑面板上下排列）
- [ ] 所有 TypeScript 类型定义正确，编译零错误

---

## 八、边界情况

| 场景 | 行为 |
|------|------|
| 选中卡片后立即搜索，卡片被过滤掉 | 保持选中但编辑面板显示"当前卡片已不在列表中" |
| 清空 title | 阻止保存，提示"标题不能为空" |
| 语料为空数组 | 显示"暂无语料"，[+ 新增语料] 按钮始终可见 |
| type 从 folder 切为 leaf | 若有子卡片则弹出确认"切换为叶子节点将隐藏子卡片，确认？" |
| 重复添加同一绑定节点 | 检查已存在则忽略 |
| 批量编辑多条语料 | 每条独立保存，互不影响 |
