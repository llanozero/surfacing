import { create } from 'zustand'
import type { CognitiveCard, NavNode } from '../data/types'
import { cognitiveCards, getCard } from '../data/cards'
import { getNavNode } from '../data/allNavNodes'
import { vectorMatch } from '../utils/vectorMatchUtils'

export type MatchMode = 'keyword' | 'vector'

export interface MatchedCard {
  card: CognitiveCard
  /** 匹配度评分 0-1（关键词：加权子串评分；向量：余弦相似度） */
  score: number
}

interface SearchStore {
  query: string
  matchedCards: MatchedCard[]
  selectedCardId: string | null
  boundNodes: NavNode[]
  selectedNodeId: string | null
  /** 匹配模式：关键词 / 向量模型 */
  matchMode: MatchMode
  isVectorLoading: boolean
  vectorError: string | null
  setQuery: (q: string) => void
  setMatchMode: (mode: MatchMode) => void
  selectCard: (id: string) => void
  selectNode: (id: string) => void
  /** 向量模式失败后的重试 */
  retryVectorMatch: () => void
  /** 返回选中的导航节点，供 navStore.init 消费 */
  enterNav: () => NavNode | null
}

/** 关键词模式：在 title / description / corpus 中子串匹配并打分 */
function matchCards(query: string): MatchedCard[] {
  const q = query.trim().toLowerCase()
  if (!q) return []
  const results: MatchedCard[] = []
  for (const card of cognitiveCards) {
    let score = 0
    if (card.title.toLowerCase().includes(q)) score += 0.6
    if (card.description?.toLowerCase().includes(q)) score += 0.3
    if (card.corpus.some((c) => c.toLowerCase().includes(q))) score += 0.2
    if (card.title.toLowerCase().startsWith(q)) score += 0.1
    if (score > 0) results.push({ card, score: Math.min(score, 1) })
  }
  return results.sort((a, b) => b.score - a.score)
}

let debounceTimer: ReturnType<typeof setTimeout> | null = null
/** 异步请求令牌，防止过期响应覆盖最新结果 */
let requestToken = 0

type Set = (partial: Partial<SearchStore>) => void
type Get = () => SearchStore

/** 统一匹配入口：按当前模式分叉（spec §4.2） */
function runMatch(query: string, set: Set, get: Get) {
  const q = query.trim()
  const token = ++requestToken

  if (!q) {
    set({ matchedCards: [], isVectorLoading: false, vectorError: null })
    return
  }

  if (get().matchMode === 'keyword') {
    const matchedCards = matchCards(q)
    const sel = get().selectedCardId
    const stillValid = sel && matchedCards.some((m) => m.card.id === sel)
    set({
      matchedCards,
      vectorError: null,
      isVectorLoading: false,
      ...(stillValid ? {} : { selectedCardId: null, boundNodes: [], selectedNodeId: null }),
    })
    return
  }

  // 向量模式：异步执行
  set({ isVectorLoading: true, vectorError: null })
  vectorMatch(q, cognitiveCards)
    .then((matchedCards) => {
      if (token !== requestToken) return // 过期响应丢弃
      const sel = get().selectedCardId
      const stillValid = sel && matchedCards.some((m) => m.card.id === sel)
      set({
        matchedCards,
        isVectorLoading: false,
        ...(stillValid ? {} : { selectedCardId: null, boundNodes: [], selectedNodeId: null }),
      })
    })
    .catch((err: unknown) => {
      if (token !== requestToken) return
      set({
        matchedCards: [],
        isVectorLoading: false,
        vectorError: err instanceof Error ? err.message : '向量匹配服务异常',
      })
    })
}

export const useSearchStore = create<SearchStore>((set, get) => ({
  query: '',
  matchedCards: [],
  selectedCardId: null,
  boundNodes: [],
  selectedNodeId: null,
  matchMode: 'keyword',
  isVectorLoading: false,
  vectorError: null,

  setQuery: (q) => {
    set({ query: q })
    if (debounceTimer) clearTimeout(debounceTimer)
    debounceTimer = setTimeout(() => runMatch(get().query, set, get), 300)
  },

  setMatchMode: (mode) => {
    if (get().matchMode === mode) return
    // 切换模式：清空选中状态与错误（spec §4.3）
    set({
      matchMode: mode,
      selectedCardId: null,
      selectedNodeId: null,
      boundNodes: [],
      vectorError: null,
    })
    // query 非空 → 立即以新模式重新匹配
    if (get().query.trim()) runMatch(get().query, set, get)
  },

  selectCard: (id) => {
    const card = getCard(id)
    if (!card) return
    const boundNodes = (card.bound_nodes ?? [])
      .map((nid) => getNavNode(nid))
      .filter((n): n is NavNode => Boolean(n))
    set({ selectedCardId: id, boundNodes, selectedNodeId: null })
  },

  selectNode: (id) => set({ selectedNodeId: id }),

  retryVectorMatch: () => {
    if (get().query.trim()) runMatch(get().query, set, get)
  },

  enterNav: () => {
    const { selectedNodeId } = get()
    if (!selectedNodeId) return null
    return getNavNode(selectedNodeId) ?? null
  },
}))

export function getSelectedCard(state: SearchStore): CognitiveCard | null {
  return state.selectedCardId ? getCard(state.selectedCardId) ?? null : null
}

export function getSelectedNode(state: SearchStore): NavNode | null {
  return state.selectedNodeId ? getNavNode(state.selectedNodeId) ?? null : null
}
