# Tasks

- [x] Task 1: 在牌桌配置栏新增倍速选择器（1x / 2x / 4x / 8x）
  - 在 config-bar 中添加 select 元素，id="speedMultiplier"
  - 值对应 {1, 2, 4, 8}，默认 1
  - 存储到 `gameState.speedMultiplier`
- [x] Task 2: 新增代打状态指示器 UI 和按钮禁用机制
  - 在牌桌中央区域（回合计数器旁）添加 `#autoPilotStatus` 元素
  - 添加 CSS 闪烁动画 `.blink`
  - 添加 `setAutoPilotBusy(isBusy)` 函数：启用/禁用所有操作按钮
- [x] Task 3: 重写 `runAutoPilot` 为异步队列执行
  - 改为 `async function runAutoPilot(pi)`
  - 将决策流程拆分为多个异步步骤，每步之间 `await delay()`
  - 意识激活步骤：逐个激活，每次激活后 render + 等待
  - 技能释放步骤：逐个释放，每次释放后 render + 等待
  - 使用 `baseDelay / gameState.speedMultiplier` 计算实际延迟
  - 进入时调用 `setAutoPilotBusy(true)`，结束时调用 `setAutoPilotBusy(false)`
- [x] Task 4: 重写 `runAllAutoPilots` 为串行异步执行
  - 改为 `async function runAllAutoPilots()`
  - for 循环逐个 await runAutoPilot(pi)
  - 每个玩家代打完成后日志输出分割线
- [x] Task 5: 更新 `nextPhase` 中对代打的调用适配异步
  - `nextPhase` 中的 `setTimeout(() => runAutoPilot(pi), 100)` 改为 `runAutoPilot(pi)`（异步函数自动入微任务队列）

# Task Dependencies
- Task 3 依赖 Task 1（倍速值）和 Task 2（状态指示器）
- Task 4 依赖 Task 3
- Task 5 依赖 Task 3
