import React from 'react'
import type { TreeNodeData } from '../../data/types'
import { getTreeChildren } from '../../utils/treeUtils'
import { useTreeStore, nodeMatches } from '../../store/treeStore'
import TreeBadge from './TreeBadge'
import styles from './TreeNode.module.css'

interface TreeNodeProps {
  node: TreeNodeData
  level: number
}

/** 递归树节点：展开/折叠 + 选中 + 搜索过滤 */
const TreeNode: React.FC<TreeNodeProps> = ({ node, level }) => {
  const { flatData, selectedId, expandedIds, searchQuery, selectNode, toggleNode } = useTreeStore()

  if (!nodeMatches(flatData, node.id, searchQuery)) return null

  const isFolder = node.type === 'folder'
  const isExpanded = expandedIds.has(node.id)
  const isSelected = selectedId === node.id
  const children = isFolder ? getTreeChildren(flatData, node.id) : []
  const badgeType = node.tag === '决策分支' ? 'branch' : node.tag === '层级分类' ? 'hierarchy' : null

  return (
    <>
      <div
        className={`${styles.row} ${isSelected ? styles.selected : ''}`}
        style={{ paddingLeft: 12 + level * 18 }}
        onClick={() => selectNode(node.id)}
      >
        {isFolder ? (
          <button
            className={`${styles.toggle} ${isExpanded ? styles.expanded : ''}`}
            onClick={(e) => {
              e.stopPropagation()
              toggleNode(node.id)
            }}
            aria-label={isExpanded ? '折叠' : '展开'}
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="9 18 15 12 9 6" />
            </svg>
          </button>
        ) : (
          <span className={styles.togglePlaceholder} />
        )}

        <span className={isFolder ? styles.folderIcon : styles.leafIcon}>
          {isFolder ? (
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
            </svg>
          ) : (
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
              <polyline points="14 2 14 8 20 8" />
            </svg>
          )}
        </span>

        <span className={styles.title}>{node.title}</span>
        {badgeType && <TreeBadge type={badgeType} />}
        {isFolder && <span className={styles.count}>{children.length}</span>}
      </div>

      {isFolder && isExpanded && (
        <div className={styles.children}>
          {children.map((c) => (
            <TreeNode key={c.id} node={c} level={level + 1} />
          ))}
        </div>
      )}
    </>
  )
}

export default TreeNode
