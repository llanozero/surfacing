# 代打重复触发、暂停/继续与玩家选中修复 Spec

## Why

当前代打系统存在三个问题：
1. **"全部代打"只能执行一次** — 首次 `runAllAutoPilots()` 正常执行，但完成后再次点击没有反应，因为代打状态和按钮状态没有得到正确重置
2. **无暂停/继续功能** — 代打一旦启动无法中途停止观察或调整，体验不灵活
3. **点击已选玩家触发重选** — `selectPlayer` 对已选中玩家也会执行渲染和日志，导致视觉闪烁和面板操作异常

## What Changes

- `runAllAutoPilots` 结束后重置状态，允许再次点击触发
- 新增 **暂停/继续** 按钮和 UI 控制器（`PauseController`），在代打执行期间可切换
- `selectPlayer` 增加已选中判断：若 `index === gameState.activePlayerIndex`，直接 `return`
- 暂停状态通过 `gameState.autoPilotPaused` 标记控制，`runAutoPilot` 中的 `stepDelay` 循环检测暂停标记并等待

## Impact

- Affected specs: `auto-pilot-animation`（扩展其功能）
- Affected code: `桌游设计脚手架.html` — 修改 `selectPlayer`、`runAutoPilot`、`runAllAutoPilots`，新增暂停/继续 UI 和控制逻辑

## ADDED Requirements

### Requirement: `selectPlayer` 防重复选中
The system SHALL ignore selection clicks on an already-selected player.

#### Scenario: 点击已选中玩家
- **WHEN** 玩家点击当前已选中的玩家区域（黄色高亮）
- **THEN** `selectPlayer` 检测到 `index === gameState.activePlayerIndex` 并立即 `return`
- **AND** 不执行 `renderPlayers()`，不输出日志

### Requirement: 暂停/继续代打
The system SHALL provide a pause/resume mechanism during auto-pilot execution.

#### Scenario: 暂停代打
- **WHEN** 代打正在执行中（`autoPilotBusy === true`）
- **THEN** 牌桌操作栏出现 **⏸ 暂停** 按钮（替换 "全部代打" 按钮或额外添加）
- **AND** 点击后 `autoPilotPaused = true`，正在执行的 `runAutoPilot` 在下一个 `await stepDelay()` 处卡住
- **AND** 按钮变为 **▶ 继续**

#### Scenario: 继续代打
- **WHEN** 代打处于暂停状态（`autoPilotPaused === true`）
- **THEN** 点击 "▶ 继续" 按钮，`autoPilotPaused = false`
- **AND** `runAutoPilot` 从卡住处继续执行

## MODIFIED Requirements

### Requirement: `runAllAutoPilots` 可重复触发
**修改前**: 首次运行后再次点击无响应。
**修改后**: 每次 `runAllAutoPilots()` 被调用时，重置 `autoPilotBusy = false`，重新遍历所有玩家并触发代打。

## REMOVED Requirements

无
