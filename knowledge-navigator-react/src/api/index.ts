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
import { isProMode } from '../config/backend'
import { getActiveGraphId } from '../config/graphs'
import { BackendAdapter, ApiError } from './BackendAdapter'

// ============================================================
// 辅助类型与工具
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

const enc = encodeURIComponent

/** pro 错误 → 中文提示（404 视为"后端暂未实现"，网络/超时视为连接问题） */
function remoteErrorMessage(e: unknown): string {
  if (e instanceof ApiError) {
    if (e.status === 404) return '该功能后端暂未实现'
    return `后端错误 (${e.status}): ${e.message}`
  }
  return '后端服务不可用，请检查连接'
}

/** 包装 pro 调用为 ApiResult */
async function remoteResult<T>(fn: () => Promise<T>): Promise<ApiResult<T>> {
  try {
    return ok(await fn())
  } catch (e) {
    return err(remoteErrorMessage(e))
  }
}

/** 本地连接变更后同步画布与节点管理状态 */
function syncAfterConnectionMutation(): void {
  useNavStore.getState().syncFromSource()
  useNavNodeStore.setState({ allNodes: [...allNavNodes] })
}

/**
 * Knowledge Navigator 程序化 API（async 全异步签名）。
 * lite 模式（轻量模式）：操作 Zustand Store 与共享数据源；
 * pro 模式（完整模式）：通过 BackendAdapter 调用 Python FastAPI 后端（backend-architecture.md §4.2）。
 */
export class KnowledgeNavigatorAPI {
  private adapter = BackendAdapter.getInstance()

  /** AI 生成中的请求计数（isGenerating 用） */
  private generatingCount = 0

  /** 构建带图参数的 URL */
  private g(path: string): string {
    return `${path}?graph=${getActiveGraphId()}`
  }

  // ============================================================
  // 认知卡片
  // ============================================================

  async getAllCards(): Promise<CognitiveCard[]> {
    if (isProMode()) return this.adapter.get<CognitiveCard[]>(this.g('/api/cards'))
    return useCardStore.getState().allCards
  }

  async getCard(id: string): Promise<CognitiveCard | undefined> {
    if (isProMode()) {
      try {
        return await this.adapter.get<CognitiveCard>(`/api/cards/${enc(id)}`)
      } catch {
        return undefined
      }
    }
    return getCard(id)
  }

  async getChildCards(parentId: string): Promise<CognitiveCard[]> {
    if (isProMode()) {
      return this.adapter.get<CognitiveCard[]>(`/api/cards/${enc(parentId)}/children`)
    }
    const all = await this.getAllCards()
    return all.filter((c) => {
      if (c.id === parentId) return false
      try {
        return deriveParent(c.id) === parentId
      } catch {
        return false
      }
    })
  }

  async createCard(parentId?: string): Promise<ApiResult<CognitiveCard>> {
    if (isProMode()) {
      return remoteResult(() => this.adapter.post<CognitiveCard>('/api/cards', { parent_id: parentId }))
    }
    try {
      if (parentId && !getCard(parentId)) return err(`父卡片 ${parentId} 不存在`)
      return ok(useCardStore.getState().createCard(parentId ?? null))
    } catch (e) {
      return err((e as Error).message)
    }
  }

  async deleteCard(id: string): Promise<ApiResult<void>> {
    if (isProMode()) {
      return remoteResult(async () => {
        await this.adapter.delete(`/api/cards/${enc(id)}`)
        return undefined
      })
    }
    if (!getCard(id)) return err(`卡片 ${id} 不存在`)
    const result = useCardStore.getState().deleteCard(id)
    return result.ok ? ok(undefined) : err(result.reason ?? '删除失败')
  }

  async updateCardField(id: string, field: string, value: unknown): Promise<ApiResult<void>> {
    if (field === 'id') return err('id 字段只读')
    if (isProMode()) {
      return remoteResult(async () => {
        await this.adapter.put(`/api/cards/${enc(id)}`, { [field]: value })
        return undefined
      })
    }
    if (!getCard(id)) return err(`卡片 ${id} 不存在`)
    useCardStore.getState().updateField(id, field as keyof CognitiveCard, value as never)
    return ok(undefined)
  }

