import type { NavNode, NextNodeRef } from '../data/types'
import { getNavNode, navNodeMap, allNavNodes } from '../data/allNavNodes'
import { useNavStore } from '../store/navStore'
import { useNavNodeStore } from '../store/navNodeStore'
import { usePlanStore } from '../store/planStore'

/**
 * 途经点快捷跳转连接（quick-waypoint-connection.md）。
 * 直接修改共享数据源 allNavNodes，并同步画布边集、节点管理与候选计划。
 */

export type ConnectionStatus = 'connected' | 'missing' | 'unavailable'

export interface ConnectionStatusResult {
  status: ConnectionStatus
  ref?: NextNodeRef
}

/* ========== 优先级序号 ↔ 权重映射 ==========
 * 数据模型使用 preset_weight（降序，越大越优先），
 * UI 使用优先级序号 #N（整数，越小越优先）。
 * #1 → 1.0，#2 → 0.9，…，#10 → 0.1，#11+ → 0.05
 */
export function priorityToWeight(priority: number): number {
  const p = Math.max(1, Math.round(priority))
  return Math.max(0.05, Math.round((1 - (p - 1) * 0.1) * 100) / 100)
}

export function weightToPriority(weight: number): number {
  return Math.max(1, Math.round((1 - weight) * 10) + 1)
}

/* ========== 查询 ========== */

/** 查询 fromId → toId 的连接状态（无出向边也允许新建，统一为 missing） */
export function getConnectionStatus(fromId: string, toId: string): ConnectionStatusResult {
  const from = getNavNode(fromId)
  if (!from) return { status: 'unavailable' }
  const ref = from.next_nodes.find((e) => e.target_id === toId)
  if (ref) return { status: 'connected', ref }
  return { status: 'missing' }
}

/* ========== 变更 ========== */

/** 新建连接（不触发同步，供批量复用）。返回 true 表示新建成功 */
function ensureNoSync(fromId: string, toId: string): boolean {
  if (fromId === toId) return false
  const from = getNavNode(fromId)
  const to = getNavNode(toId)
  if (!from || !to) return false
  if (from.next_nodes.some((e) => e.target_id === toId)) return false

  from.next_nodes.push({
    target_id: toId,
    preset_weight: priorityToWeight(1),
    browse_weight: 0,
    connection_type: 'user_added',
  })
  navNodeMap.set(fromId, from)
  return true
}

/** 一键建立连接：预设优先级 #1，类型 user_added。已存在/无效返回 false */
export function ensureQuickConnection(fromId: string, toId: string): boolean {
  const created = ensureNoSync(fromId, toId)
  if (created) syncAfterMutation()
  return created
}

/** 更新已有连接的优先级序号 / 连接类型 */
export function updateQuickConnection(
  fromId: string,
  toId: string,
  updates: { preset_priority?: number; connection_type?: NextNodeRef['connection_type'] },
): boolean {
  const from = getNavNode(fromId)
  if (!from) return false
  const idx = from.next_nodes.findIndex((e) => e.target_id === toId)
  if (idx < 0) return false

  const current = from.next_nodes[idx]
  from.next_nodes[idx] = {
    ...current,
    ...(updates.preset_priority !== undefined
      ? { preset_weight: priorityToWeight(updates.preset_priority) }
      : {}),
    ...(updates.connection_type !== undefined ? { connection_type: updates.connection_type } : {}),
  }
  navNodeMap.set(fromId, from)
  syncAfterMutation()
  return true
}

/** 删除连接 */
export function removeQuickConnection(fromId: string, toId: string): boolean {
  const from = getNavNode(fromId)
  if (!from) return false
  const lenBefore = from.next_nodes.length
  from.next_nodes = from.next_nodes.filter((e) => e.target_id !== toId)
  if (from.next_nodes.length === lenBefore) return false

  navNodeMap.set(fromId, from)
  syncAfterMutation()
  return true
}

/** 批量补齐途经点序列中所有缺失的连接（仅统计新建立的），末尾统一同步一次 */
export function fillAllMissingConnections(waypoints: NavNode[]): number {
  let count = 0
  for (let i = 0; i < waypoints.length - 1; i++) {
    if (ensureNoSync(waypoints[i].id, waypoints[i + 1].id)) count++
  }
  if (count > 0) syncAfterMutation()
  return count
}

/** 变更后同步所有依赖方：画布边集、节点管理、候选计划 */
function syncAfterMutation(): void {
  useNavStore.getState().syncFromSource()
  useNavNodeStore.setState({ allNodes: [...allNavNodes] })
  const ps = usePlanStore.getState()
  if (ps.sourceWaypoints.length > 0) {
    ps.replan()
  }
}
