# Bugfix: 多选框勾选后画布不渲染节点

## 根因

`useNavCanvas.ts` 中 `buildOverview()` 的 `overviewBuiltRef` 守卫导致数据从空→非空时无法重建力导向图。

**调用链路**：
1. 初始状态：无选中图 → `allNodes = []` → `buildOverview()` 被调用
2. 空数组 `[]` 是 truthy，守卫 `!d.allNodes` 不触发 → 继续执行
3. 用空节点数组构建力模拟（无任何 DOM 元素）→ `overviewBuiltRef.current = true`
4. 用户勾选图后 → `allNodes` 变为 `allNavNodes`（18 个节点）
5. `buildOverview()` 再次被调用 → `overviewBuiltRef.current === true` → **立即 return**，不重建

**第二个问题**：`buildOverview()` 所在的 `useEffect` 仅监听 `[mode]`，勾选图（数据变化）不会重新触发。

## 修复

| 文件 | 行 | 变更 |
|------|-----|------|
| `useNavCanvas.ts` | 149 | `buildOverview` 增加 `d.allNodes.length === 0` 空数据守卫，不设置 `overviewBuiltRef` |
| `useNavCanvas.ts` | 394 | `useEffect` 依赖增加 `data.allNodes?.length` 和 `data.allEdges?.length`，数据从 0→N 时重新触发 |
| `useNavCanvas.ts` | 395-396 | 仅当 `overviewBuiltRef.current` 为 false 时调用 `buildOverview()` |

## 验证

- [x] 初始无勾选：画布显示空占位，力导图未构建
- [x] 勾选任一图：`allNodes.length` 从 0→18，effect 重新触发，`buildOverview()` 正常构建
- [x] 取消全部勾选：画布回到空状态
- [x] 再次勾选：力导图重新构建
- [x] 编译零 type error
- [x] Vite 生产构建通过
