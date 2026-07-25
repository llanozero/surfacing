import { create } from 'zustand'
import type { TreeNodeData } from '../data/types'
import { treeData } from '../data/treeData'
import { getAncestorIds } from '../utils/treeUtils'

interface TreeStore {
  flatData: TreeNodeData[]
  selectedId: string | null
  expandedIds: Set<string>
  searchQuery: string
  selectNode: (id: string) => void
  toggleNode: (id: string) => void
  expandAncestors: (id: string) => void
  setSearch: (q: string) => void
}

export const useTreeStore = create<TreeStore>((set, get) => ({
  flatData: treeData,
  selectedId: null,
  expandedIds: new Set<string>(['root/1', 'root/2']),
  searchQuery: '',

  selectNode: (id) => set({ selectedId: id }),

  toggleNode: (id) => {
    const next = new Set(get().expandedIds)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    set({ expandedIds: next })
  },

  expandAncestors: (id) => {
    const next = new Set(get().expandedIds)
    getAncestorIds(id).forEach((a) => next.add(a))
    set({ expandedIds: next })
  },

  setSearch: (q) => {
    set({ searchQuery: q })
    // 搜索时自动展开匹配行的所有父级
    const query = q.trim().toLowerCase()
    if (!query) return
    const next = new Set(get().expandedIds)
    get().flatData.forEach((n) => {
      if (n.title.toLowerCase().includes(query)) {
        getAncestorIds(n.id).forEach((a) => next.add(a))
      }
    })
    set({ expandedIds: next })
  },
}))

/** 判断节点是否匹配搜索（含子树中有匹配则保留父行显示） */
export function nodeMatches(data: TreeNodeData[], id: string, query: string): boolean {
  const q = query.trim().toLowerCase()
  if (!q) return true
  const node = data.find((n) => n.id === id)
  if (node?.title.toLowerCase().includes(q)) return true
  // 子孙中有匹配则该 folder 也显示
  const prefix = `${id}/`
  return data.some((n) => n.id.startsWith(prefix) && n.title.toLowerCase().includes(q))
}
