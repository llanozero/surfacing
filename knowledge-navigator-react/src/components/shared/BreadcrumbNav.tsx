import React from 'react'
import styles from './BreadcrumbNav.module.css'

interface BreadcrumbNavProps {
  items: { path: string; label: string }[]
  onSelect: (path: string) => void
}

const BreadcrumbNav: React.FC<BreadcrumbNavProps> = ({ items, onSelect }) => (
  <nav className={styles.nav}>
    {items.map((item, i) => (
      <React.Fragment key={item.path}>
        {i > 0 && <span className={styles.sep}>/</span>}
        <button
          className={`${styles.item} ${i === items.length - 1 ? styles.current : ''}`}
          onClick={() => onSelect(item.path)}
        >
          {item.label}
        </button>
      </React.Fragment>
    ))}
  </nav>
)

export default BreadcrumbNav
