import React from 'react'
import { createPortal } from 'react-dom'
import type { ImportPreview } from '../../utils/yamlIO'
import styles from './ImportDialog.module.css'

interface ImportConfirmDialogProps {
  preview: ImportPreview
  onConfirm: () => void
  onCancel: () => void
}

/** 导入确认对话框：展示新增/覆盖统计，确认后执行合并（upsert，不删除现有数据） */
const ImportConfirmDialog: React.FC<ImportConfirmDialogProps> = ({ preview, onConfirm, onCancel }) => {
  return createPortal(
    <div className={styles.mask} onClick={onCancel}>
      <div className={styles.dialog} role="dialog" aria-modal="true" onClick={(e) => e.stopPropagation()}>
        <h3 className={styles.title}>确认导入 YAML 数据</h3>

        <div className={styles.body}>
          <div className={styles.previewGroup}>
            <span className={styles.previewTitle}>认知卡片：{preview.cards.total} 张</span>
            <div className={styles.previewLine}>
              <span>新增</span>
              <span className={styles.previewValue}>{preview.cards.added} 张</span>
            </div>
            <div className={styles.previewLine}>
              <span>覆盖（id 冲突）</span>
              <span className={styles.previewValue}>{preview.cards.overwritten} 张</span>
            </div>
          </div>

          <div className={styles.previewGroup}>
            <span className={styles.previewTitle}>导航节点：{preview.nodes.total} 个</span>
            <div className={styles.previewLine}>
              <span>新增</span>
              <span className={styles.previewValue}>{preview.nodes.added} 个</span>
            </div>
            <div className={styles.previewLine}>
              <span>覆盖（id 冲突）</span>
              <span className={styles.previewValue}>{preview.nodes.overwritten} 个</span>
            </div>
          </div>

          <p className={styles.keepNote}>
            采用合并导入：当前已有但文件中不包含的条目将保留不动。
          </p>
        </div>

        <div className={styles.actions}>
          <button className={styles.cancelBtn} onClick={onCancel}>
            取消
          </button>
          <button className={styles.confirmBtn} onClick={onConfirm}>
            确认导入
          </button>
        </div>
      </div>
    </div>,
    document.body,
  )
}

export default ImportConfirmDialog
