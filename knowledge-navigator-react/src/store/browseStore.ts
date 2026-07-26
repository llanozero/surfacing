import { create } from 'zustand'
import type { BrowseCard, NavNode } from '../data/types'
import { cognitiveCards } from '../data/cards'
import { getNavNode } from '../data/allNavNodes'
import { isRemoteMode } from '../config/backend'
import { BackendAdapter } from '../api/BackendAdapter'

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

/** 远程模式：POST /api/browse/start 并按序列拉取首站卡片 */
async function remoteStart(sequence: NavNode[]): Promise<BrowseCard[]> {
  const api = BackendAdapter.getInstance()
  await api.post('/api/browse/start', { sequence: sequence.map((n) => n.id) })
  return api.get<BrowseCard[]>('/api/browse/cards')
}

export const useBrowseStore = create<BrowseStore>((set, get) => ({
  waypoints: [],
  wpIndex: 0,
  cards: [],
  currentIndex: 0,

  initFromWaypoints: (waypoints) => {
    if (waypoints.length === 0) return

    // 远程模式：会话态保存在服务端，卡片由后端派生
    if (isRemoteMode()) {
      set({ waypoints: [...waypoints], wpIndex: 0, cards: [], currentIndex: 0 })
      void remoteStart(waypoints)
        .then((cards) => set({ cards, currentIndex: 0 }))
        .catch((e) => {
          console.warn('[browse] 后端浏览启动失败，回退本地派生：', e)
          set({ cards: cardsForWaypoint(waypoints[0]), currentIndex: 0 })
        })
      return
    }

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

    // 远程模式：以节点序列启动服务端浏览会话
    if (isRemoteMode()) {
      set({ waypoints: [...sequence], wpIndex: 0, cards: [], currentIndex: 0 })
      void remoteStart(sequence)
        .then((cards) => set({ cards, currentIndex: 0 }))
        .catch((e) => {
          console.warn('[browse] 后端浏览启动失败，回退本地派生：', e)
          set({ cards: cardsForWaypoint(sequence[0]), currentIndex: 0 })
        })
      return
    }

    set({
      waypoints: [...sequence],
      wpIndex: 0,
      cards: cardsForWaypoint(sequence[0]),
      currentIndex: 0,
    })
  },

  nextCard: () => {
    // 远程模式：服务端推进（到底循环）
    if (isRemoteMode()) {
      void BackendAdapter.getInstance()
        .post<{ cardIndex: number }>('/api/browse/next')
        .then((r) => set({ currentIndex: r.cardIndex }))
        .catch((e) => console.warn('[browse] next 同步失败：', e))
      return
    }
    const { currentIndex, cards } = get()
    if (currentIndex < cards.length - 1) set({ currentIndex: currentIndex + 1 })
  },

  prevCard: () => {
    // 远程模式：服务端回退（到顶循环）
    if (isRemoteMode()) {
      void BackendAdapter.getInstance()
        .post<{ cardIndex: number }>('/api/browse/prev')
        .then((r) => set({ currentIndex: r.cardIndex }))
        .catch((e) => console.warn('[browse] prev 同步失败：', e))
      return
    }
    const { currentIndex } = get()
    if (currentIndex > 0) set({ currentIndex: currentIndex - 1 })
  },

  nextWaypoint: () => {
    // 远程模式：服务端切换站点并拉取新站卡片
    if (isRemoteMode()) {
      const api = BackendAdapter.getInstance()
      void api
        .post<{ waypointIndex: number }>('/api/browse/waypoint')
        .then((r) =>
          api.get<BrowseCard[]>('/api/browse/cards').then((cards) => {
            set({ wpIndex: r.waypointIndex, cards, currentIndex: 0 })
          }),
        )
        .catch((e) => console.warn('[browse] 切换站点失败：', e))
      return
    }
    const { wpIndex, waypoints } = get()
    if (wpIndex < waypoints.length - 1) {
      const next = wpIndex + 1
      set({ wpIndex: next, cards: cardsForWaypoint(waypoints[next]), currentIndex: 0 })
    }
  },
}))
