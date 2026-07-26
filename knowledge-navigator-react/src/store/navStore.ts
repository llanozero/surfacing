import { create } from 'zustand'
import type { GraphEdge, NavNode } from '../data/types'
import { allNavNodes, allEdges, getNavNode } from '../data/allNavNodes'
import { composeWeights, type WeightedRef } from '../utils/weightUtils'

/** 由共享 allNavNodes 重新推导全量有向边 */
function deriveEdges(): GraphEdge[] {
  return allNavNodes.flatMap((n) =>
    n.next_nodes.map((e) => ({ source: n.id, target: e.target_id, weight: e.preset_weight })),
  )
}

export type NavMode = 'overview' | 'station'

export interface NextNodeItem {
  node: NavNode
  ref: WeightedRef
}

interface NavStore {
  mode: NavMode
  currentNodeId: string
  /** 全览视图中当前点击选中的节点 id（三态样式：普通/途经点/选中） */
  selectedNodeId: string | null
  allNavNodes: NavNode[]
  allEdges: GraphEdge[]
  waypoints: NavNode[]
  /** 自由分支浏览模式是否激活 */
  freeBrowseActive: boolean
  init: (nodeId: string, mode?: NavMode) => void
  setMode: (m: NavMode) => void
  setCurrentNode: (nodeId: string) => void
  setSelectedNode: (nodeId: string | null) => void
  addWaypoint: (node: NavNode) => void
  removeWaypoint: (index: number) => void
  clearWaypoints: () => void
  /** 切换自由分支浏览模式 */
  setFreeBrowse: (active: boolean) => void
  /** 按合成权重排序的后继节点 */
  getNextNodes: (nodeId: string) => NextNodeItem[]
  /** 前驱节点（指向 nodeId 的节点） */
  getPrevNodes: (nodeId: string) => NextNodeItem[]
  /** 节点增删改后，从共享数据源重算节点列表与边集 */
  syncFromSource: () => void
}

export const useNavStore = create<NavStore>((set, get) => ({
  mode: 'overview',
  currentNodeId: 'node-ml-foundation',
  selectedNodeId: null,
  allNavNodes,
  allEdges,
  waypoints: [],
  freeBrowseActive: false,

  init: (nodeId, mode = 'overview') => {
    if (!getNavNode(nodeId)) return
    set({ currentNodeId: nodeId, mode })
  },

  setMode: (m) => set({ mode: m }),

  setCurrentNode: (nodeId) => {
    if (getNavNode(nodeId)) set({ currentNodeId: nodeId })
  },

  setSelectedNode: (nodeId) => set({ selectedNodeId: nodeId }),

  addWaypoint: (node) => {
    // 允许重复（同一节点可多次经过）
    set({ waypoints: [...get().waypoints, node] })
  },

  removeWaypoint: (index) => {
    set({ waypoints: get().waypoints.filter((_, i) => i !== index) })
  },

  clearWaypoints: () => set({ waypoints: [] }),

  setFreeBrowse: (active) => set({ freeBrowseActive: active }),

  getNextNodes: (nodeId) => {
    const node = getNavNode(nodeId)
    if (!node) return []
    return composeWeights(node)
      .map((ref) => ({ node: getNavNode(ref.target_id), ref }))
      .filter((x): x is NextNodeItem => Boolean(x.node))
  },

  getPrevNodes: (nodeId) =>
    allNavNodes
      .filter((n) => n.next_nodes.some((e) => e.target_id === nodeId))
      .map((n) => {
        const raw = n.next_nodes.find((e) => e.target_id === nodeId)!
        const ref: WeightedRef = {
          ...raw,
          seq: 0,
          weight: raw.preset_weight,
          source: 'preset',
        }
        return { node: n, ref }
      }),

  syncFromSource: () => {
    set({ allNavNodes: [...allNavNodes], allEdges: deriveEdges() })
  },
}))

export function getCurrentNode(state: Pick<NavStore, 'currentNodeId'>): NavNode | null {
  return getNavNode(state.currentNodeId) ?? null
}
