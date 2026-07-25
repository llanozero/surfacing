import React, { useState } from 'react'
import { createPortal } from 'react-dom'
import type { NextNodeRef } from '../../data/types'
import { weightToPriority } from '../../utils/quickConnectUtils'
import styles from './ConnectionEditPopover.module.css'

interface ConnectionEditPopoverProps {
  fromId: string
  toId: string
  fromLabel: string
  toLabel: string
  initialRef: NextNodeRef
  onSave: (
    fromId: string,
    toId: string,
    updates: { preset_priority: number; connection_type: NextNodeRef['connection_type'] },
  ) => void
  onDelete: (fromId: string, toId: string) => void
  onClose: () => void
}

const TYPE_OPTIONS: { value: NextNodeRef['connection_type']; label: string }[] = [
  { value: 'preset', label: 'preset（预设）' },
  { value: 'user_added', label: 'user_added（用户添加）' },
  { value: 'browse_derived', label: 'browse_derived（浏览派生）' },
]

/** 轻量连接编辑浮层：修改优先级序号 / 连接类型 / 删除连接。点击外部自动保存并关闭 */
const ConnectionEditPopover: React.FC<ConnectionEditPopoverProps> = ({
  fromId,
  toId,
  fromLabel,
  toLabel,
  initialRef,
  onSave,
  onDelete,
  onClose,
}) => {
  const [priority, setPriority] = useState<number>(weightToPriority(initialRef.preset_weight))
  const [connType, setConnType] = useState<NextNodeRef['connection_type']>(initialRef.connection_type)

  const save = () => {
    onSave(fromId, toId, { preset_priority: Math.max(1, Math.round(priority)), connection_type: connType })
    onClose()
  }

  return createPortal(
    <div className={styles.mask} onClick={save}>
      <div className={styles.popover} role="dialog" aria-modal="true" onClick={(e) => e.stopPropagation()}>
        <h3 className={styles.title}>
          {fromLabel}
          <span className={styles.arrow}>→</span>
          {toLabel}
        </h3>

        <div className={styles.fieldRow}>
          <span className={styles.fieldLabel}>优先级</span>
          <input
            className={styles.priorityInput}
            type="number"
            min={1}
            step={1}
            value={priority}
            onChange={(e) => setPriority(Math.max(1, Math.round(Number(e.target.value) || 1)))}
          />
          <span className={styles.hint}>数字越小优先级越高</span>
        </div>

        <div className={styles.fieldRow}>
          <span className={styles.fieldLabel}>连接类型</span>
          <select
            className={styles.typeSelect}
            value={connType}
            onChange={(e) => setConnType(e.target.value as NextNodeRef['connection_type'])}
          >
            {TYPE_OPTIONS.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </div>

        <div className={styles.actions}>
          <button
            className={styles.deleteBtn}
            onClick={() => {
              onDelete(fromId, toId)
              onClose()
            }}
          >
            删除
          </button>
          <button className={styles.saveBtn} onClick={save}>
            保存
          </button>
        </div>
      </div>
    </div>,
    document.body,
  )
}

export default ConnectionEditPopover
