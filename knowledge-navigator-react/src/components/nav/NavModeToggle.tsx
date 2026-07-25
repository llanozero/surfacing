import React from 'react'
import styles from './NavModeToggle.module.css'
import type { NavMode } from '../../store/navStore'

interface NavModeToggleProps {
  mode: NavMode
  onChange: (mode: NavMode) => void
}

const NavModeToggle: React.FC<NavModeToggleProps> = ({ mode, onChange }) => (
  <div className={styles.toggle}>
    <button
      className={`${styles.btn} ${mode === 'overview' ? styles.active : ''}`}
      onClick={() => onChange('overview')}
    >
      全览
    </button>
    <button
      className={`${styles.btn} ${mode === 'station' ? styles.active : ''}`}
      onClick={() => onChange('station')}
    >
      逐站
    </button>
  </div>
)

export default NavModeToggle
