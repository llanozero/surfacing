import React from 'react'
import styles from './TreeBadge.module.css'

interface TreeBadgeProps {
  type: 'branch' | 'hierarchy'
}

const TreeBadge: React.FC<TreeBadgeProps> = ({ type }) => (
  <span className={`${styles.badge} ${type === 'branch' ? styles.branch : styles.hierarchy}`}>
    {type === 'branch' ? '决策分支' : '层级分类'}
  </span>
)

export default TreeBadge
