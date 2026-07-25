import React from 'react'
import styles from './TreeList.module.css'
import TreeNode from '../tree/TreeNode'
import { useTreeStore } from '../../store/treeStore'
import { getRootNodes } from '../../utils/treeUtils'

const TreeList: React.FC = () => {
  const flatData = useTreeStore((s) => s.flatData)
  const roots = getRootNodes(flatData)

  return (
    <div className={styles.list}>
      {roots.map((n) => (
        <TreeNode key={n.id} node={n} level={0} />
      ))}
    </div>
  )
}

export default TreeList
