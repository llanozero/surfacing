import type { CognitiveCard } from '../data/types'
import type { MatchedCard } from '../store/searchStore'

export interface VectorMatchResult {
  index: number
  similarity: number
}

const clamp01 = (n: number) => Math.max(0, Math.min(1, n))

/**
 * 降级策略（spec §3.3）：后端向量模型不可用时的词袋重叠率近似。
 * 仅为开发/演示占位，生产环境应替换为真实向量模型 API。
 */
export function fallbackVectorMatch(query: string, card: CognitiveCard): number {
  const qWords = new Set(query.toLowerCase().split(/[\s,，。、]+/).filter(Boolean))
  const cWords = new Set(
    [card.title, card.description ?? '', ...card.corpus]
      .join(' ')
      .toLowerCase()
      .split(/[\s,，。、]+/)
      .filter(Boolean),
  )
  const intersection = [...qWords].filter((w) => cWords.has(w))
  return intersection.length / Math.max(qWords.size, 1)
}

/**
 * 向量模型匹配（spec §4.1）：
 * 1. 优先调用后端 POST /api/vector-match
 * 2. 失败（后端未部署 / 超时）时降级为 fallbackVectorMatch
 * 返回按相似度降序的 MatchedCard[]
 */
export async function vectorMatch(query: string, cards: CognitiveCard[]): Promise<MatchedCard[]> {
  const corpora = cards.map((c) => [c.title, c.description ?? '', ...c.corpus].join('\n'))

  try {
    const ctrl = new AbortController()
    const timer = setTimeout(() => ctrl.abort(), 5000)
    const res = await fetch('/api/vector-match', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, corpora }),
      signal: ctrl.signal,
    })
    clearTimeout(timer)
    if (!res.ok) throw new Error(`vector-match API ${res.status}`)
    const data = (await res.json()) as { scores: VectorMatchResult[] }
    return data.scores
      .filter((s) => s.index >= 0 && s.index < cards.length && s.similarity > 0)
      .map((s) => ({ card: cards[s.index], score: clamp01(s.similarity) }))
      .sort((a, b) => b.score - a.score)
  } catch {
    // 降级：本地词袋重叠近似
    return cards
      .map((card) => ({ card, score: fallbackVectorMatch(query, card) }))
      .filter((m) => m.score > 0)
      .sort((a, b) => b.score - a.score)
  }
}
