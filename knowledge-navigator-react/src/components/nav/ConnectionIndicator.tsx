import React from 'react'
import { getConnectionStatus, weightToPriority } from '../../utils/quickConnectUtils'
import styles from './ConnectionIndicator.module.css'

interface ConnectionIndicatorProps {
  fromId: string
  toId: string
  /** 点击 ✚（缺失连接） */
  onConnect?: (fromId: string, toId: string) => void
  /** 点击 ✅（已有连接，弹出编辑浮层） */
  onEdit?: (fromId: string, toId: string) => void
}

/**
 * 相邻途经点之间的连接状态指示器：
 * ✅ 绿色已连接（hover 显示优先级编号，点击编辑）
 * ✚ 蓝色可新建（点击一键建立连接）
 */
const ConnectionIndicator: React.FC<ConnectionIndicatorProps> = ({ fromId, toId, onConnect, onEdit }) => {
  const { status, ref } = getConnectionStatus(fromId, toId)

  if (status === 'connected' && ref) {
    const priority = weightToPriority(ref.preset_weight)
    return (
      <button
        className={`${styles.indicator} ${styles.connected}`}
        onClick={() => onEdit?.(fromId, toId)}
        title={`已连接 · 优先级 #${priority} · 点击编辑`}
        aria-label={`已连接，优先级 ${priority}，点击编辑`}
      >
        ✓<span className={styles.priority}>#{priority}</span>
      </button>
    )
  }

  if (status === 'missing') {
    return (
      <button
        className={`${styles.indicator} ${styles.missing}`}
        onClick={() => onConnect?.(fromId, toId)}
        title="缺失连接 · 点击一键建立（优先级 #1）"
        aria-label="缺失连接，点击建立"
      >
        ✚
      </button>
    )
  }

  return (
    <span className={`${styles.indicator} ${styles.unavailable}`} title="节点不可用">
      ⚠️
    </span>
  )
}

export default ConnectionIndicator