  async updateCardFields(id: string, updates: Partial<CognitiveCard>): Promise<ApiResult<void>> {
    const { id: _ignored, ...rest } = updates
    if (isProMode()) {
      return remoteResult(async () => {
        await this.adapter.put(`/api/cards/${enc(id)}`, rest)
        return undefined
      })
    }
    if (!getCard(id)) return err(`卡片 ${id} 不存在`)
    for (const [field, value] of Object.entries(rest)) {
      useCardStore.getState().updateField(id, field as keyof CognitiveCard, value as never)
    }
    return ok(undefined)
  }

  async addCardCorpus(id: string, text: string): Promise<ApiResult<void>> {
    if (!text.trim()) return err('语料内容不能为空')
    if (isProMode()) {
      return remoteResult(async () => {
        await this.adapter.post(`/api/cards/${enc(id)}/corpus`, { text })
        return undefined
      })
    }
    if (!getCard(id)) return err(`卡片 ${id} 不存在`)
    useCardStore.getState().addCorpus(id, text)
    return ok(undefined)
  }

  async updateCardCorpus(id: string, index: number, text: string): Promise<ApiResult<void>> {
    if (isProMode()) {
      return remoteResult(async () => {
        await this.adapter.put(`/api/cards/${enc(id)}/corpus/${index}`, { text })
        return undefined
      })
    }
    const card = getCard(id)
    if (!card) return err(`卡片 ${id} 不存在`)
    if (index < 0 || index >= card.corpus.length) return err(`语料索引 ${index} 超出范围`)
    useCardStore.getState().updateCorpus(id, index, text)
    return ok(undefined)
  }

  async removeCardCorpus(id: string, index: number): Promise<ApiResult<void>> {
    if (isProMode()) {
      return remoteResult(async () => {
        await this.adapter.delete(`/api/cards/${enc(id)}/corpus/${index}`)
        return undefined
      })
    }
    const card = getCard(id)
    if (!card) return err(`卡片 ${id} 不存在`)
    if (index < 0 || index >= card.corpus.length) return err(`语料索引 ${index} 超出范围`)
    useCardStore.getState().removeCorpus(id, index)
    return ok(undefined)
  }

  /** 卡片绑定节点：pro 模式（完整模式）经整卡字段更新（后端 cards 路由无独立 bind 端点） */
  async addCardBoundNode(cardId: string, nodeId: string): Promise<ApiResult<void>> {
    if (isProMode()) {
      return remoteResult(async () => {
        const card = await this.adapter.get<CognitiveCard>(`/api/cards/${enc(cardId)}`)
        const bound = card.bound_nodes ?? []
        if (!bound.includes(nodeId)) {
          await this.adapter.put(`/api/cards/${enc(cardId)}`, { bound_nodes: [...bound, nodeId] })
        }
        return undefined
      })
    }
    if (!getCard(cardId)) return err(`卡片 ${cardId} 不存在`)
    if (!getNavNode(nodeId)) return err(`节点 ${nodeId} 不存在`)
    useCardStore.getState().addBoundNode(cardId, nodeId)
    return ok(undefined)
  }

  async removeCardBoundNode(cardId: string, nodeId: string): Promise<ApiResult<void>> {
    if (isProMode()) {
      return remoteResult(async () => {
        const card = await this.adapter.get<CognitiveCard>(`/api/cards/${enc(cardId)}`)
        await this.adapter.put(`/api/cards/${enc(cardId)}`, {
          bound_nodes: (card.bound_nodes ?? []).filter((nid) => nid !== nodeId),
        })
        return undefined
      })
    }
    if (!getCard(cardId)) return err(`卡片 ${cardId} 不存在`)
    useCardStore.getState().removeBoundNode(cardId, nodeId)
    return ok(undefined)
  }

  // ============================================================
  // 导航节点
  // ============================================================

  async getAllNavNodes(): Promise<NavNode[]> {
    if (isProMode()) return this.adapter.get<NavNode[]>(this.g('/api/nodes'))
    return useNavNodeStore.getState().allNodes
  }

