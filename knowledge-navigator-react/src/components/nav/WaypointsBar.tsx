import React from 'react'
import type { NavNode } from '../../data/types'
import WaypointChip from './WaypointChip'
import styles from './WaypointsBar.module.css'

interface WaypointsBarProps {
  waypoints: NavNode[]
  onRemove: (index: number) => void
}

const WaypointsBar: React.FC<WaypointsBarProps> = ({ waypoints, onRemove }) => (
  <div className={styles.bar}>
    <span className={styles.label}>途径点</span>
    <div className={styles.track}>
      {waypoints.length === 0 ? (
        <span className={styles.empty}>点击画布中的节点，在下拉面板中添加途径点</span>
      ) : (
        waypoints.map((wp, i) => (
          <WaypointChip key={`${wp.id}-${i}`} index={i} node={wp} onRemove={() => onRemove(i)} />
        ))
      )}
    </div>
  </div>
)

export default WaypointsBar
