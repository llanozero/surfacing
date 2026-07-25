import React from 'react'
import styles from './ZoomControls.module.css'

interface ZoomControlsProps {
  onIn: () => void
  onOut: () => void
  onReset: () => void
}

const ZoomControls: React.FC<ZoomControlsProps> = ({ onIn, onOut, onReset }) => (
  <div className={styles.controls}>
    <button className={styles.btn} onClick={onIn} aria-label="放大">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
        <path d="M12 5v14M5 12h14" />
      </svg>
    </button>
    <button className={styles.btn} onClick={onOut} aria-label="缩小">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
        <path d="M5 12h14" />
      </svg>
    </button>
    <button className={styles.btn} onClick={onReset} aria-label="重置缩放">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
        <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" /><path d="M3 3v5h5" />
      </svg>
    </button>
  </div>
)

export default ZoomControls
