import React from 'react'
import type { NavNode } from '../../data/types'
import WaypointChip from './WaypointChip'
import ConnectionIndicator from './ConnectionIndicator'
import styles from './WaypointsBar.module.css'

interface WaypointsBarProps {
  waypoints: NavNode[]
  onRemove: (index: number) => void
  /** 是否显示相邻途经点之间的连接指示器（默认 true） */
  showConnections?: boolean
  /** 点击 ✚ 一键新建连接 */
  onQuickConnect?: (fromId: string, toId: string) => void
  /** 点击 ✅ 弹出连接编辑浮层 */
  onEditConnection?: (fromId: string, toId: string) => void
}

const WaypointsBar: React.FC<WaypointsBarProps> = ({
  waypoints,
  onRemove,
  showConnections = true,
  onQuickConnect,
  onEditConnection,
}) => (
  <div className={styles.bar}>
    <span className={styles.label}>途径点</span>
    <div className={styles.track}>
      {waypoints.length === 0 ? (
        <span className={styles.empty}>点击画布中的节点，在下拉面板中添加途径点</span>
      ) : (
        waypoints.map((wp, i) => (
          <React.Fragment key={`${wp.id}-${i}`}>
            <WaypointChip index={i} node={wp} onRemove={() => onRemove(i)} />
            {/* 相邻 Chip 之间的连接状态指示器 */}
            {i < waypoints.length - 1 && showConnections && (
              <ConnectionIndicator
                fromId={wp.id}
                toId={waypoints[i + 1].id}
                onConnect={onQuickConnect}
                onEdit={onEditConnection}
              />
            )}
          </React.Fragment>
        ))
      )}
    </div>
  </div>
)

export default WaypointsBar
