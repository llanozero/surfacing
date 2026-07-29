/**
 * TTS 预热工具：加载导航图时，后台批量预合成节点音频
 *
 * 依赖后端 POST /api/tts/warmup 接口（见 nav-tts-asset-management.md §5.4）
 */

import { getTtsConfig } from '../config/tts'
import { apiUrl } from './ttsPlayer'

interface GraphNode {
  id: string
  graph_id?: string
  label: string
  description?: string
}

interface WarmupItem {
  text: string
  voice: string
  rate: string
  pitch: string
  source: string
}

/**
 * 触发后台预热
 * @param nodes  当前画布中的所有导航节点
 * @param graphIdOverride  可选的 graph_id 覆盖（钻入子图时使用）
 */
export async function triggerWarmup(
  nodes: GraphNode[],
  graphIdOverride?: string,
): Promise<void> {
  const cfg = getTtsConfig()
  if (!cfg.prewarm) return
  if (!nodes || nodes.length === 0) return

  const items: WarmupItem[] = nodes.map((n) => ({
    text: `${n.label}。${n.description || ''}`,
    voice: cfg.voice,
    rate: cfg.rate,
    pitch: cfg.pitch,
    source: `node/${graphIdOverride || n.graph_id || 'top'}/${n.id}`,
  }))

  try {
    const resp = await fetch(apiUrl('/api/tts/warmup'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ items }),
    })
    if (!resp.ok) {
      console.warn('[ttsWarmup] 预热请求失败:', resp.status)
    }
  } catch {
    // 预热失败不阻塞用户操作
  }
}
