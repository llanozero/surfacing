# 面板拖拽防误选文本 & 尺寸快捷控件

## 问题一：拖拽调整面板尺寸时误选文本

### 现象

在面板手柄（handleZone）上拖拽调整面板大小时，拖动鼠标经过面板内容区域的文字时，文本会被选中高亮，影响拖拽体验。

### 修复

在 `.dragging` 样式类中增加 `user-select: none`，拖拽期间禁止文本选中：

```css
.dragging {
  transition: none;
  user-select: none;
  -webkit-user-select: none;
}
```

拖拽开始时 `useDragPanel` 将 `dragging` 设为 `true`，CSS 类 `.dragging` 被添加到面板容器上，整个面板内容在拖拽期间不可选中。拖拽结束后 `dragging` 恢复 `false`，文本恢复正常可选。

---

## 问题二：增加面板尺寸快捷控件

### 需求

在面板的收起态和展开态头部，增加三个一键切换面板尺寸的快捷按钮：

| 按钮 | 对应状态 | 面板显示 |
|------|---------|---------|
| 📄 隐藏 | `collapsed` | 收起为条状，仅显示节点名和操作按钮 |
| ⊞ 半屏 | `half` | 展开，显示节点详情 + 统计，`translateY(50%)` |
| ⛶ 全屏 | `full` | 展开 + 显示绑定的卡片和下一节点列表，`translateY(0%)` |

### 改动

#### CSS (`.module.css`)

新增 `.sizeBar`、`.sizeBtn`、`.sizeBtnActive` 三个样式类：

```css
.sizeBar {
  display: flex;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
}
.sizeBtn {
  width: 28px;
  height: 28px;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--label-tertiary);
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s, color 0.15s;
}
.sizeBtn:hover {
  background: var(--fill-f1);
  color: var(--label-primary);
}
.sizeBtnActive {
  composes: sizeBtn;
  background: var(--fill-f2);
  color: var(--accent);
}
```

同时为 `.collapsedLabel` 和 `.nodeLabel` 添加 `flex: 1`，让标签文本在尺寸控件和操作按钮之间自适应占满剩余空间。

#### TSX 组件

新增尺寸按钮配置常量：

```typescript
const SIZE_BTNS: { pos: PanelPosition; label: string; title: string }[] = [
  { pos: 'collapsed', label: '📄', title: '隐藏' },
  { pos: 'half', label: '⊞', title: '半屏' },
  { pos: 'full', label: '⛶', title: '全屏' },
]
```

**收起态（collapsed bar）**：按钮组放在最左侧

```
[📄] [⊞] [⛶]  机器学习基础              [添加为途径点]
↑ 尺寸控件                   ↑ 标签（flex:1）    ↑ 操作按钮
```

**展开态（half / full header）**：按钮组放在头部右侧，与 TTS 按钮并列

```
  机器学习基础              [📄] [⊞] [⛶] [🔊]
  ↑ 标签（flex:1）    ↑ 尺寸控件          ↑ TTS
```

每个按钮点击时调用 `setPosition(b.pos)` 切换面板尺寸。当前活动的尺寸按钮应用 `.sizeBtnActive` 样式（accent 色高亮）。

### 影响范围

- 仅 `DropDownPanel.tsx` 和 `DropDownPanel.module.css` 两个文件
- 拖拽防误选：不改变功能逻辑，仅拖拽期间增加 CSS 限制
- 尺寸控件：不改变现有 `useDragPanel` 行为和 `usePanelStore` 接口，仅新增 UI 按钮
- `panelStore.ts`、`useDragPanel.ts`：无需改动

---

## 验证步骤

### 拖拽防误选

1. 打开面板展开态（half 或 full）
2. 按住面板顶部手柄拖拽调整面板大小
3. 拖拽过程中鼠标经过面板内容文字区域 → **文本不应被选中高亮**
4. 松开鼠标后 → **文本恢复正常可选中**

### 尺寸快捷控件

1. 面板展开态（half 或 full）：
   - 点击 📄 → 面板收起为 collapsed 条状
   - 再点击 ⊞ → 面板展开为 half
   - 再点击 ⛶ → 面板展开为 full（显示卡片和节点列表）
2. 面板收起态（collapsed）：
   - 点击 ⊞ → 面板展开为 half
   - 点击 ⛶ → 面板展开为 full
3. 当前尺寸按钮应高亮显示
4. 拖拽手柄吸附后，对应尺寸按钮也应正确高亮

---

## 编译验证

```
npx tsc --noEmit
→ exit code 0，编译零错误
```
