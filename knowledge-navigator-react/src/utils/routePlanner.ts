import type { NavNode } from '../data/types'
import { getNavNode } from '../data/allNavNodes'

export type WaypointMode = 'ordered' | 'unordered'
export type WeightMode = 'mixed' | 'user_only'

export interface RoutePlan {
  id: string // 'plan-0', 'plan-1', ...
  label: string // 'Plan A', 'Plan B', ...
  sequence: NavNode[]
  totalWeight: number
  algorithm: 'permutation' | 'greedy' | 'connection' | 'subpath'
  isRecommended: boolean
}

export interface PlanOutput {
  plans: RoutePlan[]
  sourceWaypoints: NavNode[]
  waypointMode: WaypointMode
}

const PLAN_LABELS = ['Plan A', 'Plan B', 'Plan C', 'Plan D', 'Plan E', 'Plan F']
/** 全排列算法的途经点数量上限（7! = 5040，前端可承受） */
const PERMUTATION_LIMIT = 7

/**
 * 查询 from → to 的合成连接权重（spec §3.3）。
 * mixed: 预设与浏览权重取均值；user_only: 仅预设权重。无直接连接返回 0。
 */
export function getConnectionWeight(from: NavNode, to: NavNode, mode: WeightMode): number {
  const ref = from.next_nodes.find((n) => n.target_id === to.id)
  if (!ref) return 0
  if (mode === 'user_only') return ref.preset_weight
  return (ref.preset_weight + ref.browse_weight) / 2
}

/** 一条序列的累积权重和 */
function sequenceWeight(seq: NavNode[], mode: WeightMode): number {
  let sum = 0
  for (let i = 0; i < seq.length - 1; i++) {
    sum += getConnectionWeight(seq[i], seq[i + 1], mode)
  }
  return sum
}

const seqKey = (seq: NavNode[]) => seq.map((n) => n.id).join('>')

/** 枚举全部排列（n ≤ PERMUTATION_LIMIT） */
function permutations<T>(arr: T[]): T[][] {
  if (arr.length <= 1) return [arr]
  const out: T[][] = []
  arr.forEach((item, i) => {
    const rest = [...arr.slice(0, i), ...arr.slice(i + 1)]
    for (const p of permutations(rest)) out.push([item, ...p])
  })
  return out
}

/* ---------- 算法一：贪心前进（仅无序模式，spec §3.4） ---------- */
function greedyForward(waypoints: NavNode[], mode: WeightMode): NavNode[] {
  const remaining = [...waypoints]
  const seq: NavNode[] = [remaining.shift()!]
  let current = seq[0]
  while (remaining.length > 0) {
    let bestIdx = -1
    let bestW = 0
    remaining.forEach((w, i) => {
      const weight = getConnectionWeight(current, w, mode)
      if (weight > bestW) {
        bestW = weight
        bestIdx = i
      }
    })
    // 无直接连接时按剩余添加顺序补偿
    const next = bestIdx >= 0 ? remaining.splice(bestIdx, 1)[0] : remaining.shift()!
    seq.push(next)
    current = next
  }
  return seq
}

/* ---------- 算法二：全排列最优（仅无序模式，spec §3.5） ---------- */
function permutationOptimal(waypoints: NavNode[], mode: WeightMode, topK: number): NavNode[][] {
  const scored = permutations(waypoints).map((seq) => ({ seq, w: sequenceWeight(seq, mode) }))
  scored.sort((a, b) => b.w - a.w)
  const seen = new Set<string>()
  const out: NavNode[][] = []
  for (const { seq } of scored) {
    const key = seqKey(seq)
    if (seen.has(key)) continue
    seen.add(key)
    out.push(seq)
    if (out.length >= topK) break
  }
  return out
}

/* ---------- 算法三：衔接优先 DFS（仅无序模式，spec §3.6） ---------- */
function connectionPriority(waypoints: NavNode[], mode: WeightMode, topK: number): NavNode[][] {
  const results: { seq: NavNode[]; w: number }[] = []

  if (waypoints.length <= PERMUTATION_LIMIT) {
    // 从每个途经点出发 DFS，追踪访问全部途经点的累积权重最高路径
    const dfs = (current: NavNode, visited: NavNode[], weight: number) => {
      if (visited.length === waypoints.length) {
        results.push({ seq: [...visited], w: weight })
        return
      }
      for (const next of waypoints) {
        if (visited.includes(next)) continue
        dfs(next, [...visited, next], weight + getConnectionWeight(current, next, mode))
      }
    }
    waypoints.forEach((start) => dfs(start, [start], 0))
  } else {
    // n 过大时降级：从每个起点贪心
    waypoints.forEach((start) => {
      const rest = waypoints.filter((w) => w !== start)
      const seq = greedyForward([start, ...rest], mode)
      results.push({ seq, w: sequenceWeight(seq, mode) })
    })
  }

  results.sort((a, b) => b.w - a.w)
  const seen = new Set<string>()
  const out: NavNode[][] = []
  for (const { seq } of results) {
    const key = seqKey(seq)
    if (seen.has(key)) continue
    seen.add(key)
    out.push(seq)
    if (out.length >= topK) break
  }
  return out
}

