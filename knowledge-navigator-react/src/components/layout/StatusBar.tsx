import React, { useState, useEffect } from 'react'
import styles from './StatusBar.module.css'
import SettingsDialog from '../settings/SettingsDialog'
import { useGraphStore } from '../../store/graphStore'

const StatusBar: React.FC = () => {
  const [time, setTime] = React.useState('')
  const [settingsOpen, setSettingsOpen] = useState(false)
  const { fetchGraphList } = useGraphStore()

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

  return (
    <header className={styles.bar}>
      <span className={styles.time}>{time}</span>
      <span className={styles.title}>认知导航</span>
      <span className={styles.spacer} />
      <button
        className={styles.ttsBtn}
        onClick={() => setSettingsOpen(true)}
        title="设置"
      >
        ⚙
      </button>
      {settingsOpen && <SettingsDialog onClose={() => setSettingsOpen(false)} />}
    </header>
  )
}

export default StatusBar
