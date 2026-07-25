import { create } from 'zustand'
import React from 'react'
import styles from './Toast.module.css'

interface ToastStore {
  message: string | null
  show: (msg: string, duration?: number) => void
  hide: () => void
}

export const useToastStore = create<ToastStore>((set) => ({
  message: null,
  show: (msg, duration = 2000) => {
    set({ message: msg })
    setTimeout(() => set({ message: null }), duration)
  },
  hide: () => set({ message: null }),
}))

const Toast: React.FC = () => {
  const message = useToastStore((s) => s.message)
  if (!message) return null

  return (
    <div className={styles.toast} role="status" aria-live="polite">
      {message}
    </div>
  )
}

export default Toast
