# 全部代打完成后自动推进回合 Spec

## Why

当前 `runAllAutoPilot` 依次执行所有玩家的 AI 决策后，仅输出日志"全部代打完成"，不推进游戏回合。用户期望的流程是：执行"回合结算"后点击"全部代打"→ AI 自动完成剩余操作 → 回合自动推进到下一轮。但实际回合计数器不增加，导致代打与手动操作脱节。

## What Changes

- `runAllAutoPilots` 在所有玩家代打完成后，自动推进到下一回合
- 推进逻辑：将 `phaseIndex` 推进到 0（事件翻牌阶段），触发 `gameState.round++`
- 更新回合/阶段显示，触发事件牌抽取

## Impact

- Affected specs: `auto-pilot-fixes`、`auto-pilot-animation`
- Affected code: `桌游设计脚手架.html` — 修改 `runAllAutoPilots` 尾部，追加回合推进逻辑

## ADDED Requirements

### Requirement: 代打结束后自动推进回合
The system SHALL advance to the next round after all auto-piloted players have finished their actions.

#### Scenario: 全部代打完成 → 新回合
- **WHEN** `runAllAutoPilots()` 的 for 循环结束（所有代打玩家执行完毕）
- **THEN** 系统自动调用回合推进逻辑：将 `phaseIndex` 置 0，`gameState.round++`
- **AND** 更新 `roundCounter`、`headerRound`、`currentPhase` 显示
- **AND** 自动抽取新的事件牌
- **AND** 清空当前事件牌显示（为新回合做准备）

## MODIFIED Requirements

### Requirement: `runAllAutoPilots` 尾部追加推进逻辑
**修改前**: 循环结束后仅输出 "全部代打完成"。
**修改后**: 循环结束后执行回合推进 → 输出 "全部代打完成，已推进至第 N 回合"。

## REMOVED Requirements

无
