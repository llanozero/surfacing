import { create } from 'zustand'
import type { NavNode } from '../data/types'
import {
  generateRoutePlans,
  type RoutePlan,
  type WaypointMode,
  type WeightMode,
} from '../utils/routePlanner'

interface PlanStore {
  sourceWaypoints: NavNode[]
  waypointMode: WaypointMode
  weightMode: WeightMode
  plans: RoutePlan[]
  selectedPlanId: string | null
  /** 切换排序模式，自动重新生成计划（spec §4.2） */
  setWaypointMode: (mode: WaypointMode) => void
  /** 设置权重模式（混合 / 纯用户）；已有途经点时自动重算 */
  setWeightMode: (mode: WeightMode) => void
  /** 从途经点生成候选路线计划（重置为默认无序模式） */
  generatePlans: (waypoints: NavNode[], weightMode: WeightMode) => void
  selectPlan: (id: string) => void
  /** 按当前模式与已存途经点重新执行算法 */
  replan: () => void
  /** 返回所选计划的节点序列，供 browseStore.initFromSequence 消费 */
  enterBrowse: () => NavNode[]
  reset: () => void
}

/** 默认选中总权重最高（推荐）的计划 */
function defaultSelection(plans: RoutePlan[]): string | null {
  return plans.find((p) => p.isRecommended)?.id ?? plans[0]?.id ?? null
}

export const usePlanStore = create<PlanStore>((set, get) => ({
  sourceWaypoints: [],
  waypointMode: 'unordered',
  weightMode: 'mixed',
  plans: [],
  selectedPlanId: null,

  setWaypointMode: (mode) => {
    if (get().waypointMode === mode) return
    const { sourceWaypoints, weightMode, plans, selectedPlanId } = get()
    const prevSeq = plans.find((p) => p.id === selectedPlanId)?.sequence.map((n) => n.id).join('>')
    const output = generateRoutePlans(sourceWaypoints, weightMode, mode)
    // 选中保持：相同序列在新列表中仍存在则保持选中（spec §2.3）
    let selected = defaultSelection(output.plans)
    if (prevSeq) {
      const same = output.plans.find((p) => p.sequence.map((n) => n.id).join('>') === prevSeq)
      if (same) selected = same.id
    }
    set({ waypointMode: mode, plans: output.plans, selectedPlanId: selected })
  },

  setWeightMode: (mode) => {
    if (get().weightMode === mode) return
    set({ weightMode: mode })
    // 已有途经点（无论是否已生成计划）→ 按新权重模式重算
    if (get().sourceWaypoints.length > 0) get().replan()
  },

  generatePlans: (waypoints, weightMode) => {
    // 每次重新进入：重置为默认无序模式（spec §九 边界情况）
    const output = generateRoutePlans(waypoints, weightMode, 'unordered')
    set({
      sourceWaypoints: [...waypoints],
      weightMode,
      waypointMode: 'unordered',
      plans: output.plans,
      selectedPlanId: defaultSelection(output.plans),
    })
  },

  selectPlan: (id) => set({ selectedPlanId: id }),

  replan: () => {
    const { sourceWaypoints, weightMode, waypointMode } = get()
    const output = generateRoutePlans(sourceWaypoints, weightMode, waypointMode)
    set({ plans: output.plans, selectedPlanId: defaultSelection(output.plans) })
  },

  enterBrowse: () => {
    const { plans, selectedPlanId } = get()
    const plan = plans.find((p) => p.id === selectedPlanId)
    return plan ? [...plan.sequence] : []
  },

  reset: () =>
    set({
      sourceWaypoints: [],
      waypointMode: 'unordered',
      weightMode: 'mixed',
      plans: [],
      selectedPlanId: null,
    }),
}))
