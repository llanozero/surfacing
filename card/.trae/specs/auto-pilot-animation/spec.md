# AI 代打动画与倍速控制 Spec

## Why

当前代打模式（`runAutoPilot`）一次性执行所有 AI 决策，前端没有机会渲染中间状态（如激活意识、释放技能的过程）。玩家看不到代打的"决策过程"，体验不连贯。需要增加**操作间隔**和**倍速控制**，让代打过程可视化。

## What Changes

- `runAutoPilot` 改为异步队列执行，每个操作之间插入可配置的时间延迟
- 牌桌配置栏新增**倍速选择器**（1x / 2x / 4x / 8x），影响延迟时长
- 代打执行期间显示"🤖 代打进行中..."状态指示器
- `runAllAutoPilots` 改为串行执行（当前玩家代打完成后才开始下一位），避免 UI 阻塞
- 代打中的意识激活、技能释放、化茧宣告等操作均以"动画序列"方式逐步执行

## Impact

- Affected specs: 无（新增功能，不修改既有 spec）
- Affected code: `桌游设计脚手架.html` — 修改 JS 中的 `runAutoPilot`、`runAllAutoPilot`、`toggleAutoPilot`，新增倍速配置 UI 和状态指示器

## ADDED Requirements

### Requirement: 代打动画序列
The system SHALL execute auto-pilot actions as an asynchronous sequence with configurable delays between steps.

#### Scenario: 单玩家代打动画
- **WHEN** `runAutoPilot(pi)` 被调用
- **THEN** 系统依次执行：意识激活→技能释放→日志输出，每步之间延迟 `baseDelay / speedMultiplier` 毫秒
- **AND** 每次状态变更后调用 `renderPlayers()` 更新 UI

#### Scenario: 全部代打动画
- **WHEN** `runAllAutoPilots()` 被调用
- **THEN** 系统串行处理每个代打玩家，前一个完成后再开始下一个
- **AND** 总执行时间受倍速控制

### Requirement: 倍速控制
The system SHALL provide a speed selector that controls the execution speed of auto-pilot animations.

#### Scenario: 倍速调整
- **WHEN** 玩家在牌桌配置栏选择倍速（1x / 2x / 4x / 8x）
- **THEN** 代打操作间隔 = 基础间隔(800ms) / 倍速
- **AND** 实时生效，不需要重新启动代打

### Requirement: 代打状态指示器
The system SHALL display a status indicator when auto-pilot is executing.

#### Scenario: 代打中状态
- **WHEN** 任意玩家的代打正在执行
- **THEN** 牌桌中央区域显示 "🤖 代打进行中..." 闪烁指示器
- **AND** 所有操作按钮禁用，防止冲突
- **AND** 代打完成后指示器消失，按钮恢复

## MODIFIED Requirements

无

## REMOVED Requirements

无