  async getNavNode(id: string): Promise<NavNode | undefined> {
    if (isProMode()) {
      try {
        return await this.adapter.get<NavNode>(`/api/nodes/${enc(id)}`)
      } catch {
        return undefined
      }
    }
    return getNavNode(id)
  }

  async searchNavNodes(query: string): Promise<NavNode[]> {
    if (isProMode()) return this.adapter.get<NavNode[]>(`/api/nodes?q=${enc(query)}`)
    return filterNodes(useNavNodeStore.getState().allNodes, query)
  }

  async createNavNode(): Promise<ApiResult<NavNode>> {
    if (isProMode()) {
      return remoteResult(() => this.adapter.post<NavNode>('/api/nodes', {}))
    }
    try {
      return ok(useNavNodeStore.getState().createNavNode())
    } catch (e) {
      return err((e as Error).message)
    }
  }

  async deleteNavNode(id: string): Promise<ApiResult<void>> {
    if (isProMode()) {
      return remoteResult(async () => {
        await this.adapter.delete(`/api/nodes/${enc(id)}`)
        return undefined
      })
    }
    if (!getNavNode(id)) return err(`节点 ${id} 不存在`)
    useNavNodeStore.getState().selectNode(id)
    const result = useNavNodeStore.getState().deleteNavNode()
    return result.ok ? ok(undefined) : err(result.reason ?? '删除失败')
  }

  async updateNavNodeField(id: string, field: string, value: unknown): Promise<ApiResult<void>> {
    if (field === 'id') return err('id 字段只读')
    if (isProMode()) {
      return remoteResult(async () => {
        await this.adapter.put(`/api/nodes/${enc(id)}`, { [field]: value })
        return undefined
      })
    }
    if (!getNavNode(id)) return err(`节点 ${id} 不存在`)
    useNavNodeStore.getState().selectNode(id)
    useNavNodeStore.getState().updateField(field as keyof NavNode, value as never)
    return ok(undefined)
  }

  async addNavNodeBoundCard(nodeId: string, cardId: string): Promise<ApiResult<void>> {
    if (isProMode()) {
      return remoteResult(async () => {
        await this.adapter.post(`/api/nodes/${enc(nodeId)}/bind-card`, { card_id: cardId })
        return undefined
      })
    }
    if (!getNavNode(nodeId)) return err(`节点 ${nodeId} 不存在`)
    if (!getCard(cardId)) return err(`卡片 ${cardId} 不存在`)
    useNavNodeStore.getState().selectNode(nodeId)
    useNavNodeStore.getState().addBoundCard(cardId)
    return ok(undefined)
  }

  async removeNavNodeBoundCard(nodeId: string, cardId: string): Promise<ApiResult<void>> {
    if (isProMode()) {
      return remoteResult(async () => {
        await this.adapter.delete(`/api/nodes/${enc(nodeId)}/bind-card/${enc(cardId)}`)
        return undefined
      })
    }
    if (!getNavNode(nodeId)) return err(`节点 ${nodeId} 不存在`)
    useNavNodeStore.getState().selectNode(nodeId)
    useNavNodeStore.getState().removeBoundCard(cardId)
    return ok(undefined)
  }

  // ============================================================
  // 出向连接
  // ============================================================

  async getNextNodes(nodeId: string): Promise<NextNodeItem[]> {
    if (isProMode()) return this.adapter.get<NextNodeItem[]>(`/api/nodes/${enc(nodeId)}/next`)
    return useNavStore.getState().getNextNodes(nodeId)
  }

  async getPrevNodes(nodeId: string): Promise<NextNodeItem[]> {
    if (isProMode()) return this.adapter.get<NextNodeItem[]>(`/api/nodes/${enc(nodeId)}/prev`)
    return useNavStore.getState().getPrevNodes(nodeId)
  }

