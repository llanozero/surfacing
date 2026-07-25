# 五 Tab 布局 — 功能规范

## 版本

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| 1.0 | 2026-07-25 | — | 初始规范：底部 TabBar 从 4 Tab 扩展为 5 Tab，"规划"作为中间第三个固定 Tab |

---

## 一、概述

### 1.1 目标

将底部 TabBar 从现有的 4 个 Tab 扩展为 **5 个 Tab**，将"规划"（PlanView）从过渡视图升级为**独立可切换的持久视图**，置于中间第 3 位。

```
当前 4 Tab 布局:
  搜索 → 导航 → 浏览 → 管理

变更后 5 Tab 布局:
  搜索 → 导航 → 规划 → 浏览 → 管理
                    ↑
                新增 (中间)
```

### 1.2 变更动机

- 路线规划视图不再是"导航→浏览"之间的过渡面板，而是用户可随时切换查看、重新规划的独立页面
- 规划视图需要持久保持其状态（候选计划列表、选中计划），即便切换到其他 Tab 再返回也不丢失
- 四个 Tab 改为五个后，视觉上 Tab 栏更均衡，"规划"居于中心位置符合认知焦点

---

## 二、TabBar 变更

### 2.1 Tab 顺序

| 序号 | 名称 | ViewName | 说明 |
|------|------|----------|
| 1 | 搜索 | `search` 不变 |
| 2 | 导航 | `nav` 不变 |
| 3 | **规划** | `plan` **新增，居中** |
| 4 | 浏览 | `browse` 原有第 3 → 第 4 |
| 5 | 管理 | `tree` 原有第 4 → 第 5 |

### 2.2 TabBar 代码变更

```typescript
// TabBar.tsx — 新增 PlanIcon

const PlanIcon: React.FC<{ size?: number; className?: string }> = ({ size = 20, className }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor"
    strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
  </svg>
)

const tabs: TabDef[] = [
  { name: 'search', label: '搜索', icon: SearchIcon },
  { name: 'nav',    label: '导航', icon: RouteIcon },
  { name: 'plan',   label: '规划', icon: PlanIcon },    // ← 新增，第 3 位
  { name: 'browse', label: '浏览', icon: PlayIcon },
  { name: 'tree',   label: '管理', icon: FolderTreeIcon },
]
```

### 2.3 键盘快捷键变更

当前快捷键：`1` → search, `2` → nav, `3` → browse, `4` → tree

变更后快捷键：`1` → search, `2` → nav, `3` → plan, `4` → browse, `5` → tree

```typescript
// App.tsx
const keys: Record<string, ViewName> = {
  '1': 'search',
  '2': 'nav',
  '3': 'plan',     // ← 变更: 从 browse 改为 plan
  '4': 'browse',   // ← 变更: 从 tree 改为 browse
  '5': 'tree',     // ← 新增
}
```

---

## 三、ViewStore 与视图注册

### 3.1 viewStore 当前状态

`ViewName` 已包含 `'plan'`：

```typescript
export type ViewName = 'search' | 'nav' | 'plan' | 'browse' | 'tree'
```

无需修改。

### 3.2 App.tsx 注册

当前已注册 PlanView：

```typescript
const viewMap: Record<ViewName, React.FC> = {
  search: SearchView,
  nav: NavView,
  plan: PlanView,      // ← 已有
  browse: BrowseView,
  tree: TreeView,
}
```

无需修改。

---

## 四、规划视图状态持久化

### 4.1 状态保持规则

规划视图从过渡视图变为持久 Tab 后，状态管理规则更新：

| 场景 | 旧行为（过渡视图） | 新行为（持久 Tab） |
|------|-------------------|-------------------|
| 切换到其他 Tab 再返回 | 清空 planStore | 保持候选计划和选中状态不变 |
| 从 NavView 点击"规划路线" | 重新生成计划 | 重新生成计划（用户意图是更新路线） |
| 切换 Tab 后修改了 navStore 的途经点 | 不受影响 | 下次进入 plan 时不清除旧计划，但显示"途经点已变更，建议重新规划"提示条 |
| PlanView 中完成浏览后返回 | 清空 planStore | 保留计划结果，用户可手动重新规划 |

### 4.2 新增"途经点已变更"提示

当用户从 plan Tab 切换到 nav Tab 修改了途经点，再切回 plan Tab 时，检测到 `sourceWaypoints` 与当前 navStore 的 `waypoints` 不一致，显示提示条：

```
┌──────────────────────────────────────────┐
│ ⚠ 途经点已变更，建议重新规划  [重新规划]  │  ← 黄色提示条
└──────────────────────────────────────────┘
```

### 4.3 不再自动重置

PlanStore 的 `reset()` 方法仅在以下场景调用：
- 用户点击"重新规划"按钮
- 用户手动清空途经点后重新规划
- 应用初始化

