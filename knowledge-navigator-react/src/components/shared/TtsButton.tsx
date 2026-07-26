import React, { useState, useCallback } from 'react'
import styles from './TtsButton.module.css'
import { playTts, stopTts, isTtsPlaying } from '../../utils/ttsPlayer'
import { useToastStore } from './Toast'

interface TtsButtonProps {
  text: string
  size?: 'sm' | 'md'
}

const TtsButton: React.FC<TtsButtonProps> = ({ text, size = 'sm' }) => {
  const [playing, setPlaying] = useState(false)
  const toast = useToastStore((s) => s.show)

  const handleClick = useCallback(async (e: React.MouseEvent) => {
    e.stopPropagation()
    if (!text) return

    if (isTtsPlaying()) {
      stopTts()
      setPlaying(false)
      return
    }

    setPlaying(true)
    try {
      await playTts(text)
    } catch (err) {
      toast(err instanceof Error ? err.message : 'TTS 播放失败')
    } finally {
      setPlaying(false)
    }
  }, [text, toast])

  return (
    <button
      className={`${styles.btn} ${size === 'md' ? styles.md : styles.sm} ${playing ? styles.active : ''}`}
      onClick={handleClick}
      title={playing ? '停止' : '朗读'}
      disabled={!text}
    >
      {playing ? '⏹' : '🔊'}
    </button>
  )
}

export default TtsButton
