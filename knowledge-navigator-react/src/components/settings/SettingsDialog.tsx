import React, { useState, useEffect, useCallback } from 'react'
import { createPortal } from 'react-dom'
import styles from './SettingsDialog.module.css'
import { getTtsConfig, setTtsConfig, getDefaultTtsConfig } from '../../config/tts'
import { getBackendConfig, setBackendConfig, type BackendMode } from '../../config/backend'
import { playTts, stopTts } from '../../utils/ttsPlayer'
import { saveAllDraftsToBackend } from '../../store/navNodeStore'
import { useToastStore } from '../shared/Toast'

type TabId = 'backend' | 'tts' | 'sync'

interface VoiceItem {
  name: string
  friendly_name: string
  locale: string
  gender: string
}

interface SettingsDialogProps {
  /** 初始打开的 Tab，默认 'backend' */
  initialTab?: TabId
  onClose: () => void
}

const TABS: { id: TabId; label: string }[] = [
  { id: 'backend', label: '后端' },
  { id: 'tts', label: 'TTS' },
  { id: 'sync', label: '同步' },
]

const RATE_PRESETS = ['-50%', '-40%', '-30%', '-20%', '-10%', '+0%', '+10%', '+20%', '+30%', '+40%', '+50%', '+60%', '+70%', '+80%', '+90%', '+100%']
const PITCH_PRESETS = ['-20Hz', '-18Hz', '-16Hz', '-14Hz', '-12Hz', '-10Hz', '-8Hz', '-6Hz', '-4Hz', '-2Hz', '+0Hz', '+2Hz', '+4Hz', '+6Hz', '+8Hz', '+10Hz', '+12Hz', '+14Hz', '+16Hz', '+18Hz', '+20Hz']
const DEMO_TEXT = '你好，这是认知导航系统的语音朗读测试。'

type SyncState = 'idle' | 'syncing' | 'ok' | 'fail'

