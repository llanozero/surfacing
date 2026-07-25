import React from 'react'
import styles from './ModeToggle.module.css'
import type { MatchMode } from '../../store/searchStore'

interface ModeToggleProps {
  mode: MatchMode
  onChange: (mode: MatchMode) => void
}

const ModeToggle: React.FC<ModeToggleProps> = ({ mode, onChange }) => (
  <div className={styles.toggle} role="tablist" aria-label="匹配模式">
    <button
      role="tab"
      aria-selected={mode === 'keyword'}
      className={`${styles.btn} ${mode === 'keyword' ? styles.active : ''}`}
      onClick={() => onChange('keyword')}
    >
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
        <circle cx="11" cy="11" r="8" /><path d="m21 21-4.3-4.3" />
      </svg>
      关键词匹配
    </button>
    <button
      role="tab"
      aria-selected={mode === 'vector'}
      className={`${styles.btn} ${mode === 'vector' ? styles.activeVector : ''}`}
      onClick={() => onChange('vector')}
    >
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 2a4 4 0 0 1 4 4c2.5.5 4 2.5 4 5a6 6 0 0 1-3 5.2V18a3 3 0 0 1-3 3h-4a3 3 0 0 1-3-3v-1.8A6 6 0 0 1 4 11c0-2.5 1.5-4.5 4-5a4 4 0 0 1 4-4z" />
      </svg>
      向量模型匹配
    </button>
  </div>
)

export default ModeToggle
