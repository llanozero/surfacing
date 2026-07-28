import React, { useEffect, useMemo, useRef } from 'react'
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
  const hasInitialized = useRef(false)

  const allIds = useMemo(() => graphs.map((g) => g.graph_id), [graphs])

  useEffect(() => {
    if (graphs.length > 0 && selectedGraphIds.length === 0 && !hasInitialized.current) {
      hasInitialized.current = true
      setSelectedGraphs(allIds)
    }
  }, [graphs, selectedGraphIds, allIds, setSelectedGraphs])
  const isAllSelected = selectedGraphIds.length > 0 && selectedGraphIds.length === allIds.length

  const totalNodes = useMemo(() => {
    return graphs
      .filter((g) => selectedGraphIds.includes(g.graph_id))
      .reduce((sum, g) => sum + (g.node_count || 0), 0)
  }, [graphs, selectedGraphIds])

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
    <div className={styles.wrapper}>
      <div className={styles.header}>
        <span className={styles.title}>画布图加载</span>
        <span className={styles.stats}>
          已选: {selectedGraphIds.length}/{allIds.length} 图，共 {totalNodes} 节点
        </span>
      </div>
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
    </div>
  )
}

export default GraphMultiSelect
