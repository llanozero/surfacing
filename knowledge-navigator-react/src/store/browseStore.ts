import { create } from 'zustand'
import type { BrowseCard, NavNode } from '../data/types'
import { cognitiveCards } from '../data/cards'
import { getNavNode } from '../data/allNavNodes'

/**
 * 由途径点的 bound_cards 派生浏览卡片：
 * 绑定到该节点的认知卡片 → BrowseCard（related 取该节点的前驱/后继 label）。
 */
export function cardsForWaypoint(waypoint: NavNode): BrowseCard[] {
  const bound = cognitiveCards.filter((c) => c.bound_nodes?.includes(waypoint.id))
  const relatedPrev = waypoint.browse_history?.map((h) => getNavNode(h.from)?.label).filter(Boolean) ?? []
  const relatedNext = waypoint.next_nodes.map((e) => getNavNode(e.target_id)?.label).filter(Boolean) ?? []

  return bound.map((c, i) => ({
    title: c.title,
    desc: c.description ?? c.corpus[0] ?? '',
    tag: c.tag ?? '',
    weight: Math.max(0.3, 0.9 - i * 0.12),
    cards: c.corpus.length,
    corpus: c.corpus,
    related: [
      ...relatedPrev.slice(0, 1).map((name) => ({ name: name as string, pos: '前置' as const })),
      ...relatedNext.slice(0, 2).map((name) => ({ name: name as string, pos: '后置' as const })),
    ],
  }))
}

interface BrowseStore {
  waypoints: NavNode[]
  wpIndex: number
  cards: BrowseCard[]
  currentIndex: number
  initFromWaypoints: (waypoints: NavNode[]) => void
  /** 按规划后的节点序列初始化浏览 */
  initFromSequence: (sequence: NavNode[]) => void
  nextCard: () => void
  prevCard: () => void
  nextWaypoint: () => void
}

export const useBrowseStore = create<BrowseStore>((set, get) => ({
  waypoints: [],
  wpIndex: 0,
  cards: [],
  currentIndex: 0,

  initFromWaypoints: (waypoints) => {
    if (waypoints.length === 0) return
    set({
      waypoints: [...waypoints],
      wpIndex: 0,
      cards: cardsForWaypoint(waypoints[0]),
      currentIndex: 0,
    })
  },

  // 按规划后的节点序列初始化（spec §4.6，逻辑与 initFromWaypoints 一致）
  initFromSequence: (sequence) => {
    if (sequence.length === 0) return
    set({
      waypoints: [...sequence],
      wpIndex: 0,
      cards: cardsForWaypoint(sequence[0]),
      currentIndex: 0,
    })
  },

  nextCard: () => {
    const { currentIndex, cards } = get()
    if (currentIndex < cards.length - 1) set({ currentIndex: currentIndex + 1 })
  },

  prevCard: () => {
    const { currentIndex } = get()
    if (currentIndex > 0) set({ currentIndex: currentIndex - 1 })
  },

  nextWaypoint: () => {
    const { wpIndex, waypoints } = get()
    if (wpIndex < waypoints.length - 1) {
      const next = wpIndex + 1
      set({ wpIndex: next, cards: cardsForWaypoint(waypoints[next]), currentIndex: 0 })
    }
  },
}))
