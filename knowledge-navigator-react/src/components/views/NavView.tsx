import React, { useRef, useState, useMemo, useEffect, useCallback } from 'react'
import styles from './NavView.module.css'
import Button from '../shared/Button'
import BreadcrumbNav from '../shared/BreadcrumbNav'
import NavCanvas from '../canvas/NavCanvas'
import ZoomControls from '../canvas/ZoomControls'
import NavModeToggle from '../nav/NavModeToggle'
import WaypointsBar from '../nav/WaypointsBar'
import ConnectionEditPopover from '../nav/ConnectionEditPopover'
import GraphMultiSelect from '../nav/GraphMultiSelect'
import DropDownPanel from '../panel/DropDownPanel'
import { useNavStore, getCurrentNode, type NextNodeItem } from '../../store/navStore'
import { useBrowseStore } from '../../store/browseStore'
import { usePanelStore } from '../../store/panelStore'
import { usePlanStore } from '../../store/planStore'
import { useViewStore } from '../../store/viewStore'
import { useToastStore } from '../shared/Toast'
import { useGraphStore } from '../../store/graphStore'
import { useDrillStore } from '../../store/drillStore'
import { useNavCanvas } from '../../hooks/useNavCanvas'
import { KnowledgeNavigatorAPI } from '../../api'
import {
  ensureQuickConnection,
  updateQuickConnection,
  removeQuickConnection,
  fillAllMissingConnections,
  getConnectionStatus,
} from '../../utils/quickConnectUtils'
import { getNavNode } from '../../data/allNavNodes'
import type { NavNode, CanvasDataResponse, GraphEdge } from '../../data/types'

type CanvasNode = CanvasDataResponse['nodes'][number]

const api = new KnowledgeNavigatorAPI()

