import { useEffect, useRef } from 'react'

/**
 * 卡片滑动 Hook：上滑下一张 / 下滑上一张。
 * 支持 touch 滑动与鼠标滚轮。
 */
export function useCardSwipe(
  stackRef: React.RefObject<HTMLDivElement | null>,
  onNext: () => void,
  onPrev: () => void,
) {
  const stateRef = useRef({ startY: 0, active: false, wheelLock: false })
  const cbRef = useRef({ onNext, onPrev })
  cbRef.current = { onNext, onPrev }

  useEffect(() => {
    const el = stackRef.current
    if (!el) return
    const st = stateRef.current

    const onTouchStart = (e: TouchEvent) => {
      st.startY = e.touches[0].clientY
      st.active = true
    }
    const onTouchEnd = (e: TouchEvent) => {
      if (!st.active) return
      st.active = false
      const dy = e.changedTouches[0].clientY - st.startY
      if (dy < -48) cbRef.current.onNext() // 上滑 → 下一张
      else if (dy > 48) cbRef.current.onPrev()
    }
    const onWheel = (e: WheelEvent) => {
      if (st.wheelLock) return
      st.wheelLock = true
      setTimeout(() => (st.wheelLock = false), 350)
      if (e.deltaY > 24) cbRef.current.onNext()
      else if (e.deltaY < -24) cbRef.current.onPrev()
    }

    el.addEventListener('touchstart', onTouchStart, { passive: true })
    el.addEventListener('touchend', onTouchEnd)
    el.addEventListener('wheel', onWheel, { passive: true })
    return () => {
      el.removeEventListener('touchstart', onTouchStart)
      el.removeEventListener('touchend', onTouchEnd)
      el.removeEventListener('wheel', onWheel)
    }
  }, [stackRef])
}
