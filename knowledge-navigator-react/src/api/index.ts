import type { CognitiveCard, NavNode, GraphEdge, BrowseCard, TreeNodeData, NextNodeRef } from '../data/types'
import { getCard } from '../data/cards'
import { allNavNodes, getNavNode, navNodeMap } from '../data/allNavNodes'
import { useCardStore } from '../store/cardStore'
import { useNavNodeStore, filterNodes } from '../store/navNodeStore'
import { useNavStore, type NavMode, type NextNodeItem } from '../store/navStore'
import { usePlanStore } from '../store/planStore'
import { useBrowseStore } from '../store/browseStore'
import { useSearchStore, type MatchMode, type MatchedCard } from '../store/searchStore'
import { useTreeStore } from '../store/treeStore'
import { useViewStore, type ViewName } from '../store/viewStore'
import { usePanelStore, type PanelPosition } from '../store/panelStore'
import {
  getConnectionStatus,
  ensureQuickConnection,
  removeQuickConnection,
  fillAllMissingConnections,
  priorityToWeight,
  type ConnectionStatusResult,
} from '../utils/quickConnectUtils'
import { composeWeights, type WeightedRef } from '../utils/weightUtils'
import { getRootNodes, getTreeChildren, getFullPath, deriveParent } from '../utils/treeUtils'
import {
  exportAllToYAML,
  downloadYAML as browserDownloadYAML,
  parseAndValidateYAML,
  computeImportPreview,
  mergeImportedData,
  type YamlData,
  type ImportPreview,
} from '../utils/yamlIO'
import {
  aiCardTitle,
  aiCardDescription,
  aiNodeLabel,
  aiNodeDescription,
} from '../utils/aiGenerateCore'
import type { RoutePlan, WaypointMode, WeightMode } from '../utils/routePlanner'

// ============================================================
// 辅助类型
// ============================================================

export type ApiResult<T> = { ok: true; data: T } | { ok: false; error: string }

export interface NextNodeRefInput {
  target_id: string
  /** 优先级序号（整数，#1 最高）；内部映射为 preset_weight */
  preset_priority?: number
  /** 浏览优先级序号；内部映射为 browse_weight */
  browse_priority?: number
  connection_type?: NextNodeRef['connection_type']
}

const ok = <T>(data: T): ApiResult<T> => ({ ok: true, data })
const err = <T>(message: string): ApiResult<T> => ({ ok: false, error: message })

const sleep = (ms: number) => new Promise<void>((r) => setTimeout(r, ms))

/** 连接变更后同步画布与节点管理状态 */
function syncAfterConnectionMutation(): void {
  useNavStore.getState().syncFromSource()
  useNavNodeStore.setState({ allNodes: [...allNavNodes] })
}

/**
 * Knowledge Navigator 程序化 API。
 * 封装所有 Zustand Store 与共享数据源的操作，浏览器与 Node（CLI）环境通用。
 */
export class KnowledgeNavigatorAPI {
  /** AI 生成中的请求计数（isGenerating 用） */
  private generatingCount = 0

  // ============================================================
  // 认知卡片
  // ============================================================

  getAllCards(): CognitiveCard[] {
    return useCardStore.getState().allCards
  }

  getCard(id: string): CognitiveCard | undefined {
    return getCard(id)
  }

  getChildCards(parentId: string): CognitiveCard[] {
    return this.getAllCards().filter((c) => {
      if (c.id === parentId) return false
      try {
        return deriveParent(c.id) === parentId
      } catch {
        return false
      }
    })
  }

  createCard(parentId?: string): ApiResult<CognitiveCard> {
    try {
      if (parentId && !getCard(parentId)) return err(`父卡片 ${parentId} 不存在`)
      const card = useCardStore.getState().createCard(parentId ?? null)
      return ok(card)
    } catch (e) {
      return err((e as Error).message)
    }
  }

  deleteCard(id: string): ApiResult<void> {
    if (!getCard(id)) return err(`卡片 ${id} 不存在`)
    const result = useCardStore.getState().deleteCard(id)
    return result.ok ? ok(undefined) : err(result.reason ?? '删除失败')
  }

