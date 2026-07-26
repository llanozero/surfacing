import { create } from 'zustand'
import type { NavNode, NextNodeRef } from '../data/types'
import { allNavNodes, navNodeMap } from '../data/allNavNodes'
import { cognitiveCards } from '../data/cards'
import { useNavStore } from './navStore'
import { usePanelStore } from './panelStore'
import { useCardStore } from './cardStore'
import { wtCreateNode, wtDeleteNode, wtUpdateNode } from '../api/writeThrough'

export type SubTab = 'cards' | 'nodes'

interface NavNodeStore {
  /** 全部导航节点（与 data/allNavNodes 共享数据源，编辑即时同步） */
  allNodes: NavNode[]
  searchQuery: string
  selectedNodeId: string | null
  /** 管理视图子 Tab：cards = 认知卡片管理，nodes = 导航节点管理 */
  activeSubTab: SubTab
  setActiveSubTab: (tab: SubTab) => void
  setSearchQuery: (q: string) => void
  selectNode: (id: string) => void
  /** 新建导航节点（id 自动生成 node-custom-N），创建后自动选中 */
  createNavNode: () => NavNode
  /**
   * 删除当前选中节点，级联清理：
   * 其他节点的 next_nodes/browse_history 引用、卡片 bound_nodes 引用、
   * NavView 途经点/选中/当前节点、下拉面板。
   */
  deleteNavNode: () => { ok: boolean; reason?: string }
  updateField: <K extends keyof NavNode>(field: K, value: NavNode[K]) => void
  addBoundCard: (cardId: string) => void
  removeBoundCard: (cardId: string) => void
  addNextNode: (ref: NextNodeRef) => void
  updateNextNode: (targetId: string, field: keyof NextNodeRef, value: number | string) => void
  removeNextNode: (targetId: string) => void
}

/**
 * 将更新后的节点写回共享数据源（allNavNodes 数组 + navNodeMap），
 * 使 NavView 画布、搜索绑定查询等其他视图读取到最新值。
 * 当前阶段仅内存生效，YAML 持久化由后续 data-saver 实现。
 */
function commitToSource(updated: NavNode) {
  const idx = allNavNodes.findIndex((n) => n.id === updated.id)
  if (idx >= 0) allNavNodes[idx] = updated
  navNodeMap.set(updated.id, updated)
  // 远程模式：同步到后端（火忘，失败仅告警）
  wtUpdateNode(updated)
}

const clamp01 = (n: number) => Math.max(0, Math.min(1, n))