切换 Tab **不再触发** reset。

---

## 五、NavView → PlanView 的触发调整

### 5.1 "规划路线"按钮行为

当前 NavView 中的"规划路线"按钮调用 `switchView('plan')`，行为保持不变。

新增：点击"规划路线"时，若 `planStore` 中已有旧计划且途经点未变更，显示确认弹窗：

```
途经点未变更，是否使用上次的规划结果？
[使用上次]  [重新规划]
```

- 点击"使用上次" → 直接切换到 plan Tab，不重新生成
- 点击"重新规划" → 调用 `generatePlans()` 重新生成后切换到 plan Tab

### 5.2 游览完成后回到规划

浏览完成后（BrowseView 中点击"返回"），若之前是从 plan 进入的浏览，则回到 plan 视图而非 nav 视图：

```typescript
// BrowseView.tsx
const handleBack = () => {
  // 记录上一视图来源
  const prevView = useViewStore.getState().activeView
  // 实际由 viewStore 管理浏览历史
  switchView(previousView)  // 回到 plan 或 nav
}
```

需要在 viewStore 中维护一个简单的浏览历史栈：

```typescript
interface ViewStore {
  activeView: ViewName
  viewHistory: ViewName[]   // 视图切换历史，最多 2 层
  switchView: (name: ViewName) => void
  goBack: () => void        // 回到上一个视图
}
```

---

## 六、5 Tab 的视觉适配

### 6.1 Tab 按钮宽度

5 个 Tab 时每个按钮宽度为 20%（`flex: 1`），与 4 Tab 时的 25% 相比略窄，文字仍可正常显示：

| Tab 数 | 每项宽度 | 图标+文字 |
|--------|---------|-----------|
| 4 Tab | 25% | 充裕 |
| 5 Tab | 20% | 紧凑但仍可显示 |

现有 CSS 的 `flex: 1` 无需修改，自动适配。

### 6.2 图标选择

规划 Tab 的图标使用折线图/路线图风格，与"规划"的语义匹配：

```
<svg> — 折线图/polyline 风格
  从左上到右下的上升折线，代表"规划"和"趋势"的意象
```

现有 `flex: 1` + `flex-direction: column` 布局自动适配 5 项。

### 6.3 激活态高亮

与现有 Tab 一致：激活时文字和图标变为 `var(--status-kimiblue)` 蓝色高亮。

---

## 七、与 route-planning-view.md 的差异说明

| 项目 | route-planning-view.md (v1.1) | 本规范 (5 Tab) |
|------|------|------|
| PlanView 定位 | 过渡视图，不加入 TabBar | 持久视图，加入 TabBar 第 3 位 |
| planStore 重置时机 | 切换 Tab 时清空 | 切换 Tab **保持**，仅在用户主动操作时重置 |
| 键盘快捷键 | 3 → browse, 4 → tree | 3 → plan, 4 → browse, 5 → tree |
| 视图切换来源 | 仅从 NavView 进入 | 可从 TabBar、NavView、键盘快捷键进入 |
| 状态持久化 | 无 | planStore 状态跨 Tab 保持 |
| 途经点变更检测 | 无 | 新增检测 + 提示条 |

---

## 八、验收标准

- [ ] 底部 TabBar 显示 5 个 Tab：搜索、导航、**规划**、浏览、管理
- [ ] 规划 Tab 位于中间第 3 位，图标为折线图样式
- [ ] 点击规划 Tab 切换到 PlanView
- [ ] 键盘 1-5 分别对应 5 个 Tab
- [ ] 从 plan Tab 切换到其他 Tab 再返回，候选计划和选中状态保持不变
- [ ] 从 nav Tab 修改途经点后回到 plan Tab，显示"途经点已变更"提示条
- [ ] 点击"重新规划"按钮重新生成计划
- [ ] 从 BrowseView 返回时，若来自 plan 则回到 plan，若来自 nav 则回到 nav
- [ ] 5 个 Tab 在移动端正常显示，无布局溢出
- [ ] 所有 TypeScript 类型定义正确，编译零错误

---

## 九、与现有功能的兼容性

| 现有功能 | 兼容性 | 说明 |
|----------|--------|------|
| 4 Tab 布局 | 🔄 替换 | 升级为 5 Tab |
| PlanView 内容 | ✅ 不变 | 仅定位从过渡变为持久 |
| NavView → PlanView 跳转 | ✅ 不变 | 行为一致，新增可选"使用上次" |
| BrowseView 返回逻辑 | ✅ 扩展 | 新增视图历史栈，支持回到 plan |
| 键盘快捷键 1-4 | 🔄 变更 | 3→plan, 4→browse, 5→tree |
| planStore | ✅ 扩展 | 新增持久化规则 + 途经点变更检测 |