  updateCardField(id: string, field: string, value: unknown): ApiResult<void> {
    if (field === 'id') return err('id 字段只读')
    if (!getCard(id)) return err(`卡片 ${id} 不存在`)
    useCardStore.getState().updateField(id, field as keyof CognitiveCard, value as never)
    return ok(undefined)
  }

  updateCardFields(id: string, updates: Partial<CognitiveCard>): ApiResult<void> {
    if (!getCard(id)) return err(`卡片 ${id} 不存在`)
    const { id: _ignored, ...rest } = updates
    for (const [field, value] of Object.entries(rest)) {
      useCardStore.getState().updateField(id, field as keyof CognitiveCard, value as never)
    }
    return ok(undefined)
  }

  addCardCorpus(id: string, text: string): ApiResult<void> {
    if (!getCard(id)) return err(`卡片 ${id} 不存在`)
    if (!text.trim()) return err('语料内容不能为空')
    useCardStore.getState().addCorpus(id, text)
    return ok(undefined)
  }

  updateCardCorpus(id: string, index: number, text: string): ApiResult<void> {
    const card = getCard(id)
    if (!card) return err(`卡片 ${id} 不存在`)
    if (index < 0 || index >= card.corpus.length) return err(`语料索引 ${index} 超出范围`)
    useCardStore.getState().updateCorpus(id, index, text)
    return ok(undefined)
  }

  removeCardCorpus(id: string, index: number): ApiResult<void> {
    const card = getCard(id)
    if (!card) return err(`卡片 ${id} 不存在`)
    if (index < 0 || index >= card.corpus.length) return err(`语料索引 ${index} 超出范围`)
    useCardStore.getState().removeCorpus(id, index)
    return ok(undefined)
  }

  addCardBoundNode(cardId: string, nodeId: string): ApiResult<void> {
    if (!getCard(cardId)) return err(`卡片 ${cardId} 不存在`)
    if (!getNavNode(nodeId)) return err(`节点 ${nodeId} 不存在`)
    useCardStore.getState().addBoundNode(cardId, nodeId)
    return ok(undefined)
  }

  removeCardBoundNode(cardId: string, nodeId: string): ApiResult<void> {
    if (!getCard(cardId)) return err(`卡片 ${cardId} 不存在`)
    useCardStore.getState().removeBoundNode(cardId, nodeId)
    return ok(undefined)
  }

  // ============================================================
  // 导航节点
  // ============================================================

  getAllNavNodes(): NavNode[] {
    return useNavNodeStore.getState().allNodes
  }

  getNavNode(id: string): NavNode | undefined {
    return getNavNode(id)
  }

  searchNavNodes(query: string): NavNode[] {
    return filterNodes(this.getAllNavNodes(), query)
  }

  createNavNode(): ApiResult<NavNode> {
    try {
      return ok(useNavNodeStore.getState().createNavNode())
    } catch (e) {
      return err((e as Error).message)
    }
  }

  deleteNavNode(id: string): ApiResult<void> {
    if (!getNavNode(id)) return err(`节点 ${id} 不存在`)
    const store = useNavNodeStore.getState()
    store.selectNode(id)
    const result = useNavNodeStore.getState().deleteNavNode()
    return result.ok ? ok(undefined) : err(result.reason ?? '删除失败')
  }

  updateNavNodeField(id: string, field: string, value: unknown): ApiResult<void> {
    if (field === 'id') return err('id 字段只读')
    if (!getNavNode(id)) return err(`节点 ${id} 不存在`)
    useNavNodeStore.getState().selectNode(id)
    useNavNodeStore.getState().updateField(field as keyof NavNode, value as never)
    return ok(undefined)
  }

  addNavNodeBoundCard(nodeId: string, cardId: string): ApiResult<void> {
    if (!getNavNode(nodeId)) return err(`节点 ${nodeId} 不存在`)
    if (!getCard(cardId)) return err(`卡片 ${cardId} 不存在`)
    useNavNodeStore.getState().selectNode(nodeId)
    useNavNodeStore.getState().addBoundCard(cardId)
    return ok(undefined)
  }

