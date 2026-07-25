import { useEffect, useRef, useState, useCallback } from 'react'
import type { PanelPosition } from '../store/panelStore'

/** 停靠位（translateY 百分比）：收起 85%、半屏 50%、全屏 0 */
const STOPS: { pos: PanelPosition; pct: number }[] = [
  { pos: 'full', pct: 0 },
  { pos: 'half', pct: 50 },
  { pos: 'collapsed', pct: 85 },
]

/**
 * 下拉面板拖拽 Hook（spec §4.2）：
 * - 垂直拖拽，手指位移 / 3 映射面板位移
 * - 松手吸附最近停靠位
 * - 兼容 touch 与 mouse
 */
export function useDragPanel(
  position: PanelPosition,
  onSnap: (pos: PanelPosition) => void,
  enabled: boolean,
) {
  const pctOf = (pos: PanelPosition) => STOPS.find((s) => s.pos === pos)!.pct
  const [dragPct, setDragPct] = useState<number | null>(null)
  const dragState = useRef<{ startY: number; startPct: number } | null>(null)
  const panelRef = useRef<HTMLDivElement | null>(null)

  const currentPct = dragPct ?? pctOf(position)

  const getY = (e: TouchEvent | MouseEvent) =>
    'touches' in e ? e.touches[0].clientY : e.clientY

  const onDragStart = useCallback(
    (e: React.TouchEvent | React.MouseEvent) => {
      if (!enabled) return
      const y = 'touches' in e ? e.touches[0].clientY : e.clientY
      dragState.current = { startY: y, startPct: pctOf(position) }
    },
    [enabled, position],
  )

  useEffect(() => {
    const onMove = (e: TouchEvent | MouseEvent) => {
      const st = dragState.current
      const panel = panelRef.current
      if (!st || !panel) return
      const dy = getY(e) - st.startY
      const h = panel.offsetHeight || 1
      // 位移 /3 映射为面板位移（百分比）
      const pct = st.startPct + (dy / 3 / h) * 100
      setDragPct(Math.max(0, Math.min(92, pct)))
      if (e.cancelable) e.preventDefault()
    }
    const onUp = () => {
      const st = dragState.current
      if (!st) return
      dragState.current = null
      setDragPct((pct) => {
        if (pct == null) return null
        // 吸附最近停靠位
        let best = STOPS[0]
        for (const s of STOPS) {
          if (Math.abs(s.pct - pct) < Math.abs(best.pct - pct)) best = s
        }
        onSnap(best.pos)
        return null
      })
    }
    window.addEventListener('touchmove', onMove, { passive: false })
    window.addEventListener('touchend', onUp)
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
    return () => {
      window.removeEventListener('touchmove', onMove)
      window.removeEventListener('touchend', onUp)
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseup', onUp)
    }
  }, [onSnap])

  return { panelRef, currentPct, dragging: dragPct !== null, onDragStart }
}
