import { create } from 'zustand'

/** 钻入栈中的一项：记录一次钻入操作 */
export interface DrillStackItem {
  parentGraphId: string   // 钻入前的图
  parentNodeId: string    // 钻入前的子图节点 ID
  subGraphId: string      // 钻入的目标图
  entryNodeId: string     // 目标图中的入口节点
  parentNodeLabel: string // 子图节点的 label（面包屑用）
  subGraphLabel: string   // 目标图的 label（面包屑用）
}

/** 面包屑路径中的一步 */
export interface BreadcrumbStep {
  graphId: string
  graphLabel: string
  nodeId: string
  nodeLabel: string
}

interface DrillStore {
  /** 钻入栈（支持多级嵌套，栈底是最外层的钻入） */
  stack: DrillStackItem[]

  /** 钻入前画布选中的图 ID 列表（钻出后恢复） */
  snapshotSelectedGraphIds: string[]

  push: (item: DrillStackItem) => void
  pop: () => DrillStackItem | undefined
  peek: () => DrillStackItem | undefined
  clear: () => void

  /** 快照当前选中图列表 */
  setSnapshot: (ids: string[]) => void

  /** 是否处于钻入状态 */
  isInDrill: () => boolean

  /** 构建面包屑路径：从顶层 top 到当前层的图+节点路径 */
  buildBreadcrumb: (
    currentGraphId: string,
    currentGraphLabel: string,
    currentNodeId: string,
    currentNodeLabel: string,
  ) => BreadcrumbStep[]
}

export const useDrillStore = create<DrillStore>((set, get) => ({
  stack: [],
  snapshotSelectedGraphIds: [],

  push: (item) => {
    set((s) => ({ stack: [...s.stack, item] }))
  },

  pop: () => {
    const stack = get().stack
    if (stack.length === 0) return undefined
    const popped = stack[stack.length - 1]
    set({ stack: stack.slice(0, -1) })
    return popped
  },

  peek: () => {
    const stack = get().stack
    return stack.length > 0 ? stack[stack.length - 1] : undefined
  },

  clear: () => {
    set({ stack: [], snapshotSelectedGraphIds: [] })
  },

  setSnapshot: (ids) => {
    set({ snapshotSelectedGraphIds: ids })
  },

  isInDrill: () => get().stack.length > 0,

  buildBreadcrumb: (currentGraphId, currentGraphLabel, currentNodeId, currentNodeLabel) => {
    const { stack } = get()
    const steps: BreadcrumbStep[] = []

    // 第一步永远是 top 顶层
    steps.push({
      graphId: 'top',
      graphLabel: 'top',
      nodeId: '',
      nodeLabel: '',
    })

    // 从栈底到栈顶构建面包屑
    for (const item of stack) {
      steps.push({
        graphId: item.subGraphId,
        graphLabel: item.subGraphLabel,
        nodeId: item.entryNodeId,
        nodeLabel: item.parentNodeLabel,
      })
    }

    // 当前层
    if (currentGraphId !== steps[steps.length - 1]?.graphId) {
      steps.push({
        graphId: currentGraphId,
        graphLabel: currentGraphLabel,
        nodeId: currentNodeId,
        nodeLabel: currentNodeLabel,
      })
    }

    return steps
  },
}))