export const useNavNodeStore = create<NavNodeStore>((set, get) => {
  /** 更新当前选中节点：state 与共享数据源同步 */
  const mutateSelected = (fn: (node: NavNode) => NavNode) => {
    const { selectedNodeId, allNodes } = get()
    if (!selectedNodeId) return
    const idx = allNodes.findIndex((n) => n.id === selectedNodeId)
    if (idx < 0) return
    const updated = fn(allNodes[idx])
    commitToSource(updated)
    set({ allNodes: allNodes.map((n, i) => (i === idx ? updated : n)) })
    // 边数据可能变化（next_nodes 编辑），导航画布数据源同步
    useNavStore.getState().syncFromSource()
  }

  return {
    allNodes: allNavNodes,
    searchQuery: '',
    selectedNodeId: null,
    activeSubTab: 'cards',

    setActiveSubTab: (tab) => set({ activeSubTab: tab }),

    setSearchQuery: (q) => {
      set({ searchQuery: q })
      // 搜索即过滤：当前选中不匹配时，自动跳到第一个匹配项（无匹配则清空）
      const { selectedNodeId, allNodes } = get()
      const filtered = filterNodes(allNodes, q)
      if (selectedNodeId && !filtered.some((n) => n.id === selectedNodeId)) {
        set({ selectedNodeId: filtered[0]?.id ?? null })
      }
    },

    selectNode: (id) => set({ selectedNodeId: id }),

    createNavNode: () => {
      // id 自动生成：node-custom-N（递增且不与现有冲突）
      let n = 1
      while (navNodeMap.has(`node-custom-${n}`)) n++
      const newNode: NavNode = {
        id: `node-custom-${n}`,
        label: '新建节点',
        description: '',
        bound_cards: [],
        next_nodes: [],
      }
      allNavNodes.push(newNode)
      navNodeMap.set(newNode.id, newNode)
      set({ allNodes: [...allNavNodes], selectedNodeId: newNode.id })
      // 远程模式：同步到后端
      wtCreateNode(newNode)
      // 导航画布数据源同步（边集不变，但节点列表更新）
      useNavStore.getState().syncFromSource()
      return newNode
    },

    deleteNavNode: () => {
      const { selectedNodeId } = get()
      if (!selectedNodeId) return { ok: false, reason: '未选中节点' }
      const idx = allNavNodes.findIndex((n) => n.id === selectedNodeId)
      if (idx < 0) return { ok: false, reason: '节点不存在' }

      // 共享数据源移除
      allNavNodes.splice(idx, 1)
      navNodeMap.delete(selectedNodeId)
      // 远程模式：同步到后端（后端级联清理连接与卡片绑定）
      wtDeleteNode(selectedNodeId)

      // 级联清理：其他节点的出向连接与浏览记录
      allNavNodes.forEach((n) => {
        n.next_nodes = n.next_nodes.filter((e) => e.target_id !== selectedNodeId)
        if (n.browse_history) {
          n.browse_history = n.browse_history.filter((h) => h.from !== selectedNodeId)
        }
      })

      // 级联清理：认知卡片的绑定引用
      cognitiveCards.forEach((c) => {
        if (c.bound_nodes?.includes(selectedNodeId)) {
          c.bound_nodes = c.bound_nodes.filter((nid) => nid !== selectedNodeId)
        }
      })
      useCardStore.setState({ allCards: [...cognitiveCards] })

      // 级联清理：NavView 途经点 / 选中 / 当前节点 + 边数据重算
      const nav = useNavStore.getState()
      useNavStore.setState({
        waypoints: nav.waypoints.filter((w) => w.id !== selectedNodeId),
        ...(nav.currentNodeId === selectedNodeId
          ? { currentNodeId: allNavNodes[0]?.id ?? '' }
          : {}),
      })
      useNavStore.getState().syncFromSource()

      // 级联清理：下拉面板
      if (usePanelStore.getState().node?.id === selectedNodeId) {
        usePanelStore.getState().clearNode()
      }

      set({ allNodes: [...allNavNodes], selectedNodeId: null })
      return { ok: true }
    },

    updateField: (field, value) => {
      if (field === 'id') return // id 只读
      mutateSelected((node) => ({ ...node, [field]: value }))
    },

    addBoundCard: (cardId) => {
      const node = get().allNodes.find((n) => n.id === get().selectedNodeId)
      if (!node) return
      if (node.bound_cards?.includes(cardId)) return // 重复添加忽略
      mutateSelected((n) => ({ ...n, bound_cards: [...(n.bound_cards ?? []), cardId] }))
    },

    removeBoundCard: (cardId) => {
      mutateSelected((n) => ({
        ...n,
        bound_cards: (n.bound_cards ?? []).filter((id) => id !== cardId),
      }))
    },

    addNextNode: (ref) => {
      const node = get().allNodes.find((n) => n.id === get().selectedNodeId)
      if (!node) return
      if (node.next_nodes.some((e) => e.target_id === ref.target_id)) return
      mutateSelected((n) => ({
        ...n,
        next_nodes: [
          ...n.next_nodes,
          { ...ref, preset_weight: clamp01(ref.preset_weight), browse_weight: clamp01(ref.browse_weight) },
        ],
      }))
    },

    updateNextNode: (targetId, field, value) => {
      mutateSelected((n) => ({
        ...n,
        next_nodes: n.next_nodes.map((e) => {
          if (e.target_id !== targetId) return e
          if (field === 'preset_weight' || field === 'browse_weight') {
            return { ...e, [field]: clamp01(Number(value) || 0) }
          }
          if (field === 'connection_type') {
            return { ...e, connection_type: value as NextNodeRef['connection_type'] }
          }
          return e
        }),
      }))
    },

    removeNextNode: (targetId) => {
      mutateSelected((n) => ({
        ...n,
        next_nodes: n.next_nodes.filter((e) => e.target_id !== targetId),
      }))
    },
  }
})

/** label / description 模糊过滤 */
export function filterNodes(nodes: NavNode[], query: string): NavNode[] {
  const q = query.trim().toLowerCase()
  if (!q) return nodes
  return nodes.filter(
    (n) => n.label.toLowerCase().includes(q) || n.description.toLowerCase().includes(q),
  )
}

/** 当前编辑的节点（派生） */
export function getEditingNode(state: Pick<NavNodeStore, 'allNodes' | 'selectedNodeId'>): NavNode | null {
  return state.allNodes.find((n) => n.id === state.selectedNodeId) ?? null
}
