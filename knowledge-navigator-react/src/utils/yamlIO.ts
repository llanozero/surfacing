import { load, dump } from 'js-yaml'
import type { CognitiveCard, NavNode } from '../data/types'
import { cognitiveCards } from '../data/cards'
import { allNavNodes, navNodeMap } from '../data/allNavNodes'

/* ========== 类型定义 ========== */

/** YAML 文件顶层结构 */
export interface YamlData {
  cognitive_cards: CognitiveCard[]
  navigation_nodes: NavNode[]
}

/** 导入校验错误 */
export interface ValidationError {
  type: 'structure' | 'field' | 'reference'
  message: string
  itemId?: string
}

/** 导入变更预览 */
export interface ImportPreview {
  cards: { total: number; added: number; overwritten: number }
  nodes: { total: number; added: number; overwritten: number }
}

/* ========== 导出 ========== */

/**
 * 导出全部认知卡片和导航节点为 YAML 字符串。
 * 序列化前剔除空数组、undefined、metadata 中的空对象，
 * 保持导出文件简洁可读。
 */
export function exportAllToYAML(cards: CognitiveCard[], nodes: NavNode[]): string {
  // cleanCard/cleanNode 返回清理后的部分字段对象，dump 直接序列化
  const data = {
    cognitive_cards: cards.map(cleanCard),
    navigation_nodes: nodes.map(cleanNode),
  }
  const now = new Date().toISOString()
  const comment = `# Exported at: ${now}\n# Total cards: ${cards.length}, total nodes: ${nodes.length}\n\n`
  return comment + dump(data, { indent: 2, lineWidth: 120, noRefs: true })
}

/**
 * 触发浏览器下载 YAML 文件。
 * 使用 <a> download + Blob URL 方案，兼容所有现代浏览器。
 */