  removeNavNodeBoundCard(nodeId: string, cardId: string): ApiResult<void> {
    if (!getNavNode(nodeId)) return err(`节点 ${nodeId} 不存在`)
    useNavNodeStore.getState().selectNode(nodeId)
    useNavNodeStore.getState().removeBoundCard(cardId)
    return ok(undefined)
  }

  // ============================================================
  // 出向连接
  // ============================================================

  getNextNodes(nodeId: string): NextNodeItem[] {
    return useNavStore.getState().getNextNodes(nodeId)
  }

  getPrevNodes(nodeId: string): NextNodeItem[] {
    return useNavStore.getState().getPrevNodes(nodeId)
  }

  addNextNodeRef(fromId: string, ref: NextNodeRefInput): ApiResult<void> {
    const from = getNavNode(fromId)
    if (!from) return err(`节点 ${fromId} 不存在`)
    if (!getNavNode(ref.target_id)) return err(`目标节点 ${ref.target_id} 不存在`)
    if (fromId === ref.target_id) return err('不允许建立自环连接')
    if (from.next_nodes.some((e) => e.target_id === ref.target_id)) return err('连接已存在')

    from.next_nodes.push({
      target_id: ref.target_id,
      preset_weight: priorityToWeight(ref.preset_priority ?? 1),
      browse_weight: ref.browse_priority !== undefined ? priorityToWeight(ref.browse_priority) : 0,
      connection_type: ref.connection_type ?? 'user_added',
    })
    navNodeMap.set(fromId, from)
    syncAfterConnectionMutation()
    return ok(undefined)
  }

  updateNextNodeRef(fromId: string, targetId: string, updates: Partial<NextNodeRefInput>): ApiResult<void> {
    const from = getNavNode(fromId)
    if (!from) return err(`节点 ${fromId} 不存在`)
    const idx = from.next_nodes.findIndex((e) => e.target_id === targetId)
    if (idx < 0) return err(`连接 ${fromId} → ${targetId} 不存在`)

    const current = from.next_nodes[idx]
    from.next_nodes[idx] = {
      ...current,
      ...(updates.preset_priority !== undefined
        ? { preset_weight: priorityToWeight(updates.preset_priority) }
        : {}),
      ...(updates.browse_priority !== undefined
        ? { browse_weight: priorityToWeight(updates.browse_priority) }
        : {}),
      ...(updates.connection_type !== undefined ? { connection_type: updates.connection_type } : {}),
    }
    navNodeMap.set(fromId, from)
    syncAfterConnectionMutation()
    return ok(undefined)
  }

  removeNextNodeRef(fromId: string, targetId: string): ApiResult<void> {
    if (!getNavNode(fromId)) return err(`节点 ${fromId} 不存在`)
    const removed = removeQuickConnection(fromId, targetId)
    return removed ? ok(undefined) : err(`连接 ${fromId} → ${targetId} 不存在`)
  }

  getConnectionStatus(fromId: string, toId: string): ConnectionStatusResult {
    return getConnectionStatus(fromId, toId)
  }

  ensureQuickConnection(fromId: string, toId: string): boolean {
    return ensureQuickConnection(fromId, toId)
  }

  fillAllMissingConnections(waypointIds: string[]): number {
    const nodes = waypointIds.map((id) => getNavNode(id)).filter((n): n is NavNode => Boolean(n))
    return fillAllMissingConnections(nodes)
  }

  // ============================================================
  // 导航图
  // ============================================================

  getAllEdges(): GraphEdge[] {
    return useNavStore.getState().allEdges
  }

  setCurrentNode(nodeId: string): void {
    useNavStore.getState().setCurrentNode(nodeId)
  }

  setNavMode(mode: NavMode): void {
    useNavStore.getState().setMode(mode)
  }

  addWaypoint(nodeId: string): ApiResult<void> {
    const node = getNavNode(nodeId)
    if (!node) return err(`节点 ${nodeId} 不存在`)
    useNavStore.getState().addWaypoint(node)
    return ok(undefined)
  }

  removeWaypoint(index: number): void {
    useNavStore.getState().removeWaypoint(index)
  }

  clearWaypoints(): void {
    useNavStore.getState().clearWaypoints()
  }

  getWaypoints(): NavNode[] {
    return useNavStore.getState().waypoints
  }

