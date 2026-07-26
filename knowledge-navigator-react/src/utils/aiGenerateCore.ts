import type { CognitiveCard, NavNode } from '../data/types'
import {
  fallbackCardTitle,
  fallbackCardDescription,
  fallbackNodeLabel,
  fallbackNodeDescription,
} from './aiFallback'

/**
 * AI 生成核心（无 React 依赖，浏览器与 Node/CLI 通用）。
 * 优先调用本地 LM Studio（OpenAI 兼容接口，Qwen 优先），
 * 不可用 / 超时时降级为本地规则算法。
 */

/** 生成结果：text 为生成文本，source 标注来源（用于区分 lite 模式（轻量模式）） */
export interface AiResult {
  text: string
  source: 'ai' | 'local'
}

/** LM Studio 候选地址：优先走 Vite 开发代理（规避 CORS），其次直连 */
const LM_BASES = ['/api/lm/v1', 'http://localhost:1234/v1']
// 本地模型冷启动 + 推理耗时较长，超时放宽到 30s（规范默认 5s 针对远端 API）
const REQUEST_TIMEOUT_MS = 30000

/** 已探测到的可用 base + 候选模型 id 列表（模块级缓存，避免每次请求都探测） */
let cachedBase: string | null = null
let cachedModels: string[] | null = null

interface LmModelList {
  data?: { id: string }[]
}

/** 候选聊天模型排序：排除 embedding/reranker/encoder，Qwen 优先 */
function rankChatModels(models: { id: string }[]): string[] {
  const chatModels = models.filter((m) => !/embed|rerank|encoder/i.test(m.id)).map((m) => m.id)
  return chatModels.sort((a, b) => Number(/qwen/i.test(b)) - Number(/qwen/i.test(a)))
}

/** 探测 LM Studio：找到可用 base 并读取候选模型列表 */
async function resolveLmEndpoint(signal: AbortSignal): Promise<{ base: string; models: string[] }> {
  if (cachedBase && cachedModels) return { base: cachedBase, models: cachedModels }

  for (const base of LM_BASES) {
    try {
      const res = await fetch(`${base}/models`, { signal })
      if (!res.ok) continue
      const json = (await res.json()) as LmModelList
      const models = json.data ? rankChatModels(json.data) : []
      if (models.length > 0) {
        cachedBase = base
        cachedModels = models
        return { base, models }
      }
    } catch {
      // 该地址不可达（浏览器代理不可用 / Node 下相对地址报错），尝试下一个
    }
  }
  throw new Error('LM Studio 不可达或未加载模型')
}