const SettingsDialog: React.FC<SettingsDialogProps> = ({ initialTab, onClose }) => {
  const toast = useToastStore((s) => s.show)

  // ── Tab ──
  const [activeTab, setActiveTab] = useState<TabId>(initialTab ?? 'backend')

  // ── 后端设置 ──
  const backendInit = getBackendConfig()
  const [beMode, setBeMode] = useState<BackendMode>(backendInit.mode)
  const [beUrl, setBeUrl] = useState(backendInit.baseUrl)
  const [beTestState, setBeTestState] = useState<'idle' | 'testing' | 'ok' | 'fail'>('idle')
  const [beTestMsg, setBeTestMsg] = useState('')

  // ── TTS 设置 ──
  const ttsInit = getTtsConfig()
  const [voices, setVoices] = useState<VoiceItem[]>([])
  const [voicesLoading, setVoicesLoading] = useState(true)
  const [ttsVoice, setTtsVoice] = useState(ttsInit.voice)
  const [ttsRate, setTtsRate] = useState(ttsInit.rate)
  const [ttsPitch, setTtsPitch] = useState(ttsInit.pitch)
  const [ttsPrewarm, setTtsPrewarm] = useState(ttsInit.prewarm)
  const [ttsTesting, setTtsTesting] = useState(false)
  const [ttsError, setTtsError] = useState('')

  useEffect(() => {
    const cfg = getBackendConfig()
    const voicesUrl = cfg.mode === 'pro' ? `${cfg.baseUrl}/api/tts/voices` : '/api/tts/voices'
    fetch(voicesUrl)
      .then((r) => r.json())
      .then((data) => setVoices(data.voices || []))
      .catch(() => setVoices([]))
      .finally(() => setVoicesLoading(false))
  }, [])

  // ── 同步设置 ──
  const [syncState, setSyncState] = useState<SyncState>('idle')
  const [syncMsg, setSyncMsg] = useState('')
  const [lastSyncTime, setLastSyncTime] = useState<string>('')

  const handleOverlay = useCallback((e: React.MouseEvent) => {
    if (e.target === e.currentTarget) onClose()
  }, [onClose])

  // ── 后端：测试连接 ──
  const handleBeTest = async () => {
    const url = beUrl.trim().replace(/\/+$/, '')
    if (!url) {
      setBeTestState('fail')
      setBeTestMsg('请先填写后端地址')
      return
    }
    setBeTestState('testing')
    setBeTestMsg('')
    try {
      const controller = new AbortController()
      const timer = setTimeout(() => controller.abort(), 5000)
      const res = await fetch(`${url}/api/health`, { signal: controller.signal })
      clearTimeout(timer)
      if (res.ok) {
        setBeTestState('ok')
        setBeTestMsg('连接成功，后端服务正常')
      } else {
        setBeTestState('fail')
        setBeTestMsg(`后端返回 HTTP ${res.status}`)
      }
    } catch {
      setBeTestState('fail')
      setBeTestMsg('无法连接到后端服务，请检查地址与网络')
    }
  }

  // ── 后端：保存 ──
  const handleBeSave = () => {
    const url = beUrl.trim().replace(/\/+$/, '')
    setBackendConfig({ mode: beMode, baseUrl: url || backendInit.baseUrl })
    toast(beMode === 'pro' ? `已切换为完整模式（${url || backendInit.baseUrl}）` : '已切换为轻量模式')
  }

  // ── TTS：试听 ──
  const handleTtsTest = async () => {
    stopTts()
    setTtsTesting(true)
    setTtsError('')
    try {
      await playTts(DEMO_TEXT, { voice: ttsVoice, rate: ttsRate, pitch: ttsPitch })
    } catch (e) {
      setTtsError(e instanceof Error ? e.message : '试听失败')
    } finally {
      setTtsTesting(false)
    }
  }

  // ── TTS：重置 ──
  const handleTtsReset = () => {
    const d = getDefaultTtsConfig()
    setTtsVoice(d.voice)
    setTtsRate(d.rate)
    setTtsPitch(d.pitch)
    setTtsPrewarm(d.prewarm)
  }

  // ── TTS：保存 ──
  const handleTtsSave = () => {
    setTtsConfig({ voice: ttsVoice, rate: ttsRate, pitch: ttsPitch, prewarm: ttsPrewarm })
    toast('TTS 设置已保存')
  }

  // ── 同步 ──
  const handleSync = async () => {
    const cfg = getBackendConfig()
    if (cfg.mode !== 'pro') {
      setSyncState('fail')
      setSyncMsg('当前为轻量模式，无需同步')
      return
    }
    setSyncState('syncing')
    setSyncMsg('')
    try {
      const nodeCount = await saveAllDraftsToBackend()
      const resp = await fetch(`${cfg.baseUrl}/api/graphs/sync-all`, { method: 'POST' })
      if (!resp.ok) throw new Error(`同步失败: ${resp.status}`)
      const data = await resp.json()
      const now = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
      setLastSyncTime(now)
      setSyncState('ok')
      setSyncMsg(`同步完成: ${nodeCount} 个节点 + ${data.saved_graphs} 个图已保存`)
    } catch (e) {
      setSyncState('fail')
      setSyncMsg('同步失败: ' + (e instanceof Error ? e.message : '网络错误'))
    }
  }

  const selectedVoice = voices.find((v) => v.name === ttsVoice)

  return createPortal(
    <div className={styles.overlay} onClick={handleOverlay}>
      <div className={styles.dialog} role="dialog" aria-modal="true" onClick={(e) => e.stopPropagation()}>
        {/* 标题栏 */}
        <div className={styles.header}>
          <h3 className={styles.title}>⚙ 设置</h3>
          <button className={styles.closeBtn} onClick={onClose}>✕</button>
        </div>

        {/* Tab 标签 */}
        <div className={styles.tabs}>
          {TABS.map((t) => (
            <button
              key={t.id}
              className={`${styles.tab} ${activeTab === t.id ? styles.tabActive : ''}`}
              onClick={() => setActiveTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* ── Tab 内容 ── */}
        <div className={styles.body}>

          {/* === 后端设置 === */}
          {activeTab === 'backend' && (
            <div className={styles.tabContent}>
              <div className={styles.modeGroup}>
                <label className={`${styles.modeOption} ${beMode === 'lite' ? styles.modeOptionActive : ''}`}>
                  <input
                    type="radio"
                    name="be-mode"
                    checked={beMode === 'lite'}
                    onChange={() => setBeMode('lite')}
                  />
                  <span className={styles.modeText}>
                    <span className={styles.modeName}>轻量模式（lite，默认）</span>
                    <span className={styles.modeDesc}>数据保存在浏览器内存中，刷新后恢复为内置数据</span>
                  </span>
                </label>
                <label className={`${styles.modeOption} ${beMode === 'pro' ? styles.modeOptionActive : ''}`}>
                  <input
                    type="radio"
                    name="be-mode"
                    checked={beMode === 'pro'}
                    onChange={() => setBeMode('pro')}
                  />
                  <span className={styles.modeText}>
                    <span className={styles.modeName}>完整模式（pro）</span>
                    <span className={styles.modeDesc}>连接 Python FastAPI 后端，数据持久化在服务端</span>
                  </span>
                </label>
              </div>

              <div className={styles.fieldGroup}>
                <span className={styles.fieldLabel}>后端地址</span>
                <div className={styles.urlRow}>
                  <input
                    className={styles.urlInput}
                    type="text"
                    value={beUrl}
                    disabled={beMode === 'lite'}
                    placeholder="http://localhost:8171"
                    onChange={(e) => {
                      setBeUrl(e.target.value)
                      setBeTestState('idle')
                      setBeTestMsg('')
                    }}
                  />
                  <button
                    className={styles.actionBtn}
                    disabled={beMode === 'lite' || beTestState === 'testing'}
                    onClick={handleBeTest}
                  >
                    {beTestState === 'testing' ? '测试中…' : '测试连接'}
                  </button>
                </div>
                {beTestState === 'ok' && <span className={styles.testOk}>✓ {beTestMsg}</span>}
                {beTestState === 'fail' && <span className={styles.testFail}>✗ {beTestMsg}</span>}
              </div>

              <p className={styles.hint}>
                也可以通过 URL 参数临时切换：<code>?backend_mode=pro&backend_url=http://localhost:8171</code>
              </p>

              <div className={styles.footer}>
                <button className={styles.saveBtn} onClick={handleBeSave}>保存设置</button>
              </div>
            </div>
          )}

          {/* === TTS 设置 === */}
          {activeTab === 'tts' && (
            <div className={styles.tabContent}>
              {/* 音色 */}
              <label className={styles.field}>
                <span className={styles.fieldLabel}>音色 (Voice)</span>
                <select
                  className={styles.select}
                  value={ttsVoice}
                  onChange={(e) => setTtsVoice(e.target.value)}
                  disabled={voicesLoading}
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
                <span className={styles.fieldLabel}>语速 (Rate): {ttsRate}</span>
                <input
                  type="range"
                  className={styles.slider}
                  min="0"
                  max={RATE_PRESETS.length - 1}
                  value={RATE_PRESETS.indexOf(ttsRate)}
                  onChange={(e) => setTtsRate(RATE_PRESETS[Number(e.target.value)])}
                />
                <span className={styles.rangeLabels}>
                  <span>-50%</span>
                  <span>+100%</span>
                </span>
              </label>

              {/* 音调 */}
              <label className={styles.field}>
                <span className={styles.fieldLabel}>音调 (Pitch): {ttsPitch}</span>
                <input
                  type="range"
                  className={styles.slider}
                  min="0"
                  max={PITCH_PRESETS.length - 1}
                  value={PITCH_PRESETS.indexOf(ttsPitch)}
                  onChange={(e) => setTtsPitch(PITCH_PRESETS[Number(e.target.value)])}
                />
                <span className={styles.rangeLabels}>
                  <span>-20Hz</span>
                  <span>+20Hz</span>
                </span>
              </label>

              {/* 预热开关 */}
              <div className={styles.prewarmSection}>
                <label className={styles.prewarmToggle}>
                  <span className={styles.prewarmLabel}>启用后台预热</span>
                  <input
                    type="checkbox"
                    className={styles.prewarmCheckbox}
                    checked={ttsPrewarm}
                    onChange={(e) => setTtsPrewarm(e.target.checked)}
                  />
                  <span className={styles.prewarmSwitch} />
                </label>
                <p className={styles.prewarmHint}>
                  首次加载导航图时自动预合成音频，减少等待时间
                </p>
              </div>

              {/* 试听 */}
              <button
                className={styles.testBtn}
                onClick={handleTtsTest}
                disabled={ttsTesting}
              >
                {ttsTesting ? '试听中...' : '🔊 试听'}
              </button>
              {ttsError && <p className={styles.error}>{ttsError}</p>}

              <div className={styles.footer}>
                <button className={styles.resetBtn} onClick={handleTtsReset}>重置默认</button>
                <button className={styles.saveBtn} onClick={handleTtsSave}>保存设置</button>
              </div>
            </div>
          )}

          {/* === 同步管理 === */}
          {activeTab === 'sync' && (
            <div className={styles.tabContent}>
              <div className={styles.syncInfo}>
                <p className={styles.syncDesc}>
                  将所有本地编辑的节点和认知卡片数据同步到后端 YAML 文件持久化。
                </p>
                {lastSyncTime && (
                  <p className={styles.syncLast}>
                    上次同步：{lastSyncTime}
                  </p>
                )}
              </div>

              <button
                className={styles.syncBtnLarge}
                onClick={handleSync}
                disabled={syncState === 'syncing'}
              >
                {syncState === 'syncing' ? '⏳ 同步中...' : '🔄 开始同步'}
              </button>

              {syncState === 'ok' && <span className={styles.testOk}>✓ {syncMsg}</span>}
              {syncState === 'fail' && <span className={styles.testFail}>✗ {syncMsg}</span>}
            </div>
          )}
        </div>

        {/* 底部关闭 */}
        <div className={styles.footerBar}>
          <button className={styles.cancelBtn} onClick={onClose}>关闭</button>
        </div>
      </div>
    </div>,
    document.body,
  )
}

export default SettingsDialog
