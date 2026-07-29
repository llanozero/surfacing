/** TTS 语音配置（localStorage 持久化） */

export interface TtsConfig {
  voice: string
  rate: string   // e.g. '+0%', '-20%', '+50%'
  pitch: string  // e.g. '+0Hz', '-10Hz', '+5Hz'
  prewarm: boolean
}

const STORAGE_KEY = 'kn_tts_config'

const DEFAULT: TtsConfig = {
  voice: 'zh-CN-XiaoxiaoNeural',
  rate: '+0%',
  pitch: '+0Hz',
  prewarm: false,
}

export function getDefaultTtsConfig(): TtsConfig {
  return { ...DEFAULT }
}

export function getTtsConfig(): TtsConfig {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return { ...DEFAULT }
    return { ...DEFAULT, ...JSON.parse(raw) }
  } catch {
    return { ...DEFAULT }
  }
}

export function setTtsConfig(partial: Partial<TtsConfig>): void {
  const cfg = { ...getTtsConfig(), ...partial }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(cfg))
}
