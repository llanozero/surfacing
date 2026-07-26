import React, { useState } from 'react'
import styles from './StatusBar.module.css'
import TtsSettingsDialog from '../settings/TtsSettingsDialog'

const StatusBar: React.FC = () => {
  const [time, setTime] = React.useState('')
  const [ttsOpen, setTtsOpen] = useState(false)

  React.useEffect(() => {
    const update = () => {
      const now = new Date()
      setTime(now.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }))
    }
    update()
    const id = setInterval(update, 60000)
    return () => clearInterval(id)
  }, [])

  return (
    <header className={styles.bar}>
      <span className={styles.time}>{time}</span>
      <span className={styles.title}>认知导航</span>
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
