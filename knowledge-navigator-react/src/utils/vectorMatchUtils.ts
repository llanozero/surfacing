import type { CognitiveCard } from '../data/types'
import type { MatchedCard } from '../store/searchStore'
import { isProMode } from '../config/backend'
import { BackendAdapter } from '../api/BackendAdapter'

const clamp01 = (n: number) => Math.max(0, Math.min(1, n))

/**
 * 降级策略（spec §3.3）：向量模型不可用时的词袋重叠率近似。
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

/** 本地词袋降级结果（按相似度降序） */
function localFallback(query: string, cards: CognitiveCard[]): MatchedCard[] {
  return cards
    .map((card) => ({ card, score: fallbackVectorMatch(query, card) }))
    .filter((m) => m.score > 0)
    .sort((a, b) => b.score - a.score)
}

/**
 * 向量模型匹配（spec §4.1）双模式：
 * - pro 模式（完整模式）：POST /api/search/vector-match，由后端调 LM Studio
 *   qwen3-embedding 做余弦相似度语义匹配（后端不可用时自身降级关键词）；
 * - lite 模式（轻量模式）：本地词袋重叠率近似，零网络请求；
 * - pro 模式下调用失败时同样回退本地词袋，保证界面可用。
 */
export async function vectorMatch(query: string, cards: CognitiveCard[]): Promise<MatchedCard[]> {
  if (isProMode()) {
    try {
      const data = await BackendAdapter.getInstance().post<
        { card: CognitiveCard; score: number }[]
      >('/api/search/vector-match', { query })
      return data
        .filter((m) => m.score > 0)
        .map((m) => ({ card: m.card, score: clamp01(m.score) }))
        .sort((a, b) => b.score - a.score)
    } catch (e) {
      console.warn('[search] 后端向量匹配失败，回退本地词袋近似：', e)
    }
  }
  return localFallback(query, cards)
}
