import React, { useState, useMemo } from 'react'
import styles from './GraphMultiSelect.module.css'
import { useGraphStore } from '../../store/graphStore'
import { useNavStore } from '../../store/navStore'
import { useDrillStore } from '../../store/drillStore'

const GraphMultiSelect: React.FC = () => {
  const graphs = useGraphStore((s) => s.graphs)
  const selectedGraphIds = useNavStore((s) => s.selectedGraphIds)
  const setSelectedGraphs = useNavStore((s) => s.setSelectedGraphs)
  const drillStack = useDrillStore((s) => s.stack)

  const inDrill = drillStack.length > 0
  const [collapsed, setCollapsed] = useState(true)

  const allIds = useMemo(() => graphs.map((g) => g.graph_id), [graphs])
  const isAllSelected = selectedGraphIds.length > 0 && selectedGraphIds.length === allIds.length

  const handleToggleAll = () => {
    if (isAllSelected) {
      setSelectedGraphs([])
    } else {
      setSelectedGraphs([...allIds])
    }
  }

  const handleToggle = (id: string) => {
    if (selectedGraphIds.includes(id)) {
      setSelectedGraphs(selectedGraphIds.filter((x) => x !== id))
    } else {
      setSelectedGraphs([...selectedGraphIds, id])
    }
  }

  if (inDrill || graphs.length <= 1) return null

  return (
    <div className={`${styles.wrapper} ${collapsed ? styles.collapsed : ''}`}>
      <button className={styles.header} onClick={() => setCollapsed(!collapsed)}>
        <span className={styles.title}>
          <span className={styles.arrow}>{collapsed ? '▸' : '▾'}</span>
          画布图加载
        </span>
        <span className={styles.stats}>
          已选 {selectedGraphIds.length}/{allIds.length} 图
        </span>
      </button>
      {!collapsed && (
        <div className={styles.list}>
          <label className={`${styles.item} ${styles.allItem}`}>
            <input
              type="checkbox"
              className={styles.checkbox}
              checked={isAllSelected}
              onChange={handleToggleAll}
            />
            <span className={styles.label}>全选</span>
          </label>
          <div className={styles.divider} />
          {graphs.map((g) => (
            <label key={g.graph_id} className={styles.item}>
              <input
                type="checkbox"
                className={styles.checkbox}
                checked={selectedGraphIds.includes(g.graph_id)}
                onChange={() => handleToggle(g.graph_id)}
              />
              <span className={styles.label}>
                {g.graph_id} {g.label}
              </span>
              <span className={styles.count}>{g.node_count} 节点</span>
            </label>
          ))}
        </div>
      )}
    </div>
  )
}

export default GraphMultiSelect
