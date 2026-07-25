import type { CognitiveCard, NavNode } from '../data/types'

/**
 * AI 不可用时的本地降级生成算法。
 * 所有函数在输入数据不足时返回 null，由调用方决定提示。
 */

/** 取文本第一句（按中英文句读切分） */
function firstSentence(text: string): string {
  return text.split(/[。！？!?\n]/)[0]?.trim() ?? ''
}

/** 多个标题的最长公共前缀 */
export function longestCommonPrefix(strings: string[]): string {
  if (strings.length === 0) return ''
  let prefix = strings[0]
  for (const s of strings.slice(1)) {
    while (prefix && !s.startsWith(prefix)) {
      prefix = prefix.slice(0, -1)
    }
    if (!prefix) break
  }
  return prefix
}

/** 聚合子卡片标题：公共前缀 >= 2 字则用之，否则取首个标题 */
export function aggregateTitle(titles: string[]): string {
  if (titles.length === 0) return ''
  if (titles.length === 1) return titles[0]
  const common = longestCommonPrefix(titles)
  if (common.length >= 2) return common
  return `${titles[0]}·${titles[1]}`
}

/** 卡片标题降级：语料第一句 → 子卡片标题聚合 */
export function fallbackCardTitle(card: CognitiveCard, children: CognitiveCard[]): string | null {
  if (card.corpus.length > 0) {
    const sentence = firstSentence(card.corpus.join(' '))
    if (sentence) {
      return sentence.length <= 10 ? sentence : sentence.slice(0, 8) + '…'
    }
  }
  if (children.length > 0) {
    const aggregated = aggregateTitle(children.map((c) => c.title))
    if (aggregated) return aggregated.length <= 10 ? aggregated : aggregated.slice(0, 8) + '…'
  }
  return null
}

/** 卡片描述降级：前两条语料首句 + 子卡片描述拼接 */
export function fallbackCardDescription(card: CognitiveCard, children: CognitiveCard[]): string | null {
  const sources: string[] = []

  for (const text of card.corpus.slice(0, 2)) {
    const sentence = firstSentence(text)
    if (sentence) sources.push(sentence)
  }

  if (sources.length < 2) {
    for (const child of children.slice(0, 3)) {
      if (child.description) sources.push(child.description)
    }
  }

  if (sources.length === 0) return null
  return sources.join('；') + '。'
}

/** 节点标签降级：单卡片直接用标题，多卡片取公共前缀或拼接 */
export function fallbackNodeLabel(_node: NavNode, boundCards: CognitiveCard[]): string | null {
  if (boundCards.length === 0) return null
  if (boundCards.length === 1) return boundCards[0].title

  const titles = boundCards.map((c) => c.title)
  const common = longestCommonPrefix(titles)
  if (common.length >= 2) return common
  return `${titles[0]}·${titles[1]}`
}

/** 节点描述降级：绑定卡片描述 + 前驱/后继上下文拼接 */
export function fallbackNodeDescription(
  _node: NavNode,
  boundCards: CognitiveCard[],
  prevNodes: NavNode[],
  nextNodes: NavNode[],
): string | null {
  const parts: string[] = []

  const cardDescs = boundCards.map((c) => c.description).filter((d): d is string => Boolean(d))
  if (cardDescs.length > 0) {
    parts.push(cardDescs.slice(0, 2).join('；'))
  }

  if (prevNodes.length > 0) {
    parts.push(`承接${prevNodes[0].label}`)
  }
  if (nextNodes.length > 0) {
    const nextLabels = nextNodes.slice(0, 3).map((n) => n.label).join('、')
    parts.push(`可跳转至${nextLabels}`)
  }

  if (parts.length === 0) return null
  return parts.join('。') + '。'
}
