import { getTtsConfig, type TtsConfig } from '../config/tts'
import { isRemoteMode } from '../config/backend'

let currentAudio: HTMLAudioElement | null = null

export function stopTts(): void {
  if (currentAudio) {
    currentAudio.pause()
    currentAudio = null
  }
}

export function isTtsPlaying(): boolean {
  return currentAudio !== null && !currentAudio.paused
}

export async function playTts(text: string, overrides?: Partial<TtsConfig>): Promise<void> {
  if (!text) return
  if (!isRemoteMode()) {
    throw new Error('TTS 需要后端支持，请切换到远程模式')
  }

  stopTts()
  const cfg = { ...getTtsConfig(), ...overrides }

  const res = await fetch('/api/tts/speak', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      text: text.slice(0, 5000),
      voice: cfg.voice,
      rate: cfg.rate,
      pitch: cfg.pitch,
    }),
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'TTS 请求失败' }))
    throw new Error(err.detail || 'TTS 请求失败')
  }

  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  currentAudio = new Audio(url)
  currentAudio.onended = () => {
    URL.revokeObjectURL(url)
    currentAudio = null
  }
  currentAudio.onerror = () => {
    URL.revokeObjectURL(url)
    currentAudio = null
  }
  await currentAudio.play()
}
