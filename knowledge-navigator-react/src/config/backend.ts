/**
 * 后端模式配置（backend-architecture.md §二）。
 * lite 模式（轻量）：纯前端操作，不依赖后端服务；
 * pro 模式（完整）：通过 HTTP 请求调用 Python FastAPI 后端完成全部数据操作。
 * 优先级：URL 参数 > localStorage > 默认值。
 * Node（CLI）环境下无 localStorage / window，自动降级为默认 pro 模式。
 */

export type BackendMode = 'lite' | 'pro'

export interface BackendConfig {
  /** 当前运行模式 */
  mode: BackendMode
  /** 后端的基础 URL（仅 pro 模式需要） */
  baseUrl: string
  /** 请求超时时间（毫秒） */
  timeout: number
  /** 请求重试次数 */
  retryCount: number
}

export const defaultBackendConfig: BackendConfig = {
  mode: 'pro',
  baseUrl: 'http://localhost:8171',
  timeout: 10000,
  retryCount: 1,
}

const STORAGE_KEY = 'kn_backend_config'

const hasLocalStorage = typeof localStorage !== 'undefined'
const hasWindow = typeof window !== 'undefined'

let _config: BackendConfig = { ...defaultBackendConfig }

export function getBackendConfig(): BackendConfig {
  return { ..._config }
}

export function setBackendConfig(partial: Partial<BackendConfig>): void {
  _config = { ..._config, ...partial }
  if (hasLocalStorage) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(_config))
    } catch {
      /* 存储不可用时忽略 */
    }
  }
}

export function isProMode(): boolean {
  return _config.mode === 'pro'
}

/** 初始化配置：localStorage 恢复 → URL 参数覆盖（最高优先级） */
export function initBackendConfig(): void {
  if (hasLocalStorage) {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      try {
        const parsed = JSON.parse(saved) as Partial<BackendConfig>
        if (parsed.mode === 'lite' || parsed.mode === 'pro') {
          _config = { ..._config, ...parsed }
        }
      } catch {
        /* 忽略损坏的存档 */
      }
    }
  }

  if (hasWindow) {
    const params = new URLSearchParams(window.location.search)
    const modeParam = params.get('backend_mode')
    if (modeParam === 'lite' || modeParam === 'pro') {
      _config.mode = modeParam
    }
    const baseUrl = params.get('backend_url')
    if (baseUrl) {
      _config.baseUrl = baseUrl
    }
  }

  // Node（CLI）环境：环境变量 KN_BACKEND_MODE / KN_BACKEND_URL（最高优先级）
  if (typeof process !== 'undefined' && process.env) {
    const envMode = process.env.KN_BACKEND_MODE
    if (envMode === 'lite' || envMode === 'pro') {
      _config.mode = envMode
    }
    const envUrl = process.env.KN_BACKEND_URL
    if (envUrl) {
      _config.baseUrl = envUrl
    }
  }
}
