# 阶段门控操作与代打阶段感知 Spec

## Why

当前代打系统（`runAutoPilot`）只激活意识和释放技能，与游戏的 4 阶段回合流程完全脱节：
- 代打不知道当前处于哪个阶段，不应做什么操作
- 出牌、摸牌、弃牌等操作在所有阶段都可执行，缺少阶段约束
- 技能（意识主动技能）和卡牌（手牌效果）混用，没有区分阶段和用途
- 代打结束后直接推进回合，跳过了中间的博弈对抗（Phase 2）和内省调整（Phase 3）阶段

需要一套**阶段门控系统**：每个阶段只解封对应的操作类型，代打 AI 根据当前阶段执行允许的操作，并在适当时候推进阶段。

## What Changes

- 定义一套 **Phase Gate（阶段门控）** 规则表：每个 Phase 解锁特定操作类型
- `nextPhase()` 调用时自动根据当前阶段执行对应的批量操作
- 代打 AI 改为**阶段感知**：感知当前 phaseIndex，只执行该阶段允许的操作
- 新增 `processPhaseGates()` 函数，在 `nextPhase()` 中调用
- 摸牌（Draw）、主动出牌（Play）、被动触发（Trigger）、弃牌（Discard）四类操作绑定到具体阶段
- 意识技能（Active Skill）和卡牌效果（Card Effect）分属不同阶段

## Impact

- Affected specs: `auto-pilot-animation`、`auto-pilot-fixes`、`auto-pilot-round-advance`（阶段门控将取代原有的简单代打逻辑）
- Affected code: `桌游设计脚手架.html` — 修改 `nextPhase`、`runAutoPilot`、新增 `processPhaseGates` 函数

## ADDED Requirements

### Requirement: 阶段门控规则表
The system SHALL enforce phase-gated operations based on the current phase index.

#### 门控规则定义

| Phase | 索引 | 允许操作 | 禁制操作 |
|-------|------|---------|---------|
| 📜 事件翻牌 | 0 | 无（系统自动翻牌） | 摸牌、出牌、技能、弃牌、攻击 |
| 🎭 身份行动 | 1 | 摸牌(资源采集)、质疑、密语、宣告化茧、**使用策略/资源类手牌**、**使用意识主动技能** | 打出攻击牌、反击 |
| ⚔️ 博弈对抗 | 2 | 打出**攻击/防御/干预类手牌**、结算伤害、使用**战斗相关意识技能**（D盾/W共鸣） | 摸牌、资源采集、密语 |
| 🧠 内省调整 | 3 | 弃牌(手牌上限检查)、调整子人格、被动技能触发、化茧计数 | 摸牌、出牌、攻击、使用主动技能 |

#### Scenario: 跨阶段违规操作
- **WHEN** 玩家（或代打 AI）尝试在当前阶段执行被禁制的操作
- **THEN** 系统拦截该操作并输出日志 `⚠️ [操作名] 不能在 [阶段名] 阶段执行`
- **AND** 该操作不生效，不消耗行动点/资源

### Requirement: 代数阶段感知
The system SHALL make the auto-pilot aware of the current phase and only perform phase-allowed actions.

#### Scenario: 代打执行阶段适配
- **WHEN** `runAutoPilot(pi)` 被调用
- **THEN** 读取 `gameState.phaseIndex`
- **AND** 根据 phaseIndex 决定要执行的操作列表：
  - Phase 0：跳过（无操作可执行）
  - Phase 1：激活意识 + 释放主动技能 + 摸牌（资源采集）
  - Phase 2：释放战斗技能 + 使用攻击/防御手牌（若有）
  - Phase 3：弃牌（若手牌 > 上限） + 不执行任何消耗性操作
- **AND** 执行完毕后调用 `nextPhase()` 推进到下一个阶段

#### Scenario: 全部代打完整回合
- **WHEN** `runAllAutoPilots()` 被调用
- **THEN** AI 依次经历 Phase 1 → Phase 2 → Phase 3 → 回合结算 → 推进至下一轮 Phase 0
- **AND** 每个阶段执行对应的群组操作

### Requirement: 卡牌阶段操作规则
The system SHALL define when cards can be drawn, played, triggered, and discarded.

| 操作 | 允许阶段 | 说明 |
|------|---------|------|
| 🃏 摸牌（抽牌堆） | Phase 1（资源采集行动） | 消耗 1 行动点，从公共牌堆抽 1 张 |
| 🃏 摸牌（事件牌） | Phase 0（系统自动） | 自动抽取事件牌池，不消耗行动点 |
| 🎯 主动出牌（策略/资源类） | Phase 1 | 手牌中标注 `[策略]` `[资源]` 类型的卡牌 |
| ⚔️ 主动出牌（攻击/防御/干预类） | Phase 2 | 手牌中标注 `[攻击]` `[防御]` `[干预]` 类型的卡牌 |
| 💤 被动触发 | Phase 1/2/3 | 事件牌在 Phase 0 触发；被动技能在对应阶段自动触发 |
| ♻️ 弃牌 | Phase 3（手牌上限检查） | 手牌超过上限（默认 7 张）时强制弃至上限 |
| ♻️ 主动弃牌 | 任意阶段 | 玩家可随时弃掉手牌，但不恢复行动点 |

### Requirement: 自动阶段批量处理
The system SHALL automatically execute phase-appropriate batch operations when `nextPhase()` is called.

#### Scenario: 推进到 Phase 2（博弈对抗）
- **WHEN** `nextPhase()` 被调用且新的 phaseIndex === 2
- **THEN** 系统自动执行：抽取 1 张"博弈事件牌"（若有）→ 通知所有玩家进入战斗阶段

#### Scenario: 推进到 Phase 3（内省调整）
- **WHEN** `nextPhase()` 被调用且新的 phaseIndex === 3
- **THEN** 系统自动执行：触发被动技能结算 → 子人格调整提示 → 化茧倒计时

#### Scenario: Phase 3 → Phase 0（新回合）
- **WHEN** `nextPhase()` 被调用且新的 phaseIndex === 0（从 3 回绕）
- **THEN** 系统自动执行：回合结算（`endTurnActions()`）→ round++ → 抽取事件牌

## MODIFIED Requirements

### Requirement: `nextPhase()` 增强
**修改前**: `nextPhase()` 仅切换 phaseIndex 和更新显示，在 phaseIndex===0 时处理化茧结算。
**修改后**: `nextPhase()` 在切换 phaseIndex 后调用 `processPhaseGates()` 执行该阶段的自动批处理操作。在 phaseIndex 从 3→0 回绕时自动调用 `endTurnActions()`。

### Requirement: `runAutoPilot()` 阶段感知
**修改前**: `runAutoPilot()` 固定执行"激活意识→释放技能"两个步骤。
**修改后**: `runAutoPilot()` 读取 `phaseIndex`，按阶段权限表执行对应操作。Phase 0 跳过，Phase 1 专注技能/资源，Phase 2 专注战斗，Phase 3 专注弃牌/整理。

## REMOVED Requirements

无
