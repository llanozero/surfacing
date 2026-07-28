# 画布缩放控件移至右上角横向排布

## 改动

**文件**: `src/components/canvas/ZoomControls.module.css`

### 改动前

```css
.controls {
  position: absolute;
  right: 12px;
  bottom: 12px;       /* 右下角 */
  display: flex;
  flex-direction: column;  /* 纵向排列 */
  gap: 6px;
  z-index: 5;
}
```

### 改动后

```css
.controls {
  position: absolute;
  right: 12px;
  top: 12px;           /* 右上角 */
  display: flex;
  flex-direction: row; /* 横向排列 */
  gap: 6px;
  z-index: 5;
}
```

### 效果

```
┌──────────────────────────────────────┐
│                    [＋] [－] [⟳]    │  ← 右上角横向排列
│                                      │
│           (画布内容区域)               │
│                                      │
│                                      │
└──────────────────────────────────────┘
```

- `bottom: 12px` → `top: 12px`：从右下角移到右上角
- `flex-direction: column` → `row`：从纵向堆叠变为横向排列
- 其他样式（按钮大小、颜色、悬浮效果）不变

### 影响范围

- 仅 `ZoomControls.module.css` 一个文件，2 行属性变更
- `ZoomControls.tsx` 组件代码无需改动

## 编译验证

```
npx tsc --noEmit
→ exit code 0，编译零错误
```
