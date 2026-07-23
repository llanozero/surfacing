# Tasks

- [x] Task 1: 修复 `selectPlayer` 重复选中问题
  - 在函数开头加判断：`if (index === gameState.activePlayerIndex) return;`
  - 确认点击已选玩家时不触发渲染和日志
- [x] Task 2: 修复 `runAllAutoPilots` 可重复触发
  - 在函数开头添加按钮状态重置
  - 移除 `autoPilot` 重置（保留原有状态），代打函数自身不阻挡重入
- [x] Task 3: 实现暂停/继续机制（PauseController）
  - 在 `gameState` 中添加 `autoPilotPaused: false`
  - 修改 `stepDelay` 为循环检测暂停标记：`while (gameState.autoPilotPaused) await delay(100);`
  - 添加 `toggleAutoPilotPause()` 函数，切换 `autoPilotPaused` 并更新按钮文本
- [x] Task 4: 添加暂停/继续按钮 UI
  - 在 action-row 中添加 `⏸ 暂停` 按钮（id="pauseBtn"），初始隐藏
  - `setAutoPilotBusy(true)` 时显示暂停按钮，隐藏 "全部代打" 按钮
  - `setAutoPilotBusy(false)` 时恢复
  - 暂停时按钮显示 "▶ 继续"，继续时显示 "⏸ 暂停"

# Task Dependencies
- Task 3 依赖 Task 4（按钮先存在）
- Task 4 是 UI 任务，可先于 Task 3 的 JS 逻辑完成