  getWeightedNextNodes(nodeId: string): WeightedRef[] {
    const node = getNavNode(nodeId)
    return node ? composeWeights(node) : []
  }

  syncGraphFromSource(): void {
    useNavStore.getState().syncFromSource()
  }

  // ============================================================
  // 路线规划
  // ============================================================

  setWaypointMode(mode: WaypointMode): void {
    usePlanStore.getState().setWaypointMode(mode)
  }

  setWeightMode(mode: WeightMode): void {
    usePlanStore.getState().setWeightMode(mode)
  }

  generatePlans(waypointIds?: string[]): ApiResult<RoutePlan[]> {
    let nodes: NavNode[]
    if (waypointIds && waypointIds.length > 0) {
      const missing = waypointIds.filter((id) => !getNavNode(id))
      if (missing.length > 0) return err(`节点不存在: ${missing.join(', ')}`)
      nodes = waypointIds.map((id) => getNavNode(id)!)
    } else {
      nodes = useNavStore.getState().waypoints
    }
    if (nodes.length < 2) return err('途经点至少需要 2 个')

    const weightMode = nodes[0]?.priority_config?.mode ?? usePlanStore.getState().weightMode
    usePlanStore.getState().generatePlans(nodes, weightMode)
    return ok(usePlanStore.getState().plans)
  }

  selectPlan(planId: string): ApiResult<void> {
    if (!usePlanStore.getState().plans.some((p) => p.id === planId)) {
      return err(`计划 ${planId} 不存在`)
    }
    usePlanStore.getState().selectPlan(planId)
    return ok(undefined)
  }

  getAllPlans(): RoutePlan[] {
    return usePlanStore.getState().plans
  }

  getSelectedPlan(): RoutePlan | undefined {
    const { plans, selectedPlanId } = usePlanStore.getState()
    return plans.find((p) => p.id === selectedPlanId)
  }

  getRecommendedPlan(): RoutePlan | undefined {
    return usePlanStore.getState().plans.find((p) => p.isRecommended)
  }

  replan(): void {
    usePlanStore.getState().replan()
  }

  // ============================================================
  // 浏览
  // ============================================================

  initBrowseFromPlan(planId: string): ApiResult<void> {
    const plan = usePlanStore.getState().plans.find((p) => p.id === planId)
    if (!plan) return err(`计划 ${planId} 不存在`)
    useBrowseStore.getState().initFromSequence(plan.sequence)
    return ok(undefined)
  }

  initBrowseFromSequence(nodeIds: string[]): ApiResult<void> {
    const missing = nodeIds.filter((id) => !getNavNode(id))
    if (missing.length > 0) return err(`节点不存在: ${missing.join(', ')}`)
    if (nodeIds.length === 0) return err('节点序列不能为空')
    useBrowseStore.getState().initFromSequence(nodeIds.map((id) => getNavNode(id)!))
    return ok(undefined)
  }

  getCurrentBrowseCards(): BrowseCard[] {
    return useBrowseStore.getState().cards
  }

  getBrowseProgress(): {
    waypointIndex: number
    totalWaypoints: number
    cardIndex: number
    totalCards: number
  } {
    const { wpIndex, waypoints, currentIndex, cards } = useBrowseStore.getState()
    return { waypointIndex: wpIndex, totalWaypoints: waypoints.length, cardIndex: currentIndex, totalCards: cards.length }
  }

  nextCard(): ApiResult<void> {
    const { currentIndex, cards } = useBrowseStore.getState()
    if (currentIndex >= cards.length - 1) return err('已经是最后一张卡片')
    useBrowseStore.getState().nextCard()
    return ok(undefined)
  }

  prevCard(): ApiResult<void> {
    const { currentIndex } = useBrowseStore.getState()
    if (currentIndex <= 0) return err('已经是第一张卡片')
    useBrowseStore.getState().prevCard()
    return ok(undefined)
  }

  nextWaypoint(): ApiResult<void> {
    const { wpIndex, waypoints } = useBrowseStore.getState()
    if (wpIndex >= waypoints.length - 1) return err('已经是最后一站')
    useBrowseStore.getState().nextWaypoint()
    return ok(undefined)
  }

  // ============================================================
  // 搜索
  // ============================================================

