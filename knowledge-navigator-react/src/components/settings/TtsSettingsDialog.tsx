import React, { useEffect, useState, useCallback } from 'react'
import styles from './TtsSettingsDialog.module.css'
import { getTtsConfig, setTtsConfig, getDefaultTtsConfig } from '../../config/tts'
import { playTts, stopTts } from '../../utils/ttsPlayer'
import { isRemoteMode } from '../../config/backend'

interface VoiceItem {
  name: string
  friendly_name: string
  locale: string
  gender: string
}

interface TtsSettingsDialogProps {
  onClose: () => void
}

const RATE_PRESETS = ['-50%', '-40%', '-30%', '-20%', '-10%', '+0%', '+10%', '+20%', '+30%', '+40%', '+50%', '+60%', '+70%', '+80%', '+90%', '+100%']
const PITCH_PRESETS = ['-20Hz', '-18Hz', '-16Hz', '-14Hz', '-12Hz', '-10Hz', '-8Hz', '-6Hz', '-4Hz', '-2Hz', '+0Hz', '+2Hz', '+4Hz', '+6Hz', '+8Hz', '+10Hz', '+12Hz', '+14Hz', '+16Hz', '+18Hz', '+20Hz']

const DEMO_TEXT = '你好，这是认知导航系统的语音朗读测试。'

const TtsSettingsDialog: React.FC<TtsSettingsDialogProps> = ({ onClose }) => {
  const [voices, setVoices] = useState<VoiceItem[]>([])
  const [loading, setLoading] = useState(true)
  const [voice, setVoice] = useState(getTtsConfig().voice)
  const [rate, setRate] = useState(getTtsConfig().rate)
  const [pitch, setPitch] = useState(getTtsConfig().pitch)
  const [testing, setTesting] = useState(false)
  const [error, setError] = useState('')

  const remoteMode = isRemoteMode()

  useEffect(() => {
    if (!remoteMode) {
      setLoading(false)
      return
    }
    fetch('/api/tts/voices')
      .then((r) => r.json())
      .then((data) => setVoices(data.voices || []))
      .catch(() => setVoices([]))
      .finally(() => setLoading(false))
  }, [remoteMode])

  const selectedVoice = voices.find((v) => v.name === voice)

  const handleSave = useCallback(() => {
    setTtsConfig({ voice, rate, pitch })
    onClose()
  }, [voice, rate, pitch, onClose])

  const handleReset = useCallback(() => {
    const d = getDefaultTtsConfig()
    setVoice(d.voice)
    setRate(d.rate)
    setPitch(d.pitch)
  }, [])

  const handleTest = useCallback(async () => {
    stopTts()
    setTesting(true)
    setError('')
    try {
      await playTts(DEMO_TEXT, { voice, rate, pitch })
    } catch (e) {
      setError(e instanceof Error ? e.message : '试听失败')
    } finally {
      setTesting(false)
    }
  }, [voice, rate, pitch])

  const handleOverlayClick = useCallback((e: React.MouseEvent) => {
    if (e.target === e.currentTarget) onClose()
  }, [onClose])

  return (
    <div className={styles.overlay} onClick={handleOverlayClick}>
      <div className={styles.dialog}>
        <div className={styles.header}>
          <h3 className={styles.title}>TTS 语音设置</h3>
          <button className={styles.closeBtn} onClick={onClose}>✕</button>
        </div>

        {!remoteMode ? (
          <p className={styles.hint}>TTS 需要后端支持，请先切换到远程模式。</p>
        ) : (
          <div className={styles.body}>
            {/* 音色 */}
            <label className={styles.field}>
              <span className={styles.fieldLabel}>音色 (Voice)</span>
              <select
                className={styles.select}
                value={voice}
                onChange={(e) => setVoice(e.target.value)}
                disabled={loading}
              >
                {voices.map((v) => (
                  <option key={v.name} value={v.name}>
                    {v.friendly_name} ({v.name})
                  </option>
                ))}
              </select>
              {selectedVoice && (
                <span className={styles.voiceInfo}>
                  {selectedVoice.gender === 'Female' ? '女声' : selectedVoice.gender === 'Male' ? '男声' : ''} · {selectedVoice.locale}
                </span>
              )}
            </label>

            {/* 语速 */}
            <label className={styles.field}>
              <span className={styles.fieldLabel}>语速 (Rate): {rate}</span>
              <input
                type="range"
                className={styles.slider}
                min="0"
                max={RATE_PRESETS.length - 1}
                value={RATE_PRESETS.indexOf(rate)}
                onChange={(e) => setRate(RATE_PRESETS[Number(e.target.value)])}
              />
              <span className={styles.rangeLabels}>
                <span>-50%</span>
                <span>+100%</span>
              </span>
            </label>

            {/* 音调 */}
            <label className={styles.field}>
              <span className={styles.fieldLabel}>音调 (Pitch): {pitch}</span>
              <input
                type="range"
                className={styles.slider}
                min="0"
                max={PITCH_PRESETS.length - 1}
                value={PITCH_PRESETS.indexOf(pitch)}
                onChange={(e) => setPitch(PITCH_PRESETS[Number(e.target.value)])}
              />
              <span className={styles.rangeLabels}>
                <span>-20Hz</span>
                <span>+20Hz</span>
              </span>
            </label>

            {/* 试听 */}
            <button
              className={styles.testBtn}
              onClick={handleTest}
              disabled={testing}
            >
              {testing ? '试听中...' : '🔊 试听'}
            </button>
            {error && <p className={styles.error}>{error}</p>}
          </div>
        )}

        <div className={styles.footer}>
          <button className={styles.resetBtn} onClick={handleReset}>重置默认</button>
          <div className={styles.footerRight}>
            <button className={styles.cancelBtn} onClick={onClose}>取消</button>
            <button className={styles.saveBtn} onClick={handleSave}>保存</button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default TtsSettingsDialog
