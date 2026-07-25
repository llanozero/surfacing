import React, { useState } from 'react'
import { useNavNodeStore, getEditingNode } from '../../store/navNodeStore'
import { useToastStore } from '../shared/Toast'
import BoundCardEditor from './BoundCardEditor'
import NextNodeEditor from './NextNodeEditor'
import BrowseHistoryViewer from './BrowseHistoryViewer'
import styles from './NodeMgr.module.css'
import cardStyles from '../tree/CardEditPanel.module.css'

/** 右侧编辑面板：基本字段 + 绑定卡片 + 指向节点 + 浏览记录 + 删除节点 */
const NodeEditPanel: React.FC = () => {
  const { allNodes, selectedNodeId, updateField, deleteNavNode } = useNavNodeStore()
  const toast = useToastStore((s) => s.show)
  const [confirmingDelete, setConfirmingDelete] = useState(false)
  const node = getEditingNode({ allNodes, selectedNodeId })

  const handleDelete = () => {
    if (!confirmingDelete) {
      setConfirmingDelete(true)
      return
    }
    const nodeId = selectedNodeId
    const result = deleteNavNode()
    setConfirmingDelete(false)
    if (result.ok) toast(`已删除节点 ${nodeId}`)
    else toast(result.reason ?? '删除失败')
  }

  if (!node) {
    return (
      <div className={styles.editPanel}>
        <p className={styles.editEmpty}>请从列表中选择一个导航节点</p>
      </div>
    )
  }

  return (
    <div className={styles.editPanel}>
      {/* 基本字段（NM-04 / NM-05，自动保存） */}
      <section className={styles.section}>
        <div className={styles.fieldRow}>
          <span className={styles.fieldLabel}>id（只读）</span>
          <span className={styles.readonly}>{node.id}</span>
        </div>
        <div className={styles.fieldRow}>
          <span className={styles.fieldLabel}>label</span>
          <input
            className={styles.input}
            value={node.label}
            onChange={(e) => updateField('label', e.target.value)}
          />
        </div>
        <div className={styles.fieldRow}>
          <span className={styles.fieldLabel}>description</span>
          <textarea
            className={styles.textarea}
            rows={3}
            value={node.description}
            onChange={(e) => updateField('description', e.target.value)}
          />
        </div>
      </section>

      <BoundCardEditor node={node} />
      <NextNodeEditor node={node} />
      <BrowseHistoryViewer node={node} />

      {/* 删除节点（两步确认；级联清理其他节点与卡片的引用） */}
      <section className={styles.section}>
        <div className={cardStyles.deleteZone}>
          {confirmingDelete ? (
            <>
              <span className={cardStyles.deleteHint}>
                确认删除此节点？相关引用将一并清理
              </span>
              <button className={cardStyles.deleteConfirmBtn} onClick={handleDelete}>
                确认删除
              </button>
              <button className={cardStyles.deleteCancelBtn} onClick={() => setConfirmingDelete(false)}>
                取消
              </button>
            </>
          ) : (
            <button className={cardStyles.deleteBtn} onClick={handleDelete}>
              删除节点
            </button>
          )}
        </div>
      </section>
    </div>
  )
}

export default NodeEditPanel