  setSearchQuery(query: string): void {
    useSearchStore.getState().setQuery(query)
  }

  setMatchMode(mode: MatchMode): void {
    useSearchStore.getState().setMatchMode(mode)
  }

  /** 执行搜索：关键词模式走 300ms 防抖，向量模式等待异步匹配完成 */
  async search(query: string, mode?: MatchMode): Promise<MatchedCard[]> {
    const store = useSearchStore.getState()
    if (mode && mode !== store.matchMode) store.setMatchMode(mode)
    useSearchStore.getState().setQuery(query)

    await sleep(350) // 等待防抖触发匹配
    // 向量模式：等待异步完成（最多 10s）
    const deadline = Date.now() + 10000
    while (useSearchStore.getState().isVectorLoading && Date.now() < deadline) {
      await sleep(100)
    }
    return useSearchStore.getState().matchedCards
  }

  selectMatchedCard(cardId: string): ApiResult<void> {
    if (!getCard(cardId)) return err(`卡片 ${cardId} 不存在`)
    useSearchStore.getState().selectCard(cardId)
    return ok(undefined)
  }

  getMatchedCards(): MatchedCard[] {
    return useSearchStore.getState().matchedCards
  }

  getBoundNodesForSelectedCard(): NavNode[] {
    return useSearchStore.getState().boundNodes
  }

  async retryVectorMatch(): Promise<void> {
    useSearchStore.getState().retryVectorMatch()
    const deadline = Date.now() + 10000
    while (useSearchStore.getState().isVectorLoading && Date.now() < deadline) {
      await sleep(100)
    }
  }

  // ============================================================
  // 树形管理
  // ============================================================

  getTreeFlatData(): TreeNodeData[] {
    return useTreeStore.getState().flatData
  }

  getRootNodes(): TreeNodeData[] {
    return getRootNodes(this.getTreeFlatData())
  }

  getTreeChildren(parentId: string): TreeNodeData[] {
    return getTreeChildren(this.getTreeFlatData(), parentId)
  }

  getTreePath(nodeId: string): { path: string; label: string }[] {
    return getFullPath(this.getTreeFlatData(), nodeId)
  }

  toggleTreeNode(nodeId: string): void {
    useTreeStore.getState().toggleNode(nodeId)
  }

  expandTreeAncestors(nodeId: string): void {
    useTreeStore.getState().expandAncestors(nodeId)
  }

  searchTree(query: string): void {
    useTreeStore.getState().setSearch(query)
  }

  selectTreeNode(nodeId: string): void {
    useTreeStore.getState().selectNode(nodeId)
  }

  // ============================================================
  // YAML 导入导出
  // ============================================================

  exportToYAML(): string {
    return exportAllToYAML(this.getAllCards(), this.getAllNavNodes())
  }

  /** 浏览器端触发下载；Node 环境请直接写文件（CLI yaml export --file） */
  downloadYAML(filename?: string): void {
    if (typeof document === 'undefined') {
      throw new Error('downloadYAML 仅在浏览器环境可用；Node 环境请将 exportToYAML() 的结果写入文件')
    }
    browserDownloadYAML(this.exportToYAML(), filename)
  }

  parseYAML(raw: string): ApiResult<YamlData> {
    const result = parseAndValidateYAML(raw, this.getAllCards(), this.getAllNavNodes())
    if (!result.ok) {
      return err(result.errors.map((e) => `[${e.type}]${e.itemId ? ` ${e.itemId}:` : ' '}${e.message}`).join('\n'))
    }
    return ok(result.data)
  }

  computeImportPreview(raw: string): ApiResult<ImportPreview> {
    const parsed = this.parseYAML(raw)
    if (!parsed.ok) return err(parsed.error)
    return ok(computeImportPreview(parsed.data, this.getAllCards(), this.getAllNavNodes()))
  }

