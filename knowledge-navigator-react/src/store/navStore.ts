import { create } from 'zustand'
import type { GraphEdge, NavNode, NamespacedNode } from '../data/types'
import { allNavNodes, allEdges, getNavNode } from '../data/allNavNodes'
import { composeWeights, type WeightedRef } from '../utils/weightUtils'
import { nsId } from '../config/graphs'
import { useGraphStore } from './graphStore'

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
  allNavNodes: NavNode[]
  allEdges: GraphEdge[]
  waypoints: NavNode[]
  freeBrowseActive: boolean

  /** 画布多选框选中的图 ID 列表 */
  selectedGraphIds: string[]

  init: (nodeId: string, mode?: NavMode) => void
  setMode: (m: NavMode) => void
  setCurrentNode: (nodeId: string) => void
  addWaypoint: (node: NavNode) => void
  removeWaypoint: (index: number) => void
  clearWaypoints: () => void
  setFreeBrowse: (active: boolean) => void
  getNextNodes: (nodeId: string) => NextNodeItem[]
  getPrevNodes: (nodeId: string) => NextNodeItem[]
  syncFromSource: () => void

  /** 设置画布选中的图列表 */
  setSelectedGraphs: (ids: string[]) => void
  /** 当前是否为多图模式 */
  isMultiGraphMode: () => boolean
  /** 获取画布应渲染的命名空间化节点列表 */
  getCanvasNodes: () => NamespacedNode[]
  /** 获取画布应渲染的命名空间化边列表 */
  getCanvasEdges: () => GraphEdge[]
}

function namespaceNodes(nodes: NavNode[], graphId: string, graphLabel: string): NamespacedNode[] {
  return nodes.map((n) => ({
    ...n,
    _nsId: nsId(graphId, n.id),
    _sourceGraphId: graphId,
    _sourceGraphLabel: graphLabel,
  }))
}

export const useNavStore = create<NavStore>((set, get) => ({
  mode: 'overview',
  currentNodeId: 'node-ml-foundation',
  allNavNodes,
  allEdges,
  waypoints: [],
  freeBrowseActive: false,
  selectedGraphIds: [],

  init: (nodeId, mode = 'overview') => {
    if (!getNavNode(nodeId)) return
    set({ currentNodeId: nodeId, mode })
  },

  setMode: (m) => set({ mode: m }),

  setCurrentNode: (nodeId) => {
    if (getNavNode(nodeId)) set({ currentNodeId: nodeId })
  },

  addWaypoint: (node) => {
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

  setSelectedGraphs: (ids) => {
    set({ selectedGraphIds: ids })
  },

  isMultiGraphMode: () => {
    return get().selectedGraphIds.length > 1
  },

  getCanvasNodes: () => {
    const { selectedGraphIds, allNavNodes: nodes } = get()
    const { graphs } = useGraphStore.getState()

    const selected = graphs.filter((g) => selectedGraphIds.includes(g.graph_id))
    if (selected.length > 0) {
      return selected.flatMap((g) => namespaceNodes(nodes, g.graph_id, g.label))
    }

    const activeId = useGraphStore.getState().activeGraphId
    const activeMeta = graphs.find((g) => g.graph_id === activeId)
    return namespaceNodes(nodes, activeId, activeMeta?.label ?? activeId)
  },

  getCanvasEdges: () => {
    const { allEdges: edges, selectedGraphIds } = get()
    if (selectedGraphIds.length > 1) {
      return edges.map((e) => ({
        ...e,
        source: nsId(selectedGraphIds[0], e.source),
        target: nsId(selectedGraphIds[0], e.target),
      }))
    }
    return edges
  },
}))

export function getCurrentNode(state: Pick<NavStore, 'currentNodeId'>): NavNode | null {
  return getNavNode(state.currentNodeId) ?? null
}
