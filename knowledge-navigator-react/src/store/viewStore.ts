import { create } from 'zustand'
import { usePanelStore } from './panelStore'

export type ViewName = 'search' | 'nav' | 'plan' | 'browse' | 'tree'

interface ViewStore {
  activeView: ViewName
  switchView: (name: ViewName) => void
}

export const useViewStore = create<ViewStore>((set) => ({
  activeView: 'search',
  switchView: (name) => {
    set({ activeView: name })
    // 切换视图时同步下拉面板可见性（spec §9.1 约束）
    usePanelStore.getState().syncVisibility(name)
  },
}))