const NavView: React.FC = () => {
  const canvasRef = useRef<HTMLDivElement>(null)

  const mode = useNavStore((s) => s.mode)
  const currentNodeId = useNavStore((s) => s.currentNodeId)
  const waypoints = useNavStore((s) => s.waypoints)
  const selectedGraphIds = useNavStore((s) => s.selectedGraphIds)
  const setMode = useNavStore((s) => s.setMode)
  const setCurrentNode = useNavStore((s) => s.setCurrentNode)
  const getNextNodes = useNavStore((s) => s.getNextNodes)
  const getPrevNodes = useNavStore((s) => s.getPrevNodes)
  const removeWaypoint = useNavStore((s) => s.removeWaypoint)
  const clearWaypoints = useNavStore((s) => s.clearWaypoints)

  const setPanelNode = usePanelStore((s) => s.setNode)
  const generatePlans = usePlanStore((s) => s.generatePlans)
  const switchView = useViewStore((s) => s.switchView)
  const toast = useToastStore((s) => s.show)
  const enterFreeBrowse = useBrowseStore((s) => s.enterFreeBrowse)

  const drillIn = useGraphStore((s) => s.drillIn)
  const graphs = useGraphStore((s) => s.graphs)
  const activeGraphId = useGraphStore((s) => s.activeGraphId)
  const drillStack = useDrillStore((s) => s.stack)
  const buildBreadcrumb = useDrillStore((s) => s.buildBreadcrumb)

  const currentNode = getCurrentNode({ currentNodeId })

  const inDrill = drillStack.length > 0

  /** 画布聚合数据（从后端获取） */
  const [canvasNodes, setCanvasNodes] = useState<CanvasNode[]>([])
  const [canvasEdges, setCanvasEdges] = useState<GraphEdge[]>([])

  /** 当 selectedGraphIds 变化时，从后端获取聚合画布数据 */
  useEffect(() => {
    if (inDrill) return // 钻入模式下使用单一图数据
    if (selectedGraphIds.length === 0) {
      setCanvasNodes([])
      setCanvasEdges([])
      return
    }
    let cancelled = false
    api.fetchCanvasData(selectedGraphIds).then((res) => {
      if (cancelled) return
      if (res.ok) {
        setCanvasNodes(res.data.nodes)
        setCanvasEdges(res.data.edges)
      } else {
        // 降级到本地数据
        setCanvasNodes([])
        setCanvasEdges([])
        toast('获取画布数据失败: ' + res.error)
      }
    })
    return () => { cancelled = true }
  }, [selectedGraphIds.join(','), inDrill]) // eslint-disable-line react-hooks/exhaustive-deps

  const hasCanvasData = inDrill || canvasNodes.length > 0

  /** 构建面包屑 */
  const breadcrumbItems = useMemo(() => {
    if (inDrill) {
      const activeMeta = graphs.find((g) => g.graph_id === activeGraphId)
      const currentLabel = activeMeta?.label ?? activeGraphId
      const steps = buildBreadcrumb(activeGraphId, currentLabel, currentNodeId, currentNode?.label ?? '')
      return steps.map((s) => ({
        path: s.graphId,
        label: s.nodeLabel || s.graphLabel || s.graphId,
      }))
    }
    return [{ path: 'top', label: 'top' }]
  }, [inDrill, graphs, activeGraphId, currentNodeId, currentNode, buildBreadcrumb])

  /** 从画布数据中提取子图节点和引用节点 id */
  const subGraphNodeIds = useMemo(() => {
    const ids = new Set<string>()
    for (const n of canvasNodes) {
      if (n._nodeType === 'subgraph' || n.sub_graph_id) ids.add(n.id)
    }
    return ids
  }, [canvasNodes])

  const refNodeIds = useMemo(() => {
    const ids = new Set<string>()
    for (const n of canvasNodes) {
      if (n._nodeType === 'ref') ids.add(n.id)
    }
    return ids
  }, [canvasNodes])

  /** 构建 canvasNodes → NavNode 的映射，供查找前驱后继 */
  const canvasNodeMap = useMemo(() => {
    const map = new Map<string, CanvasNode>()
    for (const n of canvasNodes) map.set(n.id, n)
    return map
  }, [canvasNodes])

  /** 在画布数据中查找节点的前驱 */
  const getCanvasPrevNodes = useCallback((nodeId: string) => {
    const result: { node: NavNode; ref: { weight: number; source: string; seq: number; target_id: string; preset_weight: number; browse_weight: number; connection_type: 'preset' | 'browse_derived' | 'user_added' } }[] = []
    for (const n of canvasNodes) {
      for (const ref of n.next_nodes ?? []) {
        if (ref.target_id === nodeId) {
          result.push({ node: n as NavNode, ref: { ...ref, weight: ref.preset_weight, source: 'preset' as const, seq: 0 } })
        }
      }
    }
    return result as NextNodeItem[]
  }, [canvasNodes])

  /** 在画布数据中查找节点的后继 */
  const getCanvasNextNodes = useCallback((nodeId: string) => {
    const node = canvasNodeMap.get(nodeId)
    if (!node) return [] as NextNodeItem[]
    return (node.next_nodes ?? [])
      .map((ref) => {
        const target = canvasNodeMap.get(ref.target_id)
        if (!target) return null
        return {
          node: target as NavNode,
          ref: { ...ref, weight: ref.preset_weight, source: 'preset' as const, seq: 0 },
        }
      })
      .filter((x): x is NonNullable<typeof x> => x !== null) as NextNodeItem[]
  }, [canvasNodeMap])

  const [editingConn, setEditingConn] = useState<{ fromId: string; toId: string } | null>(null)

  const handleQuickConnect = (fromId: string, toId: string) => {
    const created = ensureQuickConnection(fromId, toId)
    toast(created ? '已建立跳转连接' : '连接已存在')
  }

  const handleFillAll = () => {
    const count = fillAllMissingConnections(waypoints)
    toast(count > 0 ? `已建立 ${count} 条跳转连接` : '所有相邻途经点均已连接')
  }

  const handleNodeClick = (node: NavNode) => {
    // 保留 _nodeType 等聚合字段
    setPanelNode(node)
    setCurrentNode(node.id)
  }

  const { zoomIn, zoomOut, zoomReset } = useNavCanvas(
    canvasRef,
    mode,
    {
      allNodes: hasCanvasData ? canvasNodes as NavNode[] : [],
      allEdges: hasCanvasData ? canvasEdges : [],
      currentNode: hasCanvasData ? currentNode : null,
      prevNodes: currentNode && hasCanvasData ? (inDrill ? getPrevNodes(currentNode.id) : getCanvasPrevNodes(currentNode.id)) : [],
      nextNodes: currentNode && hasCanvasData ? (inDrill ? getNextNodes(currentNode.id) : getCanvasNextNodes(currentNode.id)) : [],
      waypointIds: new Set(waypoints.map((w) => w.id)),
      selectedNodeId: hasCanvasData ? currentNodeId : '',
      subGraphNodeIds,
      refNodeIds,
    },
    { onNodeClick: handleNodeClick },
  )

  const handleClear = () => {
    clearWaypoints()
    toast('已清空途径点')
  }

  const handleFreeBrowse = () => {
    if (waypoints.length === 0) return
    const startNode = waypoints[0]
    setCurrentNode(startNode.id)
    enterFreeBrowse(startNode)
    switchView('free-browse')
  }

  const handleDrillIn = () => {
    if (!currentNode) return
    const config = currentNode.subgraph_config
    const targetId = config?.target_graph_id || currentNode.sub_graph_id
    const entryId = config?.target_entry_node || currentNode.entry_node_id
    if (!targetId || !entryId) return

    const currentSelected = useNavStore.getState().selectedGraphIds
    if (currentSelected.length > 0) {
      useDrillStore.getState().setSnapshot(currentSelected)
    }

    drillIn(targetId, entryId, currentNode.id, currentNode.label)
    setCurrentNode(entryId)
    toast(`已钻入「${currentNode.label}」`)
  }

  const handleDrillOut = () => {
    const popped = useGraphStore.getState().drillOut()
    if (popped) {
      setCurrentNode(popped.parentNodeId)

      const snapshot = useDrillStore.getState().snapshotSelectedGraphIds
      if (snapshot.length > 0) {
        useNavStore.getState().setSelectedGraphs(snapshot)
        useDrillStore.getState().setSnapshot([])
      }

      toast(`已钻出，回到「${popped.parentNodeLabel}」`)
    }
  }

  const handleGoPlan = () => {
    if (waypoints.length < 2) {
      toast('至少需要 2 个途经点才能规划路线')
      return
    }
    const weightMode = waypoints[0]?.priority_config?.mode ?? 'mixed'
    generatePlans(waypoints, weightMode)
    switchView('plan')
  }

  return (
    <div className={styles.view}>
      <div className={styles.header}>
        <h2 className={styles.title}>认知导航</h2>
        {currentNode && hasCanvasData && (
          <p className={styles.subtitle}>
            当前节点: {currentNode.label}
          </p>
        )}
      </div>

      {/* 面包屑导航 */}
      <BreadcrumbNav items={breadcrumbItems} onSelect={() => {}} />

      <NavModeToggle mode={mode} onChange={setMode} />

      {!inDrill && <GraphMultiSelect />}

      <div className={styles.canvasWrap}>
        {!hasCanvasData && (
          <div className={styles.emptyCanvas}>
            <span>请在上方选择要加载的导航图</span>
          </div>
        )}
        <NavCanvas ref={canvasRef} />
        <ZoomControls onIn={zoomIn} onOut={zoomOut} onReset={zoomReset} />
        <DropDownPanel />
      </div>

      <WaypointsBar
        waypoints={waypoints}
        onRemove={removeWaypoint}
        onQuickConnect={handleQuickConnect}
        onEditConnection={(fromId, toId) => setEditingConn({ fromId, toId })}
      />

      <div className={styles.actions}>
        <Button variant="outline" size="sm" onClick={handleClear} disabled={waypoints.length === 0}>
          清空途径点
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={handleFillAll}
          disabled={waypoints.length < 2}
        >
          补齐连接
        </Button>
        {(currentNode?.subgraph_config?.target_graph_id || currentNode?.sub_graph_id) && (
          <Button variant="primary" size="sm" onClick={handleDrillIn}>
            钻入「{currentNode.label}」
          </Button>
        )}
        {inDrill && (
          <Button variant="outline" size="sm" onClick={handleDrillOut}>
            钻出
          </Button>
        )}
        {waypoints.length === 1 && (
          <Button variant="primary" size="sm" onClick={handleFreeBrowse}>
            自由分支浏览
          </Button>
        )}
        <Button
          variant="primary"
          size="sm"
          onClick={handleGoPlan}
          disabled={waypoints.length === 0}
        >
          规划路线 ({waypoints.length} 站)
        </Button>
      </div>

      {editingConn &&
        (() => {
          const { status, ref } = getConnectionStatus(editingConn.fromId, editingConn.toId)
          const fromNode = getNavNode(editingConn.fromId)
          const toNode = getNavNode(editingConn.toId)
          if (status !== 'connected' || !ref || !fromNode || !toNode) return null
          return (
            <ConnectionEditPopover
              fromId={editingConn.fromId}
              toId={editingConn.toId}
              fromLabel={fromNode.label}
              toLabel={toNode.label}
              initialRef={ref}
              onSave={(f, t, updates) => {
                updateQuickConnection(f, t, updates)
                toast('已更新跳转连接')
              }}
              onDelete={(f, t) => {
                removeQuickConnection(f, t)
                toast('已删除跳转连接')
              }}
              onClose={() => setEditingConn(null)}
            />
          )
        })()}
    </div>
  )
}

export default NavView
