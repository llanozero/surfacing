import type { NavNode, NextNodeRef } from '../data/types'

export interface WeightedRef extends NextNodeRef {
  /** 合成后的排序序号（0 起，越小优先级越高） */
  seq: number
  /** 用于展示/渲染的合成权重 */
  weight: number
  source: 'override' | 'preset' | 'browse'
}

/**
 * 权重合成算法（data-model.md §二）：
 * 1. user_overrides 命中的连接优先级最高，直接使用覆盖权重；
 * 2. 其余按 preset_weight 降序排列（起始序号 preset_priority）；
 * 3. 序列尾部按 browse_weight 降序拼接（起始序号 browse_priority）；
 * 4. mode === 'user_only' 时仅使用预设权重。
 */
export function composeWeights(node: NavNode): WeightedRef[] {
  const cfg = node.priority_config
  const mode = cfg?.mode ?? 'mixed'
  const presetPriority = cfg?.preset_priority ?? 0
  const browsePriority = cfg?.browse_priority ?? node.next_nodes.length
  const overrides = cfg?.user_overrides ?? []

  const result: WeightedRef[] = []
  const overridden = new Set<string>()

  overrides.forEach((o, i) => {
    const ref = node.next_nodes.find((n) => n.target_id === o.target_id)
    if (!ref) return
    overridden.add(o.target_id)
    result.push({ ...ref, seq: i, weight: o.override_weight, source: 'override' })
  })

  const rest = node.next_nodes.filter((n) => !overridden.has(n.target_id))

  const byPreset = [...rest].sort((a, b) => b.preset_weight - a.preset_weight)
  byPreset.forEach((ref, i) => {
    result.push({ ...ref, seq: presetPriority + i, weight: ref.preset_weight, source: 'preset' })
  })

  if (mode === 'mixed') {
    const byBrowse = [...rest].sort((a, b) => b.browse_weight - a.browse_weight)
    byBrowse.forEach((ref, i) => {
      result.push({ ...ref, seq: browsePriority + i, weight: ref.browse_weight, source: 'browse' })
    })
  }

  // 同一 target 取序号最小者作为代表
  const best = new Map<string, WeightedRef>()
  result.forEach((r) => {
    const cur = best.get(r.target_id)
    if (!cur || r.seq < cur.seq) best.set(r.target_id, r)
  })

  return [...best.values()].sort((a, b) => a.seq - b.seq)
}
