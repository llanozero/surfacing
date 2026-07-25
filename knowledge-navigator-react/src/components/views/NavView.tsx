import React, { useRef, useState } from 'react'
import styles from './NavView.module.css'
import Button from '../shared/Button'
import NavCanvas from '../canvas/NavCanvas'
import ZoomControls from '../canvas/ZoomControls'
import NavModeToggle from '../nav/NavModeToggle'
import WaypointsBar from '../nav/WaypointsBar'
import ConnectionEditPopover from '../nav/ConnectionEditPopover'
import DropDownPanel from '../panel/DropDownPanel'
import { useNavStore, getCurrentNode } from '../../store/navStore'
import { usePanelStore } from '../../store/panelStore'
import { usePlanStore } from '../../store/planStore'
import { useViewStore } from '../../store/viewStore'
import { useToastStore } from '../shared/Toast'
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
  const selectedNodeId = useNavStore((s) => s.selectedNodeId)
  const allNavNodes = useNavStore((s) => s.allNavNodes)
  const allEdges = useNavStore((s) => s.allEdges)
  const waypoints = useNavStore((s) => s.waypoints)
  const setMode = useNavStore((s) => s.setMode)
  const setCurrentNode = useNavStore((s) => s.setCurrentNode)
  const setSelectedNode = useNavStore((s) => s.setSelectedNode)
  const getNextNodes = useNavStore((s) => s.getNextNodes)
  const getPrevNodes = useNavStore((s) => s.getPrevNodes)
  const removeWaypoint = useNavStore((s) => s.removeWaypoint)
  const clearWaypoints = useNavStore((s) => s.clearWaypoints)

  const setPanelNode = usePanelStore((s) => s.setNode)
  const generatePlans = usePlanStore((s) => s.generatePlans)
  const switchView = useViewStore((s) => s.switchView)
  const toast = useToastStore((s) => s.show)

  const currentNode = getCurrentNode({ currentNodeId })

  /** 正在编辑的连接（✅ 指示器点击后弹出浮层） */
  const [editingConn, setEditingConn] = useState<{ fromId: string; toId: string } | null>(null)

  /** QC-02：一键新建连接（预设优先级 #1，类型 user_added） */
  const handleQuickConnect = (fromId: string, toId: string) => {
    const created = ensureQuickConnection(fromId, toId)
    toast(created ? '已建立跳转连接' : '连接已存在')
  }

  /** QC-07：批量补齐所有缺失连接 */
  const handleFillAll = () => {
    const count = fillAllMissingConnections(waypoints)
    toast(count > 0 ? `已建立 ${count} 条跳转连接` : '所有相邻途经点均已连接')
  }

  // 点击分流（spec §4.2）：逐站模式切换中心节点；全览模式更新选中高亮
  const handleNodeClick = (node: NavNode) => {
    setPanelNode(node)
    if (mode === 'station') {
      setCurrentNode(node.id)
    } else {
      setSelectedNode(node.id)
    }
  }

  const { zoomIn, zoomOut, zoomReset } = useNavCanvas(
    canvasRef,
    mode,
    {
      allNodes: allNavNodes,
      allEdges,
      currentNode,
      prevNodes: currentNode ? getPrevNodes(currentNode.id) : [],
      nextNodes: currentNode ? getNextNodes(currentNode.id) : [],
      waypointIds: new Set(waypoints.map((w) => w.id)),
      selectedNodeId,
    },
    { onNodeClick: handleNodeClick },
  )

  const handleClear = () => {
    clearWaypoints()
    toast('已清空途径点')
  }

  // NavView → PlanView（spec §4.4）：途经点 ≥ 2 时进入路线规划
  const handleGoPlan = () => {
    if (waypoints.length < 2) {
      toast('至少需要 2 个途经点才能规划路线')
      return
    }
    // 权重模式取第一个途经点的 priority_config.mode，缺省 mixed
    const weightMode = waypoints[0]?.priority_config?.mode ?? 'mixed'
    generatePlans(waypoints, weightMode)
    switchView('plan')
  }

  return (
    <div className={styles.view}>
      <div className={styles.header}>
        <h2 className={styles.title}>认知导航</h2>
        <p className={styles.subtitle}>
          当前节点: {currentNode?.label ?? '—'}
        </p>
      </div>

      <NavModeToggle mode={mode} onChange={setMode} />

      <div className={styles.canvasWrap}>
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
        <Button
          variant="primary"
          size="sm"
          onClick={handleGoPlan}
          disabled={waypoints.length === 0}
        >
          规划路线 ({waypoints.length} 站)
        </Button>
      </div>

      {/* 连接编辑浮层（QC-03 / QC-04） */}
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
