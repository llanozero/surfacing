import { create } from 'zustand'
import type { NavNode } from '../data/types'

export type PanelPosition = 'collapsed' | 'half' | 'full'

interface PanelStore {
  node: NavNode | null
  position: PanelPosition
  /** 切走视图时隐藏（但保留 node，回到 nav 时恢复） */
  hidden: boolean
  setNode: (node: NavNode) => void
  clearNode: () => void
  setPosition: (pos: PanelPosition) => void
  syncVisibility: (viewName: string) => void
}

export const usePanelStore = create<PanelStore>((set, get) => ({
  node: null,
  position: 'half',
  hidden: false,

  setNode: (node) => {
    const { node: cur } = get()
    if (cur) {
      // 面板已展开 → 切换内容，保持位置
      set({ node, hidden: false })
    } else {
      // 面板未展开 → 半屏
      set({ node, position: 'half', hidden: false })
    }
  },

  clearNode: () => set({ node: null }),

  setPosition: (pos) => set({ position: pos }),

  syncVisibility: (viewName) => {
    if (viewName === 'nav') {
      set({ hidden: false })
    } else {
      set({ hidden: true })
    }
  },
}))
