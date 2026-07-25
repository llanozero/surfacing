import React from 'react'
import { useViewStore, type ViewName } from '../../store/viewStore'
import styles from './TabBar.module.css'

interface TabDef {
  name: ViewName
  label: string
  icon: React.FC<{ size?: number; className?: string }>
}

const SearchIcon: React.FC<{ size?: number; className?: string }> = ({ size = 20, className }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <circle cx="11" cy="11" r="8" /><path d="m21 21-4.3-4.3" />
  </svg>
)

const RouteIcon: React.FC<{ size?: number; className?: string }> = ({ size = 20, className }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <circle cx="6" cy="19" r="3" /><circle cx="18" cy="5" r="3" /><circle cx="18" cy="19" r="3" /><path d="M8 18a7 7 0 0 0 7-7h4" />
  </svg>
)

const PlayIcon: React.FC<{ size?: number; className?: string }> = ({ size = 20, className }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <polygon points="6 3 20 12 6 21 6 3" />
  </svg>
)

const PlanIcon: React.FC<{ size?: number; className?: string }> = ({ size = 20, className }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <polygon points="3 11 22 2 13 21 11 13 3 11" />
  </svg>
)

const FolderTreeIcon: React.FC<{ size?: number; className?: string }> = ({ size = 20, className }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M20 10a2 2 0 0 0-2-2H8" /><path d="M20 14a2 2 0 0 1-2 2H8" /><path d="M12 2v20" /><path d="M4 6h6" /><path d="M4 18h6" />
  </svg>
)

const tabs: TabDef[] = [
  { name: 'search', label: '搜索', icon: SearchIcon },
  { name: 'nav', label: '导航', icon: RouteIcon },
  { name: 'plan', label: '规划', icon: PlanIcon },
  { name: 'browse', label: '浏览', icon: PlayIcon },
  { name: 'tree', label: '管理', icon: FolderTreeIcon },
]

const TabBar: React.FC = () => {
  const { activeView, switchView } = useViewStore()

  return (
    <nav className={styles.bar}>
      {tabs.map((tab) => {
        const isActive = activeView === tab.name
        const Icon = tab.icon
        return (
          <button
            key={tab.name}
            className={`${styles.tab} ${isActive ? styles.active : ''}`}
            onClick={() => switchView(tab.name)}
            aria-label={tab.label}
          >
            <Icon size={20} className={styles.icon} />
            <span className={styles.label}>{tab.label}</span>
          </button>
        )
      })}
    </nav>
  )
}

export default TabBar
