# Tasks

- [x] Task 1: 定义阶段门控数据和违规检测函数
  - 创建 `PHASE_GATES` 常量对象，包含每个 phaseIndex 的允许/禁制操作列表
  - 创建 `checkPhaseGate(actionName, phaseIndex)` 函数，返回 boolean
  - 创建 `getPhaseAllowedActions(phaseIndex)` 函数，返回允许操作数组
- [x] Task 2: 实现卡牌类型标签系统
  - 为 `ALL_CARDS` 添加 `phaseTag` 字段（`'action'`、`'combat'`、`'any'`）
  - phaseTag 值对应卡牌允许被使用的最早/最适合阶段
- [x] Task 3: 创建 `processPhaseGates()` 函数
  - Phase 2 → Phase 3 时：触发被动技能结算
  - Phase 3 → Phase 0 时：自动调用 `endTurnActions()`、`round++`、抽事件牌、化茧结算
- [x] Task 4: 增强 `nextPhase()` 集成阶段门控
  - 在 `phaseIndex` 切换后调用 `processPhaseGates()`
  - 移除 `nextPhase` 中已有的独立化茧结算/抽事件牌逻辑，并入 `processPhaseGates`
- [x] Task 5: 重写 `runAutoPilot()` 为阶段感知版本 + `runAllAutoPilots` 完整回合循环
  - Phase 0：跳过
  - Phase 1：激活非战斗意识 → 释放非战斗技能(R/E/I/N/S) → 资源采集摸牌
  - Phase 2：释放战斗技能(D/W) → 打出 combat 标签手牌
  - Phase 3：弃牌至上限(7张) → 不消耗行动点
  - `runAllAutoPilots` 遍历 Phase 1→2→3→0 完整循环

# Task Dependencies
- Task 3 依赖 Task 1（门控规则先定义）
- Task 4 依赖 Task 3
- Task 5 依赖 Task 4（nextPhase 先改好）和 Task 2（卡牌标签）