/* ---------- 有序模式：子路径拼接（spec §3.2 / §3.7） ---------- */

/** 查找 from → to 经过一个中间节点的最优间接路径 */
function bestIntermediate(from: NavNode, to: NavNode, mode: WeightMode, exclude: Set<string>): NavNode | null {
  let best: NavNode | null = null
  let bestW = 0
  for (const ref of from.next_nodes) {
    if (exclude.has(ref.target_id)) continue
    const mid = getNavNode(ref.target_id)
    if (!mid) continue
    const w1 = mode === 'user_only' ? ref.preset_weight : (ref.preset_weight + ref.browse_weight) / 2
    const w2 = getConnectionWeight(mid, to, mode)
    if (w1 > 0 && w2 > 0 && w1 + w2 > bestW) {
      bestW = w1 + w2
      best = mid
    }
  }
  return best
}

/**
 * 有序模式生成策略：
 * 1. 相邻途经点对 (Wᵢ → Wᵢ₊₁) 优先保持直接连接
 * 2. 直接连接权重 = 0 时查找 1 个中间跳转节点
 * 3. 输出 Plan A（含中转插入）与 Plan B（原始顺序直拼，若不同）
 */
function subpathStitching(waypoints: NavNode[], mode: WeightMode): { seq: NavNode[]; algorithm: 'subpath' }[] {
  const stitched: NavNode[] = [waypoints[0]]
  for (let i = 0; i < waypoints.length - 1; i++) {
    const from = waypoints[i]
    const to = waypoints[i + 1]
    if (getConnectionWeight(from, to, mode) === 0) {
      const exclude = new Set(waypoints.map((w) => w.id))
      const mid = bestIntermediate(from, to, mode, exclude)
      if (mid && !stitched.includes(mid)) stitched.push(mid)
      // 无间接路径：保留原始顺序，该段权重记 0
    }
    stitched.push(to)
  }

  const results: { seq: NavNode[]; algorithm: 'subpath' }[] = [{ seq: stitched, algorithm: 'subpath' }]
  // 若拼接结果与原始顺序不同，补充一条原始顺序计划作对比
  if (seqKey(stitched) !== seqKey(waypoints)) {
    results.push({ seq: [...waypoints], algorithm: 'subpath' })
  }
  return results
}

/* ---------- 候选计划生成（spec §3.7） ---------- */
export function generateRoutePlans(
  waypoints: NavNode[],
  weightMode: WeightMode,
  waypointMode: WaypointMode,
): PlanOutput {
  const candidates: { seq: NavNode[]; algorithm: RoutePlan['algorithm'] }[] = []

  if (waypointMode === 'ordered') {
    subpathStitching(waypoints, weightMode).forEach((c) => candidates.push(c))
  } else {
    // 无序模式
    if (waypoints.length <= PERMUTATION_LIMIT) {
      permutationOptimal(waypoints, weightMode, 2).forEach((seq) =>
        candidates.push({ seq, algorithm: 'permutation' }),
      )
      candidates.push({ seq: greedyForward(waypoints, weightMode), algorithm: 'greedy' })
      // Permutation 与 Greedy 不足 3 条时用 Connection Priority 补充
      if (candidates.length < 3) {
        connectionPriority(waypoints, weightMode, 3).forEach((seq) =>
          candidates.push({ seq, algorithm: 'connection' }),
        )
      }
    } else {
      candidates.push({ seq: greedyForward(waypoints, weightMode), algorithm: 'greedy' })
      connectionPriority(waypoints, weightMode, 2).forEach((seq) =>
        candidates.push({ seq, algorithm: 'connection' }),
      )
    }
  }

  // 去重（序列完全一致仅保留一条）
  const seen = new Set<string>()
  const unique = candidates.filter((c) => {
    const key = seqKey(c.seq)
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })

  // 全部途经点之间无直接连接 → 仅提供按添加顺序的唯一计划（边界情况 §九）
  const anyConnection = unique.some((c) => sequenceWeight(c.seq, weightMode) > 0)
  const finalCandidates = anyConnection
    ? unique
    : [{ seq: [...waypoints], algorithm: 'subpath' as const }]

  // 按累积权重降序、标注推荐
  const scored = finalCandidates
    .map((c) => ({ ...c, total: sequenceWeight(c.seq, weightMode) }))
    .sort((a, b) => b.total - a.total)

  const plans: RoutePlan[] = scored.map((c, i) => ({
    id: `plan-${i}`,
    label: PLAN_LABELS[i] ?? `Plan ${i + 1}`,
    sequence: c.seq,
    totalWeight: c.total,
    algorithm: c.algorithm,
    isRecommended: i === 0,
  }))

  return { plans, sourceWaypoints: [...waypoints], waypointMode }
}