  /** 执行导入合并（upsert）并同步所有 Store */
  importYAML(raw: string): ApiResult<ImportPreview> {
    const parsed = this.parseYAML(raw)
    if (!parsed.ok) return err(parsed.error)
    const preview = computeImportPreview(parsed.data, this.getAllCards(), this.getAllNavNodes())

    mergeImportedData(parsed.data, {
      onCardsMerged: (cards) => {
        useCardStore.setState({ allCards: [...cards] })
        useTreeStore.setState({
          flatData: cards.map((c) => ({ id: c.id, title: c.title, type: c.type, tag: c.tag })),
        })
      },
      onNodesMerged: (nodes) => {
        useNavNodeStore.setState({ allNodes: [...nodes] })
        useNavStore.getState().syncFromSource()
      },
    })
    return ok(preview)
  }

  // ============================================================
  // AI 辅助生成
  // ============================================================

  private async trackGeneration<T>(task: () => Promise<T>): Promise<T> {
    this.generatingCount++
    try {
      return await task()
    } finally {
      this.generatingCount--
    }
  }

  async generateCardTitle(cardId: string): Promise<ApiResult<string>> {
    const card = getCard(cardId)
    if (!card) return err(`卡片 ${cardId} 不存在`)
    const children = this.getChildCards(cardId)
    if (card.corpus.length === 0 && children.length === 0) {
      return err('缺少生成依据，请先添加语料或子卡片')
    }
    const result = await this.trackGeneration(() => aiCardTitle(card, children))
    return result ? ok(result.text) : err('生成失败，请重试')
  }

  async generateCardDescription(cardId: string): Promise<ApiResult<string>> {
    const card = getCard(cardId)
    if (!card) return err(`卡片 ${cardId} 不存在`)
    const children = this.getChildCards(cardId)
    if (card.corpus.length === 0 && children.length === 0) {
      return err('缺少生成依据，请先添加语料或子卡片')
    }
    const result = await this.trackGeneration(() => aiCardDescription(card, children))
    return result ? ok(result.text) : err('生成失败，请重试')
  }

  async generateNodeLabel(nodeId: string): Promise<ApiResult<string>> {
    const node = getNavNode(nodeId)
    if (!node) return err(`节点 ${nodeId} 不存在`)
    const boundCards = (node.bound_cards ?? [])
      .map((id) => getCard(id))
      .filter((c): c is CognitiveCard => Boolean(c))
    if (boundCards.length === 0) return err('缺少生成依据，请先绑定认知卡片')
    const result = await this.trackGeneration(() => aiNodeLabel(node, boundCards))
    return result ? ok(result.text) : err('生成失败，请重试')
  }

  async generateNodeDescription(nodeId: string): Promise<ApiResult<string>> {
    const node = getNavNode(nodeId)
    if (!node) return err(`节点 ${nodeId} 不存在`)
    const boundCards = (node.bound_cards ?? [])
      .map((id) => getCard(id))
      .filter((c): c is CognitiveCard => Boolean(c))
    const nav = useNavStore.getState()
    const prevNodes = nav.getPrevNodes(nodeId).map((x) => x.node)
    const nextNodes = nav.getNextNodes(nodeId).map((x) => x.node)
    const hasSource =
      boundCards.some((c) => c.corpus.length > 0 || c.description) ||
      prevNodes.some((n) => n.description) ||
      nextNodes.some((n) => n.description)
    if (!hasSource) return err('缺少生成依据，请先绑定卡片或连接前驱/后继节点')
    const result = await this.trackGeneration(() =>
      aiNodeDescription(node, boundCards, prevNodes, nextNodes),
    )
    return result ? ok(result.text) : err('生成失败，请重试')
  }

  isGenerating(): boolean {
    return this.generatingCount > 0
  }

  // ============================================================
  // 视图与面板
  // ============================================================

  switchView(viewName: ViewName): void {
    useViewStore.getState().switchView(viewName)
  }

  getActiveView(): ViewName {
    return useViewStore.getState().activeView
  }

  getPanelState(): { node: NavNode | null; position: PanelPosition; hidden: boolean } {
    const { node, position, hidden } = usePanelStore.getState()
    return { node, position, hidden }
  }

  setPanelNode(nodeId: string | null): void {
    if (nodeId === null) {
      usePanelStore.getState().clearNode()
      return
    }
    const node = getNavNode(nodeId)
    if (node) usePanelStore.getState().setNode(node)
  }

  setPanelPosition(position: PanelPosition): void {
    usePanelStore.getState().setPosition(position)
  }
}
