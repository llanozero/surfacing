import { create } from 'zustand'
import { getActiveGraphId, setActiveGraphId, initGraphConfig } from '../config/graphs'
import { isProMode } from '../config/backend'
import { BackendAdapter } from '../api/BackendAdapter'
import { useDrillStore, type DrillStackItem } from './drillStore'

export interface GraphMeta {
  graph_id: string
  file: string
  label: string
  description: string
  node_count: number
  card_count: number
}

interface GraphStore {
  graphs: GraphMeta[]
  activeGraphId: string
  loading: boolean
  getActiveGraphMeta: () => GraphMeta | undefined
  setActiveGraph: (id: string) => void
  fetchGraphList: () => Promise<void>
  createGraph: (label: string, description?: string) => Promise<string | null>
  deleteGraph: (id: string) => Promise<boolean>

  /** 钻入子图：切换到目标图，记录钻入栈 */
  drillIn: (
    subGraphId: string,
    entryNodeId: string,
    parentNodeId: string,
    parentNodeLabel: string,
  ) => void
  /** 钻出子图：恢复到父图，定位到父节点 */
  drillOut: () => DrillStackItem | undefined
}

export const useGraphStore = create<GraphStore>((set, get) => ({
  graphs: [],
  activeGraphId: getActiveGraphId(),
  loading: false,

  getActiveGraphMeta: () => {
    const { graphs, activeGraphId } = get()
    return graphs.find((g) => g.graph_id === activeGraphId)
  },

  setActiveGraph: (id: string) => {
    setActiveGraphId(id)
    set({ activeGraphId: id })
  },

  fetchGraphList: async () => {
    set({ loading: true })
    try {
      const adapter = BackendAdapter.getInstance()
      const data = await adapter.get<{ graphs: GraphMeta[] }>('/api/graphs')
      const graphs = data.graphs || []
      const activeId = getActiveGraphId()
      // 如果当前活动图不在列表中，自动切换到第一个
      if (graphs.length > 0 && !graphs.find((g) => g.graph_id === activeId)) {
        setActiveGraphId(graphs[0].graph_id)
        set({ graphs, activeGraphId: graphs[0].graph_id, loading: false })
        return
      }
      set({ graphs, loading: false })
    } catch {
      set({ loading: false })
    }
  },

  createGraph: async (label, description = '') => {
    if (!isProMode()) return null
    try {
      const adapter = BackendAdapter.getInstance()
      const res = await adapter.post<{ graph_id: string }>('/api/graphs', { label, description })
      await get().fetchGraphList()
      return res.graph_id
    } catch {
      return null
    }
  },

  deleteGraph: async (id) => {
    if (!isProMode()) return false
    try {
      const adapter = BackendAdapter.getInstance()
      await adapter.delete(`/api/graphs/${id}`)
      await get().fetchGraphList()
      return true
    } catch {
      return false
    }
  },

  drillIn: (subGraphId, entryNodeId, parentNodeId, parentNodeLabel) => {
    const { graphs, activeGraphId } = get()
    const subGraphMeta = graphs.find((g) => g.graph_id === subGraphId)
    if (!subGraphMeta) return

    // 记录钻入栈
    useDrillStore.getState().push({
      parentGraphId: activeGraphId,
      parentNodeId,
      subGraphId,
      entryNodeId,
      parentNodeLabel,
      subGraphLabel: subGraphMeta.label,
    })

    // 切换到目标图
    setActiveGraphId(subGraphId)
    set({ activeGraphId: subGraphId })
  },

  drillOut: () => {
    const popped = useDrillStore.getState().pop()
    if (!popped) return undefined

    // 恢复到父图
    setActiveGraphId(popped.parentGraphId)
    set({ activeGraphId: popped.parentGraphId })
    return popped
  },
}))

// 应用启动时初始化
initGraphConfig()
