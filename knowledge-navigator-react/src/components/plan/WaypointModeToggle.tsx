import React from 'react'
import styles from './WaypointModeToggle.module.css'
import type { WaypointMode } from '../../utils/routePlanner'

interface WaypointModeToggleProps {
  mode: WaypointMode
  onChange: (mode: WaypointMode) => void
}

const WaypointModeToggle: React.FC<WaypointModeToggleProps> = ({ mode, onChange }) => (
  <div className={styles.wrap}>
    <span className={styles.caption}>途经点排序</span>
    <div className={styles.toggle} role="tablist" aria-label="途经点排序模式">
      <button
        role="tab"
        aria-selected={mode === 'ordered'}
        className={`${styles.btn} ${mode === 'ordered' ? styles.active : ''}`}
        onClick={() => onChange('ordered')}
      >
        有序
        <span className={styles.sub}>保持添加顺序</span>
      </button>
      <button
        role="tab"
        aria-selected={mode === 'unordered'}
        className={`${styles.btn} ${mode === 'unordered' ? styles.active : ''}`}
        onClick={() => onChange('unordered')}
      >
        无序
        <span className={styles.sub}>算法自由重排</span>
      </button>
    </div>
  </div>
)

export default WaypointModeToggle
