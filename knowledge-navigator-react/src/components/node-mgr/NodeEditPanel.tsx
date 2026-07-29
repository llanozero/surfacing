import React, { useState, useEffect } from 'react'
import { useNavNodeStore, getEditingNode } from '../../store/navNodeStore'
import { useCardStore } from '../../store/cardStore'
import { useNavStore } from '../../store/navStore'
import { useToastStore } from '../shared/Toast'
import { useAiGenerate } from '../../hooks/useAiGenerate'
import BoundCardEditor from './BoundCardEditor'
import NextNodeEditor from './NextNodeEditor'
import BrowseHistoryViewer from './BrowseHistoryViewer'
import styles from './NodeMgr.module.css'
import cardStyles from '../tree/CardEditPanel.module.css'

/** 右侧编辑面板：基本字段 + 绑定卡片 + 指向节点 + 浏览记录 + 删除节点 */
const NodeEditPanel: React.FC = () => {
  const { allNodes, selectedNodeId, updateField, deleteNavNode } = useNavNodeStore()
  const allCards = useCardStore((s) => s.allCards)
  const toast = useToastStore((s) => s.show)
  const { generating, generateNodeLabel, generateNodeDescription } = useAiGenerate()
  const [confirmingDelete, setConfirmingDelete] = useState(false)
  const node = getEditingNode({ allNodes, selectedNodeId })

  // 草稿状态：本地编辑暂存，保存时才写入数据源
  const [draftLabel, setDraftLabel] = useState(node?.label ?? '')
  const [draftDesc, setDraftDesc] = useState(node?.description ?? '')
  const [dirty, setDirty] = useState(false)

  // 切换节点时重置草稿
  useEffect(() => {
    setDraftLabel(node?.label ?? '')
    setDraftDesc(node?.description ?? '')
    setDirty(false)
  }, [node?.id])

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

  /* ---- AI 生成依据 ---- */
  const boundCards = (node.bound_cards ?? [])
    .map((id) => allCards.find((c) => c.id === id))
    .filter((c): c is NonNullable<typeof c> => Boolean(c))
  const nav = useNavStore.getState()
  const prevNodes = nav.getPrevNodes(node.id).map((x) => x.node)
  const nextNodes = nav.getNextNodes(node.id).map((x) => x.node)

  /** label 生成依据：至少绑定一张卡片 */
  const hasLabelSource = boundCards.length >= 1
  /** description 生成依据：绑定卡片语料/描述，或前驱/后继节点描述，任意其一 */
  const hasDescSource =
    boundCards.some((c) => c.corpus.length > 0 || c.description) ||
    prevNodes.some((n) => n.description) ||
    nextNodes.some((n) => n.description)
  const labelDisabledHint = '缺少生成依据，请先绑定认知卡片'
  const descDisabledHint = '缺少生成依据，请先绑定卡片或连接前驱/后继节点'

  // 保存草稿（仅本地缓存，不写后端）
  const handleSave = () => {
    if (!node) return
    updateField('label', draftLabel)
    updateField('description', draftDesc)
    setDirty(false)
    toast('节点已保存（本地缓存）')
  }

  // 取消草稿（放弃修改）
  const handleCancel = () => {
    if (!node) return
    setDraftLabel(node.label)
    setDraftDesc(node.description ?? '')
    setDirty(false)
    toast('已放弃修改')
  }

  const handleGenLabel = async () => {
    const result = await generateNodeLabel(node, boundCards)
    if (!result) {
      toast('生成失败，请重试')
      return
    }
    updateField('label', result.text)
    toast(`已生成标签${result.source === 'local' ? '（本地模式）' : ''}`)
  }

  const handleGenDescription = async () => {
    const result = await generateNodeDescription(node, boundCards, prevNodes, nextNodes)
    if (!result) {
      toast('生成失败，请重试')
      return
    }
    updateField('description', result.text)
    toast(`已生成描述${result.source === 'local' ? '（本地模式）' : ''}`)
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
          <div className={styles.aiRow}>
            <input
              className={styles.input}
              value={draftLabel}
              onChange={(e) => {
                setDraftLabel(e.target.value)
                setDirty(true)
              }}
            />
            <button
              className={styles.aiButton}
              onClick={handleGenLabel}
              disabled={generating || !hasLabelSource}
              title={hasLabelSource ? 'AI 生成标签' : labelDisabledHint}
              aria-label="AI 生成标签"
            >
              {generating ? '⏳' : '✨'}
            </button>
          </div>
        </div>
        <div className={styles.fieldRow}>
          <span className={styles.fieldLabel}>description</span>
          <div className={styles.aiRow}>
            <textarea
              className={styles.textarea}
              rows={3}
              value={draftDesc}
              onChange={(e) => {
                setDraftDesc(e.target.value)
                setDirty(true)
              }}
            />
            <button
              className={styles.aiButton}
              onClick={handleGenDescription}
              disabled={generating || !hasDescSource}
              title={hasDescSource ? 'AI 生成描述' : descDisabledHint}
              aria-label="AI 生成描述"
            >
              {generating ? '⏳' : '✨'}
            </button>
          </div>
        </div>
      </section>

      <BoundCardEditor node={node} />
      <NextNodeEditor node={node} />

      {/* ── 保存/取消按钮 ── */}
      <div className={styles.saveBar}>
        <button
          className={styles.saveBtn}
          onClick={handleSave}
          disabled={!dirty}
        >
          💾 保存
        </button>
        <button
          className={styles.cancelBtn}
          onClick={handleCancel}
          disabled={!dirty}
        >
          ↩ 取消
        </button>
        <span className={styles.saveHint}>
          {dirty ? '有未保存的更改' : '已是最新'}
        </span>
      </div>

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
