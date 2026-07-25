import React from 'react'
import { createPortal } from 'react-dom'
import type { ValidationError } from '../../utils/yamlIO'
import styles from './ImportDialog.module.css'

interface ImportErrorDialogProps {
  errors: ValidationError[]
  onClose: () => void
}

const TYPE_LABEL: Record<ValidationError['type'], string> = {
  structure: '结构',
  field: '字段',
  reference: '引用',
}

/** 导入错误对话框：列出所有校验错误，不改变任何数据 */
const ImportErrorDialog: React.FC<ImportErrorDialogProps> = ({ errors, onClose }) => {
  return createPortal(
    <div className={styles.mask} onClick={onClose}>
      <div className={styles.dialog} role="alertdialog" aria-modal="true" onClick={(e) => e.stopPropagation()}>
        <h3 className={styles.title}>导入失败：文件校验未通过</h3>

        <div className={styles.body}>
          <ul className={styles.errorList}>
            {errors.map((err, i) => (
              <li key={i} className={styles.errorItem}>
                <span className={styles.errorTag}>{TYPE_LABEL[err.type]}</span>
                {err.itemId ? `[${err.itemId}] ` : ''}
                {err.message}
              </li>
            ))}
          </ul>
          <p className={styles.keepNote}>数据未被修改，请修正文件后重新导入。</p>
        </div>

        <div className={styles.actions}>
          <button className={styles.confirmBtn} onClick={onClose}>
            知道了
          </button>
        </div>
      </div>
    </div>,
    document.body,
  )
}

export default ImportErrorDialog
