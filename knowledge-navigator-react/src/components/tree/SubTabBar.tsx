import React from 'react'
import styles from './SubTabBar.module.css'
import type { SubTab } from '../../store/navNodeStore'

interface SubTabBarProps {
  active: SubTab
  onChange: (tab: SubTab) => void
}

const SubTabBar: React.FC<SubTabBarProps> = ({ active, onChange }) => (
  <div className={styles.bar} role="tablist" aria-label="管理子视图">
    <button
      role="tab"
      aria-selected={active === 'cards'}
      className={`${styles.tab} ${active === 'cards' ? styles.active : ''}`}
      onClick={() => onChange('cards')}
    >
      认知卡片
    </button>
    <button
      role="tab"
      aria-selected={active === 'nodes'}
      className={`${styles.tab} ${active === 'nodes' ? styles.active : ''}`}
      onClick={() => onChange('nodes')}
    >
      导航节点
    </button>
  </div>
)

export default SubTabBar