/** 调用 LM Studio chat completions：按候选顺序尝试（Qwen 优先，失败自动换下一个） */
async function callLmStudio(prompt: string, signal: AbortSignal): Promise<string> {
  const { base, models } = await resolveLmEndpoint(signal)
  let lastError: Error | null = null

  for (const model of models) {
    try {
      const res = await fetch(`${base}/chat/completions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model,
          messages: [{ role: 'user', content: prompt }],
          temperature: 0.7,
          // 推理模型会先消耗 reasoning tokens，留足余量保证最终 content 输出
          max_tokens: 800,
          stream: false,
        }),
        signal,
      })
      if (!res.ok) throw new Error(`LM Studio 响应 ${res.status}`)
      const json = await res.json()
      const text: unknown = json?.choices?.[0]?.message?.content
      if (typeof text !== 'string' || !text.trim()) throw new Error('模型返回空内容')
      // 成功：将该模型提到候选首位，后续请求直接用
      if (cachedModels && cachedModels[0] !== model) {
        cachedModels = [model, ...cachedModels.filter((m) => m !== model)]
      }
      // 去掉模型可能输出的引号包裹与首尾空白
      return text.trim().replace(/^["「『]+|["」』]+$/g, '')
    } catch (e) {
      if (signal.aborted) throw e
      lastError = e as Error
    }
  }
  throw lastError ?? new Error('所有候选模型均不可用')
}

/* ========== Prompt 模板（遵循 ai-assisted-generation.md） ========== */

export function buildCardTitlePrompt(card: CognitiveCard, children: CognitiveCard[]): string {
  const corpusLines = card.corpus.map((t) => `- ${t}`).join('\n') || '（无）'
  const childLines =
    children.map((c) => `- ${c.title}${c.description ? `：${c.description}` : ''}`).join('\n') || '（无）'
  return `你是一个知识卡片标题生成助手。

根据以下数据，生成一个简洁、准确的卡片标题（10 个字符以内）：

卡片语料库：
${corpusLines}

子卡片标题与描述：
${childLines}

请直接输出标题，不要有任何额外说明。`
}

export function buildCardDescriptionPrompt(card: CognitiveCard, children: CognitiveCard[]): string {
  const corpusLines = card.corpus.map((t) => `- ${t}`).join('\n') || '（无）'
  const childLines = children.map((c) => c.description).filter(Boolean).join('\n') || '（无）'
  return `你是一个知识卡片描述生成助手。

根据以下数据，生成一段 1-2 句话的卡片描述（50-100 字），
简洁概述卡片的核心内容：

卡片标题：${card.title}
卡片语料库：
${corpusLines}

子卡片描述：
${childLines}

请直接输出描述文本。`
}

export function buildNodeLabelPrompt(boundCards: CognitiveCard[]): string {
  const titleLines = boundCards.map((c) => `- ${c.title}`).join('\n') || '（无）'
  const descLines = boundCards.map((c) => c.description).filter(Boolean).join('\n') || '（无）'
  return `你是一个导航节点标签生成助手。

根据以下绑定的认知卡片信息，生成一个简洁的导航节点标签名（8 个字以内），
作为知识路径中的一个"站点"名称：

绑定卡片标题：
${titleLines}

绑定卡片描述：
${descLines}

请直接输出标签名。`
}

export function buildNodeDescriptionPrompt(
  node: NavNode,
  boundCards: CognitiveCard[],
  prevNodes: NavNode[],
  nextNodes: NavNode[],
): string {
  const corpusLines =
    boundCards
      .map((c) => `【${c.title}】\n${c.corpus.map((t) => `- ${t}`).join('\n')}`)
      .join('\n') || '（无）'
  const descLines = boundCards.map((c) => c.description).filter(Boolean).join('\n') || '（无）'
  const prevLines = prevNodes.map((n) => `${n.label}：${n.description}`).join('\n') || '（无）'
  const nextLines = nextNodes.map((n) => `${n.label}：${n.description}`).join('\n') || '（无）'
  return `你是一个导航节点描述生成助手。

根据以下数据，生成一段 1-2 句话的节点描述（50-80 字），
说明该节点在认知导航路径中的定位和核心内容：

节点标签：${node.label}
绑定的认知卡片语料：
${corpusLines}

绑定的认知卡片描述：
${descLines}

前驱节点（上一个站点）：
${prevLines}

后继节点（可跳转的下一个站点）：
${nextLines}

请直接输出描述文本。`
}

/* ========== 统一生成入口 ========== */

/**
 * 通用生成流程：先尝试 LM Studio，失败则执行本地降级算法。
 * 两者都失败返回 null。外部可通过 signal 取消（超时内部处理）。
 */
export async function generateField(
  prompt: string,
  fallback: () => string | null,
  signal?: AbortSignal,
): Promise<AiResult | null> {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS)
  // 外部取消信号联动
  const onExternalAbort = () => controller.abort()
  signal?.addEventListener('abort', onExternalAbort)

  try {
    const text = await callLmStudio(prompt, controller.signal)
    return { text, source: 'ai' }
  } catch {
    if (signal?.aborted) return null // 外部主动取消：不降级，直接返回
    const text = fallback()
    return text ? { text, source: 'local' } : null
  } finally {
    clearTimeout(timeoutId)
    signal?.removeEventListener('abort', onExternalAbort)
  }
}

/* ========== 语义化封装（供 API / CLI 直接调用） ========== */

export function aiCardTitle(card: CognitiveCard, children: CognitiveCard[]): Promise<AiResult | null> {
  return generateField(buildCardTitlePrompt(card, children), () => fallbackCardTitle(card, children))
}

export function aiCardDescription(card: CognitiveCard, children: CognitiveCard[]): Promise<AiResult | null> {
  return generateField(buildCardDescriptionPrompt(card, children), () =>
    fallbackCardDescription(card, children),
  )
}

export function aiNodeLabel(node: NavNode, boundCards: CognitiveCard[]): Promise<AiResult | null> {
  return generateField(buildNodeLabelPrompt(boundCards), () => fallbackNodeLabel(node, boundCards))
}

export function aiNodeDescription(
  node: NavNode,
  boundCards: CognitiveCard[],
  prevNodes: NavNode[],
  nextNodes: NavNode[],
): Promise<AiResult | null> {
  return generateField(buildNodeDescriptionPrompt(node, boundCards, prevNodes, nextNodes), () =>
    fallbackNodeDescription(node, boundCards, prevNodes, nextNodes),
  )
}
