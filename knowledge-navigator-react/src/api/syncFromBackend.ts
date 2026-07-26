import { BackendAdapter } from './BackendAdapter'
import { isProMode } from '../config/backend'
import { cognitiveCards } from '../data/cards'
import { allEdges, allNavNodes, navNodeMap } from '../data/allNavNodes'
import type { CognitiveCard, NavNode, TreeNodeData } from '../data/types'
import { useCardStore } from '../store/cardStore'
import { useNavNodeStore } from '../store/navNodeStore'
import { useTreeStore } from '../store/treeStore'
import { useNavStore } from '../store/navStore'

/**
 * pro 模式（完整模式）数据水合：启动时（或切换后端配置后）从 FastAPI 后端拉取
 * 卡片与导航节点，原地替换共享数据源并刷新各 Zustand store。
 * lite 模式（轻量模式）或后端不可达时静默回退到内置静态数据。
 */
export async function hydrateFromBackend(): Promise<boolean> {
  if (!isProMode()) return false

  const api = BackendAdapter.getInstance()
  try {
    const [cards, nodes] = await Promise.all([
      api.get<CognitiveCard[]>('/api/cards'),
      api.get<NavNode[]>('/api/nodes'),
    ])

    // 1. 原地替换共享数组（const 绑定不可重赋值，splice 保持引用不变）
    cognitiveCards.splice(0, cognitiveCards.length, ...cards)
    allNavNodes.splice(0, allNavNodes.length, ...nodes)

    // 2. 重建节点索引与派生边（与 allNavNodes.ts 中的推导逻辑一致）
    navNodeMap.clear()
    for (const n of allNavNodes) navNodeMap.set(n.id, n)
    allEdges.splice(
      0,
      allEdges.length,
      ...allNavNodes.flatMap((n) =>
        n.next_nodes.map((e) => ({
          source: n.id,
          target: e.target_id,
          weight: e.preset_weight,
        })),
      ),
    )

    // 3. 刷新各 store（setState 自动触发订阅组件重渲染）
    useCardStore.setState({ allCards: [...cognitiveCards] })
    useNavNodeStore.setState({ allNodes: [...allNavNodes], selectedNodeId: null })
    const flatData: TreeNodeData[] = cards.map((c) => ({
      id: c.id,
      title: c.title,
      type: c.type,
      tag: c.tag,
    }))
    useTreeStore.setState({ flatData, selectedId: null })
    useNavStore.getState().syncFromSource()

    return true
  } catch (e) {
    console.warn('[hydrate] 后端数据拉取失败，回退到本地静态数据：', e)
    return false
  }
}
