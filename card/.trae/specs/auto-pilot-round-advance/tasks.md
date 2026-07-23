# Tasks

- [x] Task 1: 在 `runAllAutoPilots` 尾部追加回合推进逻辑
  - 在 for 循环结束后、日志输出前，执行回合推进：
    ```js
    gameState.phaseIndex = 0;
    gameState.round++;
    document.getElementById('roundCounter').textContent = gameState.round;
    document.getElementById('headerRound').textContent = gameState.round;
    document.getElementById('currentPhase').textContent = PHASE_NAMES[0];
    drawEventCard();
    ```
  - 日志改为：`'🤖 <span class="highlight">全部代打完成</span>，已推进至第 ' + gameState.round + ' 回合'`

# Task Dependencies
无
