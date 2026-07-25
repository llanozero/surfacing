import React from 'react'
import type { NavNode } from '../../data/types'
import styles from './BoundNodeItem.module.css'

interface BoundNodeItemProps {
  node: NavNode
  isSelected: boolean
  onClick: () => void
}

const BoundNodeItem: React.FC<BoundNodeItemProps> = ({ node, isSelected, onClick }) => (
  <button className={`${styles.item} ${isSelected ? styles.selected : ''}`} onClick={onClick}>
    <span className={styles.dot} />
    <span className={styles.body}>
      <span className={styles.label}>{node.label}</span>
      <span className={styles.desc}>{node.description}</span>
    </span>
    <span className={styles.meta}>{node.next_nodes.length} 个出口</span>
  </button>
)

export default BoundNodeItem
