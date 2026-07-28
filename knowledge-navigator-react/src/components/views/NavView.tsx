import React, { useRef, useState, useMemo } from 'react'
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
import { useNavStore, getCurrentNode } from '../../store/navStore'
import { useBrowseStore } from '../../store/browseStore'
import { usePanelStore } from '../../store/panelStore'
import { usePlanStore } from '../../store/planStore'
import { useViewStore } from '../../store/viewStore'
import { useToastStore } from '../shared/Toast'
import { useGraphStore } from '../../store/graphStore'
import { useDrillStore } from '../../store/drillStore'
import { useNavCanvas } from '../../hooks/useNavCanvas'
import {
  ensureQuickConnection,
  updateQuickConnection,
  removeQuickConnection,
  fillAllMissingConnections,
  getConnectionStatus,
} from '../../utils/quickConnectUtils'
import { getNavNode } from '../../data/allNavNodes'
import type { NavNode } from '../../data/types'

const NavView: React.FC = () => {
  const canvasRef = useRef<HTMLDivElement>(null)

  const mode = useNavStore((s) => s.mode)
  const currentNodeId = useNavStore((s) => s.currentNodeId)
  const allNavNodes = useNavStore((s) => s.allNavNodes)
  const allEdges = useNavStore((s) => s.allEdges)
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
  const hasCanvasData = inDrill || selectedGraphIds.length > 0

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

  /** 从 allNavNodes 中提取所有子图节点 id */
  const subGraphNodeIds = useMemo(() => {
    const ids = new Set<string>()
    for (const n of allNavNodes) {
      if (n.subgraph_config?.target_graph_id || n.sub_graph_id) ids.add(n.id)
    }
    return ids
  }, [allNavNodes])

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
    setPanelNode(node)
    setCurrentNode(node.id)
  }

  const { zoomIn, zoomOut, zoomReset } = useNavCanvas(
    canvasRef,
    mode,
    {
      allNodes: hasCanvasData ? allNavNodes : [],
      allEdges: hasCanvasData ? allEdges : [],
      currentNode: hasCanvasData ? currentNode : null,
      prevNodes: currentNode && hasCanvasData ? getPrevNodes(currentNode.id) : [],
      nextNodes: currentNode && hasCanvasData ? getNextNodes(currentNode.id) : [],
      waypointIds: new Set(waypoints.map((w) => w.id)),
      selectedNodeId: hasCanvasData ? currentNodeId : '',
      subGraphNodeIds,
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
