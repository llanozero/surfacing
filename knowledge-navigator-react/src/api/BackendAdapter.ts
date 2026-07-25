import { getBackendConfig } from '../config/backend'

/**
 * HTTP 请求适配器（backend-architecture.md §3.2）。
 * 封装 GET/POST/PUT/DELETE，统一超时与重试（默认 10s 超时 + 1 次重试）。
 */

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export class BackendAdapter {
  private static instance: BackendAdapter

  static getInstance(): BackendAdapter {
    if (!this.instance) {
      this.instance = new BackendAdapter()
    }
    return this.instance
  }

  private get baseUrl(): string {
    return getBackendConfig().baseUrl
  }

  private get timeout(): number {
    return getBackendConfig().timeout
  }

  private get retryCount(): number {
    return getBackendConfig().retryCount
  }

  /** 单次请求（带超时） */
  private async requestOnce<T>(method: string, path: string, body?: unknown): Promise<T> {
    const url = `${this.baseUrl}${path}`
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), this.timeout)

    try {
      const resp = await fetch(url, {
        method,
        signal: controller.signal,
        headers: {
          Accept: 'application/json',
          ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
        },
        ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
      })
      if (!resp.ok) {
        const errBody = (await resp.json().catch(() => ({}))) as { detail?: string }
        throw new ApiError(resp.status, errBody.detail || resp.statusText)
      }
      return (await resp.json()) as T
    } finally {
      clearTimeout(timer)
    }
  }

  /** 带重试的请求：网络错误/超时自动重试，HTTP 错误（含 404）不重试 */
  private async request<T>(method: string, path: string, body?: unknown): Promise<T> {
    let lastError: unknown
    for (let attempt = 0; attempt <= this.retryCount; attempt++) {
      try {
        return await this.requestOnce<T>(method, path, body)
      } catch (e) {
        lastError = e
        if (e instanceof ApiError) throw e // 服务端明确响应的错误不重试
      }
    }
    throw lastError
  }

  get<T>(path: string): Promise<T> {
    return this.request<T>('GET', path)
  }

  post<T>(path: string, body?: unknown): Promise<T> {
    return this.request<T>('POST', path, body)
  }

  put<T>(path: string, body?: unknown): Promise<T> {
    return this.request<T>('PUT', path, body)
  }

  delete<T>(path: string): Promise<T> {
    return this.request<T>('DELETE', path)
  }
}
