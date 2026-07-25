import React from 'react'
import styles from './SwipeHint.module.css'

interface SwipeHintProps {
  direction: 'up' | 'down'
}

const SwipeHint: React.FC<SwipeHintProps> = ({ direction }) => (
  <div className={`${styles.hint} ${direction === 'up' ? styles.up : styles.down}`}>
    <svg
      width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="2" strokeLinecap="round"
      style={{ transform: direction === 'down' ? 'rotate(180deg)' : 'none' }}
    >
      <polyline points="18 15 12 9 6 15" />
    </svg>
    <span>{direction === 'up' ? '上滑下一张' : '下滑上一张'}</span>
  </div>
)

export default SwipeHint
