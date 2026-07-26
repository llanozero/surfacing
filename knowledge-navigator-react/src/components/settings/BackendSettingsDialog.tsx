import React, { useState } from 'react'
import { createPortal } from 'react-dom'
import { getBackendConfig, setBackendConfig, type BackendMode } from '../../config/backend'
import { hydrateFromBackend } from '../../api/syncFromBackend'
import { useToastStore } from '../shared/Toast'
import styles from './BackendSettingsDialog.module.css'

interface BackendSettingsDialogProps {
  onClose: () => void
}

type TestState = 'idle' | 'testing' | 'ok' | 'fail'

/**
 * 后端设置对话框（backend-architecture.md §二）。
 * 本地模式：前端内存操作；远程模式：请求 Python FastAPI 后端。
 * 保存后写入 localStorage（优先级低于 URL 参数）。
 */
const BackendSettingsDialog: React.FC<BackendSettingsDialogProps> = ({ onClose }) => {
  const initial = getBackendConfig()
  const [mode, setMode] = useState<BackendMode>(initial.mode)
  const [baseUrl, setBaseUrl] = useState(initial.baseUrl)
  const [testState, setTestState] = useState<TestState>('idle')
  const [testMessage, setTestMessage] = useState('')
  const toast = useToastStore((s) => s.show)

  /** 测试连接：请求 /api/health，5 秒超时 */
  const handleTest = async () => {
    const url = baseUrl.trim().replace(/\/+$/, '')
    if (!url) {
      setTestState('fail')
      setTestMessage('请先填写后端地址')
      return
    }
    setTestState('testing')
    setTestMessage('')
    try {
      const controller = new AbortController()
      const timer = setTimeout(() => controller.abort(), 5000)
      const res = await fetch(`${url}/api/health`, { signal: controller.signal })
      clearTimeout(timer)
      if (res.ok) {
        setTestState('ok')
        setTestMessage('连接成功，后端服务正常')
      } else {
        setTestState('fail')
        setTestMessage(`后端返回 HTTP ${res.status}`)
      }
    } catch {
      setTestState('fail')
      setTestMessage('无法连接到后端服务，请检查地址与网络')
    }
  }

  const handleSave = () => {
    const url = baseUrl.trim().replace(/\/+$/, '')
    setBackendConfig({ mode, baseUrl: url || initial.baseUrl })
    toast(mode === 'remote' ? `已切换为远程模式（${url || initial.baseUrl}）` : '已切换为本地模式')
    onClose()
    // 切换到远程模式后立即从后端水合数据，无需刷新页面
    if (mode === 'remote') void hydrateFromBackend()
  }

  return createPortal(
    <div className={styles.mask} onClick={onClose}>
      <div className={styles.dialog} role="dialog" aria-modal="true" onClick={(e) => e.stopPropagation()}>
        <h3 className={styles.title}>后端设置</h3>

        <div className={styles.body}>
          <div className={styles.modeGroup}>
            <label className={`${styles.modeOption} ${mode === 'local' ? styles.modeOptionActive : ''}`}>
              <input
                type="radio"
                name="backend-mode"
                checked={mode === 'local'}
                onChange={() => setMode('local')}
              />
              <span className={styles.modeText}>
                <span className={styles.modeName}>本地模式（默认）</span>
                <span className={styles.modeDesc}>数据保存在浏览器内存中，刷新后恢复为内置数据</span>
              </span>
            </label>
            <label className={`${styles.modeOption} ${mode === 'remote' ? styles.modeOptionActive : ''}`}>
              <input
                type="radio"
                name="backend-mode"
                checked={mode === 'remote'}
                onChange={() => setMode('remote')}
              />
              <span className={styles.modeText}>
                <span className={styles.modeName}>远程模式</span>
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
                value={baseUrl}
                disabled={mode === 'local'}
                placeholder="http://localhost:8171"
                onChange={(e) => {
                  setBaseUrl(e.target.value)
                  setTestState('idle')
                  setTestMessage('')
                }}
              />
              <button
                className={styles.testBtn}
                disabled={mode === 'local' || testState === 'testing'}
                onClick={handleTest}
              >
                {testState === 'testing' ? '测试中…' : '测试连接'}
              </button>
            </div>
            {testState === 'ok' && <span className={`${styles.testResult} ${styles.testOk}`}>✓ {testMessage}</span>}
            {testState === 'fail' && <span className={`${styles.testResult} ${styles.testFail}`}>✗ {testMessage}</span>}
          </div>

          <p className={styles.hint}>
            也可以通过 URL 参数临时切换：<code>?backend_mode=remote&backend_url=http://localhost:8171</code>
            （URL 参数优先级高于此处保存的设置）
          </p>
        </div>

        <div className={styles.actions}>
          <button className={styles.cancelBtn} onClick={onClose}>
            取消
          </button>
          <button className={styles.confirmBtn} onClick={handleSave}>
            保存设置
          </button>
        </div>
      </div>
    </div>,
    document.body,
  )
}

export default BackendSettingsDialog
