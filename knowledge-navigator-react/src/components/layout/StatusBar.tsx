import React, { useState, useEffect } from 'react'
import styles from './StatusBar.module.css'
import TtsSettingsDialog from '../settings/TtsSettingsDialog'
import { useGraphStore } from '../../store/graphStore'
import { useDrillStore } from '../../store/drillStore'
import { useNavStore } from '../../store/navStore'

const StatusBar: React.FC = () => {
  const [time, setTime] = React.useState('')
  const [ttsOpen, setTtsOpen] = useState(false)
  const { graphs, activeGraphId, fetchGraphList, drillOut } = useGraphStore()
  const { stack, buildBreadcrumb } = useDrillStore()
  const currentNodeId = useNavStore((s) => s.currentNodeId)

  React.useEffect(() => {
    const update = () => {
      const now = new Date()
      setTime(now.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }))
    }
    update()
    const id = setInterval(update, 60000)
    return () => clearInterval(id)
  }, [])

  useEffect(() => {
    fetchGraphList()
  }, [])  // eslint-disable-line react-hooks/exhaustive-deps

  const handleDrillOut = () => {
    const popped = drillOut()
    if (popped) {
      useNavStore.getState().setCurrentNode(popped.parentNodeId)

      const { snapshotSelectedGraphIds } = useDrillStore.getState()
      if (snapshotSelectedGraphIds.length > 0) {
        useNavStore.getState().setSelectedGraphs(snapshotSelectedGraphIds)
        useDrillStore.getState().setSnapshot([])
      }
    }
  }

  /** 是否处于钻入状态 */
  const inDrill = stack.length > 0

  /** 构建面包屑：top 层始终存在 */
  const activeMeta = graphs.find((g) => g.graph_id === activeGraphId)
  const currentGraphLabel = activeMeta?.label ?? activeGraphId
  const breadcrumb = inDrill
    ? buildBreadcrumb(activeGraphId, currentGraphLabel, currentNodeId, '')
    : [{ graphId: 'top', graphLabel: 'top', nodeId: '', nodeLabel: '' }]

  return (
    <header className={styles.bar}>
      <span className={styles.time}>{time}</span>
      <span className={styles.title}>认知导航</span>
      <span className={styles.spacer} />
      {breadcrumb.length > 0 && (
        <div className={styles.breadcrumb}>
          {breadcrumb.map((step, i) => (
            <React.Fragment key={`${step.graphId}-${step.nodeId || i}`}>
              {i > 0 && <span className={styles.breadcrumbSep}>/</span>}
              <span className={`${styles.breadcrumbItem} ${step.graphId === 'top' ? styles.breadcrumbTop : ''}`}>
                {step.nodeLabel ? `${step.nodeLabel}` : step.graphLabel || step.graphId}
              </span>
            </React.Fragment>
          ))}
          {inDrill && (
            <button className={styles.drillOutBtn} onClick={handleDrillOut} title="钻出子图">
              ↩
            </button>
          )}
        </div>
      )}
      <span className={styles.spacer} />
      <button
        className={styles.ttsBtn}
        onClick={() => setTtsOpen(true)}
        title="TTS 语音设置"
      >
        ⚙
      </button>
      {ttsOpen && <TtsSettingsDialog onClose={() => setTtsOpen(false)} />}
    </header>
  )
}

export default StatusBar