  async addNextNodeRef(fromId: string, ref: NextNodeRefInput): Promise<ApiResult<void>> {
    if (isProMode()) {
      return remoteResult(async () => {
        await this.adapter.post(`/api/nodes/${enc(fromId)}/next`, ref)
        return undefined
      })
    }
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

  async updateNextNodeRef(
    fromId: string,
    targetId: string,
    updates: Partial<NextNodeRefInput>,
  ): Promise<ApiResult<void>> {
    if (isProMode()) {
      return remoteResult(async () => {
        await this.adapter.put(`/api/nodes/${enc(fromId)}/next/${enc(targetId)}`, updates)
        return undefined
      })
    }
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

  async removeNextNodeRef(fromId: string, targetId: string): Promise<ApiResult<void>> {
    if (isProMode()) {
      return remoteResult(async () => {
        await this.adapter.delete(`/api/nodes/${enc(fromId)}/next/${enc(targetId)}`)
        return undefined
      })
    }
    if (!getNavNode(fromId)) return err(`节点 ${fromId} 不存在`)
    const removed = removeQuickConnection(fromId, targetId)
    return removed ? ok(undefined) : err(`连接 ${fromId} → ${targetId} 不存在`)
  }

  async getConnectionStatus(fromId: string, toId: string): Promise<ConnectionStatusResult> {
    if (isProMode()) {
      return this.adapter.get<ConnectionStatusResult>(
        `/api/connections/status/${enc(fromId)}/${enc(toId)}`,
      )
    }
    return getConnectionStatus(fromId, toId)
  }

  async ensureQuickConnection(fromId: string, toId: string): Promise<boolean> {
    if (isProMode()) {
      try {
        await this.adapter.post('/api/connections/ensure', { from_id: fromId, to_id: toId })
        return true
      } catch {
        return false
      }
    }
    return ensureQuickConnection(fromId, toId)
  }

  async fillAllMissingConnections(waypointIds: string[]): Promise<number> {
    if (isProMode()) {
      const result = await this.adapter.post<{ count: number }>('/api/connections/fill-all', {
        waypoint_ids: waypointIds,
      })
      return result.count
    }
    const nodes = waypointIds.map((id) => getNavNode(id)).filter((n): n is NavNode => Boolean(n))
    return fillAllMissingConnections(nodes)
  }

  // ============================================================
  // 导航图
  // ============================================================

  async getAllEdges(): Promise<GraphEdge[]> {
    if (isProMode()) return this.adapter.get<GraphEdge[]>(this.g('/api/graph/edges'))
    return useNavStore.getState().allEdges
  }

  /** 中心节点 / 导航模式 / 途经点为会话内 UI 状态，两种模式均本地处理 */
  setCurrentNode(nodeId: string): void {
    useNavStore.getState().setCurrentNode(nodeId)
  }

  setNavMode(mode: NavMode): void {
    useNavStore.getState().setMode(mode)
  }

  async addWaypoint(nodeId: string): Promise<ApiResult<void>> {
    const node = await this.getNavNode(nodeId)
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

  async getWeightedNextNodes(nodeId: string): Promise<WeightedRef[]> {
    if (isProMode()) return this.adapter.get<WeightedRef[]>(`/api/nodes/${enc(nodeId)}/next`)
    const node = getNavNode(nodeId)
    return node ? composeWeights(node) : []
  }

  async syncGraphFromSource(): Promise<void> {
    if (isProMode()) {
      await this.adapter.post('/api/graph/sync')
      return
    }
    useNavStore.getState().syncFromSource()
  }

  // ============================================================
  // 路线规划
  // ============================================================

  /** 排序 / 权重模式为会话状态，两种模式均本地处理 */
  setWaypointMode(mode: WaypointMode): void {
    usePlanStore.getState().setWaypointMode(mode)
  }

  setWeightMode(mode: WeightMode): void {
    usePlanStore.getState().setWeightMode(mode)
  }

  async generatePlans(waypointIds?: string[]): Promise<ApiResult<RoutePlan[]>> {
    if (isProMode()) {
      return remoteResult(async () => {
        const plans = await this.adapter.post<RoutePlan[]>('/api/plan/generate', {
          waypoint_ids: waypointIds,
        })
        // 镜像到本地 store，保证 getSelectedPlan / getRecommendedPlan 可用
        usePlanStore.setState({ plans, selectedPlanId: plans.find((p) => p.isRecommended)?.id ?? plans[0]?.id ?? null })
        return plans
      })
    }
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

  async selectPlan(planId: string): Promise<ApiResult<void>> {
    if (isProMode()) {
      return remoteResult(async () => {
        await this.adapter.post(`/api/plan/plans/${enc(planId)}/select`)
        usePlanStore.setState({ selectedPlanId: planId })
        return undefined
      })
    }
    if (!usePlanStore.getState().plans.some((p) => p.id === planId)) {
      return err(`计划 ${planId} 不存在`)
    }
    usePlanStore.getState().selectPlan(planId)
    return ok(undefined)
  }

  async getAllPlans(): Promise<RoutePlan[]> {
    if (isProMode()) return this.adapter.get<RoutePlan[]>('/api/plan/plans')
    return usePlanStore.getState().plans
  }

  async getSelectedPlan(): Promise<RoutePlan | undefined> {
    const { plans, selectedPlanId } = usePlanStore.getState()
    if (isProMode()) {
      const remotePlans = await this.getAllPlans()
      return remotePlans.find((p) => p.id === selectedPlanId)
    }
    return plans.find((p) => p.id === selectedPlanId)
  }

  async getRecommendedPlan(): Promise<RoutePlan | undefined> {
    const plans = await this.getAllPlans()
    return plans.find((p) => p.isRecommended)
  }

  async replan(): Promise<void> {
    if (isProMode()) {
      const plans = await this.adapter.post<RoutePlan[]>('/api/plan/replan')
      usePlanStore.setState({ plans })
      return
    }
    usePlanStore.getState().replan()
  }

  // ============================================================
  // 浏览
  // ============================================================

  async initBrowseFromPlan(planId: string): Promise<ApiResult<void>> {
    if (isProMode()) {
      return remoteResult(async () => {
        await this.adapter.post('/api/browse/start', { plan_id: planId })
        return undefined
      })
    }
    const plan = usePlanStore.getState().plans.find((p) => p.id === planId)
    if (!plan) return err(`计划 ${planId} 不存在`)
    useBrowseStore.getState().initFromSequence(plan.sequence)
    return ok(undefined)
  }

  async initBrowseFromSequence(nodeIds: string[]): Promise<ApiResult<void>> {
    if (nodeIds.length === 0) return err('节点序列不能为空')
    if (isProMode()) {
      return remoteResult(async () => {
        await this.adapter.post('/api/browse/start', { sequence: nodeIds })
        return undefined
      })
    }
    const missing = nodeIds.filter((id) => !getNavNode(id))
    if (missing.length > 0) return err(`节点不存在: ${missing.join(', ')}`)
    useBrowseStore.getState().initFromSequence(nodeIds.map((id) => getNavNode(id)!))
    return ok(undefined)
  }

  async getCurrentBrowseCards(): Promise<BrowseCard[]> {
    if (isProMode()) return this.adapter.get<BrowseCard[]>('/api/browse/cards')
    return useBrowseStore.getState().cards
  }

  async getBrowseProgress(): Promise<{
    waypointIndex: number
    totalWaypoints: number
    cardIndex: number
    totalCards: number
  }> {
    if (isProMode()) return this.adapter.get('/api/browse/status')
    const { wpIndex, waypoints, currentIndex, cards } = useBrowseStore.getState()
    return { waypointIndex: wpIndex, totalWaypoints: waypoints.length, cardIndex: currentIndex, totalCards: cards.length }
  }

  async nextCard(): Promise<ApiResult<void>> {
    if (isProMode()) {
      return remoteResult(async () => {
        await this.adapter.post('/api/browse/next')
        return undefined
      })
    }
    const { currentIndex, cards } = useBrowseStore.getState()
    if (currentIndex >= cards.length - 1) return err('已经是最后一张卡片')
    useBrowseStore.getState().nextCard()
    return ok(undefined)
  }

  async prevCard(): Promise<ApiResult<void>> {
    if (isProMode()) {
      return remoteResult(async () => {
        await this.adapter.post('/api/browse/prev')
        return undefined
      })
    }
    const { currentIndex } = useBrowseStore.getState()
    if (currentIndex <= 0) return err('已经是第一张卡片')
    useBrowseStore.getState().prevCard()
    return ok(undefined)
  }

  async nextWaypoint(): Promise<ApiResult<void>> {
    if (isProMode()) {
      return remoteResult(async () => {
        await this.adapter.post('/api/browse/waypoint')
        return undefined
      })
    }
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

  /** 执行搜索：本地走防抖+异步匹配；pro 调用 /api/search/query 并镜像结果到本地 store */
  async search(query: string, mode?: MatchMode): Promise<MatchedCard[]> {
    if (isProMode()) {
      const results = await this.adapter.post<MatchedCard[]>('/api/search/query', { query, mode })
      useSearchStore.setState({ query, matchedCards: results, ...(mode ? { matchMode: mode } : {}) })
      return results
    }
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

  async selectMatchedCard(cardId: string): Promise<ApiResult<void>> {
    const card = await this.getCard(cardId)
    if (!card) return err(`卡片 ${cardId} 不存在`)
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
    if (isProMode()) {
      const query = useSearchStore.getState().query
      const results = await this.adapter.post<MatchedCard[]>('/api/search/vector-match', { query })
      useSearchStore.setState({ matchedCards: results })
      return
    }
    useSearchStore.getState().retryVectorMatch()
    const deadline = Date.now() + 10000
    while (useSearchStore.getState().isVectorLoading && Date.now() < deadline) {
      await sleep(100)
    }
  }

  // ============================================================
  // 树形管理
  // ============================================================

  async getTreeFlatData(): Promise<TreeNodeData[]> {
    if (isProMode()) {
      const cards = await this.adapter.get<CognitiveCard[]>('/api/cards')
      return cards.map((c) => ({ id: c.id, title: c.title, type: c.type, tag: c.tag }))
    }
    return useTreeStore.getState().flatData
  }

  async getRootNodes(): Promise<TreeNodeData[]> {
    return getRootNodes(await this.getTreeFlatData())
  }

  async getTreeChildren(parentId: string): Promise<TreeNodeData[]> {
    return getTreeChildren(await this.getTreeFlatData(), parentId)
  }

  async getTreePath(nodeId: string): Promise<{ path: string; label: string }[]> {
    return getFullPath(await this.getTreeFlatData(), nodeId)
  }

  /** 展开 / 选中 / 搜索为纯 UI 状态，两种模式均本地处理 */
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

  async exportToYAML(): Promise<string> {
    if (isProMode()) {
      const result = await this.adapter.get<{ yaml: string } | string>('/api/yaml/export')
      return typeof result === 'string' ? result : result.yaml
    }
    return exportAllToYAML(useCardStore.getState().allCards, useNavNodeStore.getState().allNodes)
  }

  /** 浏览器端触发下载；Node 环境请直接写文件（CLI yaml export --file） */
  async downloadYAML(filename?: string): Promise<void> {
    if (typeof document === 'undefined') {
      throw new Error('downloadYAML 仅在浏览器环境可用；Node 环境请将 exportToYAML() 的结果写入文件')
    }
    browserDownloadYAML(await this.exportToYAML(), filename)
  }

  async parseYAML(raw: string): Promise<ApiResult<YamlData>> {
    if (isProMode()) {
      return remoteResult(() => this.adapter.post<YamlData>('/api/yaml/validate', { raw }))
    }
    const result = parseAndValidateYAML(raw, useCardStore.getState().allCards, useNavNodeStore.getState().allNodes)
    if (!result.ok) {
      return err(result.errors.map((e) => `[${e.type}]${e.itemId ? ` ${e.itemId}:` : ' '}${e.message}`).join('\n'))
    }
    return ok(result.data)
  }

  async computeImportPreview(raw: string): Promise<ApiResult<ImportPreview>> {
    if (isProMode()) {
      return remoteResult(() => this.adapter.post<ImportPreview>('/api/yaml/preview', { raw }))
    }
    const parsed = await this.parseYAML(raw)
    if (!parsed.ok) return err(parsed.error)
    return ok(
      computeImportPreview(parsed.data, useCardStore.getState().allCards, useNavNodeStore.getState().allNodes),
    )
  }

  /** 执行导入合并（upsert）；lite 模式（轻量模式）同步所有 Store */
  async importYAML(raw: string): Promise<ApiResult<ImportPreview>> {
    if (isProMode()) {
      return remoteResult(() => this.adapter.post<ImportPreview>('/api/yaml/import', { raw }))
    }
    const parsed = await this.parseYAML(raw)
    if (!parsed.ok) return err(parsed.error)
    const preview = computeImportPreview(
      parsed.data,
      useCardStore.getState().allCards,
      useNavNodeStore.getState().allNodes,
    )

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

  /** pro AI 生成统一入口 */
  private async remoteAiGenerate(endpoint: string, id: string): Promise<ApiResult<string>> {
    return remoteResult(async () => {
      const result = await this.adapter.post<{ result: string }>(`/api/ai/generate/${endpoint}`, { id })
      return result.result
    })
  }

  async generateCardTitle(cardId: string): Promise<ApiResult<string>> {
    if (isProMode()) {
      return this.trackGeneration(() => this.remoteAiGenerate('card-title', cardId))
    }
    const card = getCard(cardId)
    if (!card) return err(`卡片 ${cardId} 不存在`)
    const children = await this.getChildCards(cardId)
    if (card.corpus.length === 0 && children.length === 0) {
      return err('缺少生成依据，请先添加语料或子卡片')
    }
    const result = await this.trackGeneration(() => aiCardTitle(card, children))
    return result ? ok(result.text) : err('生成失败，请重试')
  }

  async generateCardDescription(cardId: string): Promise<ApiResult<string>> {
    if (isProMode()) {
      return this.trackGeneration(() => this.remoteAiGenerate('card-desc', cardId))
    }
    const card = getCard(cardId)
    if (!card) return err(`卡片 ${cardId} 不存在`)
    const children = await this.getChildCards(cardId)
    if (card.corpus.length === 0 && children.length === 0) {
      return err('缺少生成依据，请先添加语料或子卡片')
    }
    const result = await this.trackGeneration(() => aiCardDescription(card, children))
    return result ? ok(result.text) : err('生成失败，请重试')
  }

  async generateNodeLabel(nodeId: string): Promise<ApiResult<string>> {
    if (isProMode()) {
      return this.trackGeneration(() => this.remoteAiGenerate('node-label', nodeId))
    }
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
    if (isProMode()) {
      return this.trackGeneration(() => this.remoteAiGenerate('node-desc', nodeId))
    }
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

  /** 切换视图：本地即时生效；pro 模式（完整模式）同时通知后端（失败不阻塞） */
  switchView(viewName: ViewName): void {
    useViewStore.getState().switchView(viewName)
    if (isProMode()) {
      this.adapter.post('/api/view/switch', { view: viewName }).catch(() => {
        /* 后端视图同步失败不阻塞本地切换 */
      })
    }
  }

  getActiveView(): ViewName {
    return useViewStore.getState().activeView
  }

  /** 面板为纯 UI 状态，两种模式均本地处理 */
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

  // ============================================================
  // 跨图资源解析
  // ============================================================

  /** 解析单个跨图引用，返回完整资源数据 */
  async resolveCrossGraphNode(ref: string): Promise<NavNode | null> {
    if (!ref.includes('::')) return null
    if (!isProMode()) return null
    try {
      const res = await this.adapter.get<{ type: string; data: NavNode; graph_id: string; graph_label: string }>(
        `/api/graphs/resolve?ref=${enc(ref)}`,
      )
      if (res.type === 'node') return res.data
      return null
    } catch {
      return null
    }
  }

  /** 批量解析跨图引用 */
  async resolveCrossGraphBatch(refs: string[]): Promise<Array<{
    ref: string; type?: string; data?: NavNode; graph_id?: string; graph_label?: string; error?: string
  }>> {
    if (!isProMode()) return refs.map((ref) => ({ ref, error: '非 pro 模式' }))
    try {
      return await this.adapter.post('/api/graphs/resolve-batch', { refs })
    } catch {
      return refs.map((ref) => ({ ref, error: '批量解析失败' }))
    }
  }
}
