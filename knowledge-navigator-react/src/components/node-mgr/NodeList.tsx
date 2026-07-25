import React from 'react'
import SearchBar from '../shared/SearchBar'
import { useNavNodeStore, filterNodes } from '../../store/navNodeStore'
import { useToastStore } from '../shared/Toast'
import styles from './NodeMgr.module.css'

/** 左侧节点列表（NM-02 搜索过滤 / NM-03 选中 / 新建节点） */
const NodeList: React.FC = () => {
  const { allNodes, searchQuery, selectedNodeId, setSearchQuery, selectNode, createNavNode } =
    useNavNodeStore()
  const toast = useToastStore((s) => s.show)
  const filtered = filterNodes(allNodes, searchQuery)

  const handleCreate = () => {
    const node = createNavNode()
    toast(`已新建节点 ${node.id}`)
  }

  return (
    <div className={styles.listPanel}>
      <SearchBar placeholder="搜索导航节点..." value={searchQuery} onChange={setSearchQuery} />
      <button className={styles.addBtn} onClick={handleCreate}>
        + 新建节点
      </button>
      <div className={styles.list}>
        {filtered.length > 0 ? (
          filtered.map((node) => (
            <button
              key={node.id}
              className={`${styles.listItem} ${node.id === selectedNodeId ? styles.listItemSelected : ''}`}
              onClick={() => selectNode(node.id)}
            >
              <span className={styles.listDot} />
              <span className={styles.listLabel}>{node.label}</span>
              <span className={styles.listMeta}>{node.next_nodes.length} 出口</span>
            </button>
          ))
        ) : (
          <p className={styles.listEmpty}>
            {allNodes.length === 0 ? '暂无导航节点' : '未找到匹配的导航节点'}
          </p>
        )}
      </div>
    </div>
  )
}

export default NodeList
