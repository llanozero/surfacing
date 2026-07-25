import React from 'react'
import type { NavNode } from '../../data/types'
import styles from './WaypointChip.module.css'

interface WaypointChipProps {
  index?: number
  node?: NavNode
  type?: 'node' | 'add'
  onRemove?: () => void
}

const WaypointChip: React.FC<WaypointChipProps> = ({ index, node, type = 'node', onRemove }) => {
  if (type === 'add') {
    return <span className={`${styles.chip} ${styles.addChip}`}>+ 添加</span>
  }
  return (
    <span className={styles.chip}>
      <span className={styles.index}>{(index ?? 0) + 1}</span>
      <span className={styles.label}>{node?.label}</span>
      <button
        className={styles.remove}
        onClick={(e) => {
          e.stopPropagation()
          onRemove?.()
        }}
        aria-label={`移除途径点 ${node?.label}`}
      >
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
          <path d="M18 6 6 18M6 6l12 12" />
        </svg>
      </button>
    </span>
  )
}

export default WaypointChip