export function downloadYAML(yamlStr: string, filename?: string): void {
  const name = filename ?? `cognitive-nav-data-${new Date().toISOString().slice(0, 10)}.yaml`
  const blob = new Blob([yamlStr], { type: 'application/x-yaml;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = name
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

/* ========== 导入 ========== */

/**
 * 解析并校验 YAML 字符串。
 * 引用一致性校验范围 = 导入数据集 ∪ 当前数据源（允许分批导入）。
 * 返回 { ok: true, data } 或 { ok: false, errors }。
 */
export function parseAndValidateYAML(
  raw: string,
  currentCards: CognitiveCard[] = cognitiveCards,
  currentNodes: NavNode[] = allNavNodes,
): { ok: true; data: YamlData } | { ok: false; errors: ValidationError[] } {
  const errors: ValidationError[] = []
  let parsed: unknown

  try {
    parsed = load(raw)
  } catch (e) {
    errors.push({ type: 'structure', message: `YAML 解析失败: ${(e as Error).message}` })
    return { ok: false, errors }
  }

  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
    errors.push({ type: 'structure', message: 'YAML 顶层必须是一个对象' })
    return { ok: false, errors }
  }

  const root = parsed as Record<string, unknown>
  const hasCards = 'cognitive_cards' in root
  const hasNodes = 'navigation_nodes' in root
  if (!hasCards && !hasNodes) {
    errors.push({ type: 'structure', message: 'YAML 文件中缺少 cognitive_cards 或 navigation_nodes 键' })
    return { ok: false, errors }
  }

  const cards: CognitiveCard[] = []
  const nodes: NavNode[] = []

  // 校验认知卡片
  if (hasCards) {
    if (!Array.isArray(root.cognitive_cards)) {
      errors.push({ type: 'structure', message: 'cognitive_cards 必须是数组' })
    } else {
      root.cognitive_cards.forEach((item: unknown, i: number) => {
        const c = item as Partial<CognitiveCard> | null
        const id = c?.id ?? `index ${i}`
        if (!c || typeof c !== 'object') {
          errors.push({ type: 'field', itemId: String(id), message: `第 ${i + 1} 项不是有效对象` })
          return
        }
        if (!c.id || typeof c.id !== 'string') {
          errors.push({ type: 'field', itemId: String(id), message: '缺少必填字段 id' })
          return
        }
        if (!c.title || typeof c.title !== 'string') {
          errors.push({ type: 'field', itemId: c.id, message: '缺少必填字段 title' })
          return
        }
        if (!['folder', 'leaf'].includes(c.type as string)) {
          errors.push({ type: 'field', itemId: c.id, message: 'type 必须是 folder 或 leaf' })
          return
        }
        if (c.corpus !== undefined && !Array.isArray(c.corpus)) {
          errors.push({ type: 'field', itemId: c.id, message: 'corpus 必须是字符串数组' })
          return
        }
        if (c.bound_nodes !== undefined && !Array.isArray(c.bound_nodes)) {
          errors.push({ type: 'field', itemId: c.id, message: 'bound_nodes 必须是数组' })
          return
        }
        cards.push({ corpus: [], ...c } as CognitiveCard)
      })
    }
  }

  // 校验导航节点
  if (hasNodes) {
    if (!Array.isArray(root.navigation_nodes)) {
      errors.push({ type: 'structure', message: 'navigation_nodes 必须是数组' })
    } else {
      root.navigation_nodes.forEach((item: unknown, i: number) => {
        const n = item as Partial<NavNode> | null
        const id = n?.id ?? `index ${i}`
        if (!n || typeof n !== 'object') {
          errors.push({ type: 'field', itemId: String(id), message: `第 ${i + 1} 项不是有效对象` })
          return
        }
        if (!n.id || typeof n.id !== 'string') {
          errors.push({ type: 'field', itemId: String(id), message: '缺少必填字段 id' })
          return
        }
        if (!n.label || typeof n.label !== 'string') {
          errors.push({ type: 'field', itemId: n.id, message: '缺少必填字段 label' })
          return
        }
        if (!Array.isArray(n.next_nodes)) {
          errors.push({ type: 'field', itemId: n.id, message: 'next_nodes 必须是数组（允许空数组）' })
          return
        }
        const badRef = n.next_nodes.findIndex(
          (e) => !e || typeof e.target_id !== 'string' || typeof e.preset_weight !== 'number',
        )
        if (badRef >= 0) {
          errors.push({
            type: 'field',
            itemId: n.id,
            message: `next_nodes 第 ${badRef + 1} 项缺少 target_id 或 preset_weight`,
          })
          return
        }
        if (n.bound_cards !== undefined && !Array.isArray(n.bound_cards)) {
          errors.push({ type: 'field', itemId: n.id, message: 'bound_cards 必须是数组' })
          return
        }
        nodes.push({ description: '', ...n } as NavNode)
      })
    }
  }

  if (errors.length > 0) return { ok: false, errors }

  // 引用一致性：导入数据 ∪ 当前数据 范围内检查
  const knownNodeIds = new Set([...nodes.map((n) => n.id), ...currentNodes.map((n) => n.id)])
  const knownCardIds = new Set([...cards.map((c) => c.id), ...currentCards.map((c) => c.id)])

  cards.forEach((c) => {
    c.bound_nodes?.forEach((nodeId) => {
      if (!knownNodeIds.has(nodeId)) {
        errors.push({
          type: 'reference',
          itemId: c.id,
          message: `卡片 ${c.id} 的 bound_nodes 引用了不存在的节点 ${nodeId}`,
        })
      }
    })
  })
  nodes.forEach((n) => {
    n.bound_cards?.forEach((cardId) => {
      if (!knownCardIds.has(cardId)) {
        errors.push({
          type: 'reference',
          itemId: n.id,
          message: `节点 ${n.id} 的 bound_cards 引用了不存在的卡片 ${cardId}`,
        })
      }
    })
    n.next_nodes.forEach((e) => {
      if (!knownNodeIds.has(e.target_id)) {
        errors.push({
          type: 'reference',
          itemId: n.id,
          message: `节点 ${n.id} 的 next_nodes 指向了不存在的节点 ${e.target_id}`,
        })
      }
    })
  })

  if (errors.length > 0) return { ok: false, errors }

  return { ok: true, data: { cognitive_cards: cards, navigation_nodes: nodes } }
}

/**
 * 计算变更预览（相对于当前数据）。
 */
export function computeImportPreview(
  imported: YamlData,
  currentCards: CognitiveCard[],
  currentNodes: NavNode[],
): ImportPreview {
  const cardIds = new Set(currentCards.map((c) => c.id))
  const nodeIds = new Set(currentNodes.map((n) => n.id))

  const cardAdded = imported.cognitive_cards.filter((c) => !cardIds.has(c.id)).length
  const cardOverwritten = imported.cognitive_cards.filter((c) => cardIds.has(c.id)).length

  const nodeAdded = imported.navigation_nodes.filter((n) => !nodeIds.has(n.id)).length
  const nodeOverwritten = imported.navigation_nodes.filter((n) => nodeIds.has(n.id)).length

  return {
    cards: { total: imported.cognitive_cards.length, added: cardAdded, overwritten: cardOverwritten },
    nodes: { total: imported.navigation_nodes.length, added: nodeAdded, overwritten: nodeOverwritten },
  }
}

/**
 * 执行导入合并（upsert），直接修改共享数据源。
 * 导入完成后调用回调更新各 Store state。
 */
export function mergeImportedData(
  imported: YamlData,
  callbacks: {
    onCardsMerged: (cards: CognitiveCard[]) => void
    onNodesMerged: (nodes: NavNode[]) => void
  },
): void {
  // 合并认知卡片（upsert：存在即覆盖，不存在则追加）
  const mergedCards = upsertArray(cognitiveCards, imported.cognitive_cards, (a, b) => a.id === b.id)
  // 合并导航节点（upsert）
  const mergedNodes = upsertArray(allNavNodes, imported.navigation_nodes, (a, b) => a.id === b.id)

  // 写回共享数据源
  cognitiveCards.length = 0
  cognitiveCards.push(...mergedCards)
  allNavNodes.length = 0
  allNavNodes.push(...mergedNodes)

  // 重建 navNodeMap
  allNavNodes.forEach((n) => navNodeMap.set(n.id, n))

  callbacks.onCardsMerged(mergedCards)
  callbacks.onNodesMerged(mergedNodes)
}

/* ========== 内部工具 ========== */

/** upsert: 已存在则覆盖，不存在则追加 */
function upsertArray<T>(current: T[], incoming: T[], isSame: (a: T, b: T) => boolean): T[] {
  const result = [...current]
  for (const item of incoming) {
    const idx = result.findIndex((c) => isSame(c, item))
    if (idx >= 0) {
      result[idx] = item
    } else {
      result.push(item)
    }
  }
  return result
}

/** 导出前清理空字段 */
function cleanCard(card: CognitiveCard): Partial<CognitiveCard> {
  return {
    id: card.id,
    title: card.title,
    type: card.type,
    ...(card.tag ? { tag: card.tag } : {}),
    ...(card.description ? { description: card.description } : {}),
    ...(card.corpus?.length ? { corpus: card.corpus } : {}),
    ...(card.bound_nodes?.length ? { bound_nodes: card.bound_nodes } : {}),
    ...(card.metadata && Object.keys(card.metadata).length > 0 ? { metadata: card.metadata } : {}),
  }
}

function cleanNode(node: NavNode): Partial<NavNode> & { metadata?: unknown } {
  const metadata = (node as { metadata?: unknown }).metadata
  return {
    id: node.id,
    label: node.label,
    ...(node.description ? { description: node.description } : {}),
    ...(node.bound_cards?.length ? { bound_cards: node.bound_cards } : {}),
    ...(node.browse_history?.length ? { browse_history: node.browse_history } : {}),
    next_nodes: node.next_nodes ?? [],
    ...(node.priority_config ? { priority_config: node.priority_config } : {}),
    ...(metadata && Object.keys(metadata).length > 0 ? { metadata } : {}),
  }
}
