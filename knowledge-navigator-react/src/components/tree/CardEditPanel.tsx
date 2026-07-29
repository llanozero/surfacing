import React, { useState, useEffect } from 'react'
import type { CognitiveCard } from '../../data/types'
import { allNavNodes } from '../../data/allNavNodes'
import { useCardStore } from '../../store/cardStore'
import { useToastStore } from '../shared/Toast'
import { useAiGenerate } from '../../hooks/useAiGenerate'
import { deriveParent } from '../../utils/treeUtils'
import NodeSelector from '../node-mgr/NodeSelector'
import mgrStyles from '../node-mgr/NodeMgr.module.css'
import styles from './CardEditPanel.module.css'

interface CardEditPanelProps {
  card: CognitiveCard
}

const TAG_OPTIONS = [
  { value: '', label: '无标签' },
  { value: '决策分支', label: '决策分支' },
  { value: '层级分类', label: '层级分类' },
]

/** 认知卡片编辑面板：基本字段 + 语料库 + 绑定导航节点（草稿暂存，保存时写入） */
const CardEditPanel: React.FC<CardEditPanelProps> = ({ card }) => {
  const { updateField, addCorpus, updateCorpus, removeCorpus, addBoundNode, removeBoundNode, deleteCard } =
    useCardStore()
  const allCards = useCardStore((s) => s.allCards)
  const toast = useToastStore((s) => s.show)
  const { generating, generateCardTitle, generateCardDescription } = useAiGenerate()
  const [selectorOpen, setSelectorOpen] = useState(false)
  const [newCorpus, setNewCorpus] = useState('')
  const [confirmingDelete, setConfirmingDelete] = useState(false)

  // 草稿状态：本地编辑暂存，保存时才写入数据源
  const [draftTitle, setDraftTitle] = useState(card.title)
  const [draftDesc, setDraftDesc] = useState(card.description ?? '')
  const [draftTag, setDraftTag] = useState(card.tag ?? '')
  const [dirty, setDirty] = useState(false)

  // 切换卡片时重置草稿
  useEffect(() => {
    setDraftTitle(card.title)
    setDraftDesc(card.description ?? '')
    setDraftTag(card.tag ?? '')
    setDirty(false)
  }, [card.id]) // eslint-disable-line react-hooks/exhaustive-deps

  /** 子卡片（文件夹的生成依据之一） */
  const children = allCards.filter((c) => {
    if (c.id === card.id) return false
    try {
      return deriveParent(c.id) === card.id
    } catch {
      return false
    }
  })
  /** 生成依据是否充足：有语料或有子卡片 */
  const hasAiSource = card.corpus.length > 0 || children.length > 0
  const aiDisabledHint = '缺少生成依据，请先添加语料或子卡片'

  const handleGenTitle = async () => {
    const result = await generateCardTitle(card, children)
    if (!result) {
      toast('生成失败，请重试')
      return
    }
    let text = result.text
    let truncated = false
    if (text.length > 10) {
      text = text.slice(0, 9) + '…'
      truncated = true
    }
    setDraftTitle(text)
    setDirty(true)
    toast(`已生成标题${result.source === 'local' ? '（本地模式）' : ''}${truncated ? '（已截断）' : ''}`)
  }

  const handleGenDescription = async () => {
    const result = await generateCardDescription(card, children)
    if (!result) {
      toast('生成失败，请重试')
      return
    }
    setDraftDesc(result.text)
    setDirty(true)
    toast(`已生成描述${result.source === 'local' ? '（本地模式）' : ''}`)
  }

  // 保存草稿（仅本地缓存，不写后端）
  const handleSave = () => {
    updateField(card.id, 'title', draftTitle)
    updateField(card.id, 'description', draftDesc)
    updateField(card.id, 'tag', draftTag || undefined)
    setDirty(false)
    toast('卡片已保存（本地缓存）')
  }

  // 取消草稿（放弃修改）
  const handleCancel = () => {
    setDraftTitle(card.title)
    setDraftDesc(card.description ?? '')
    setDraftTag(card.tag ?? '')
    setDirty(false)
    toast('已放弃修改')
  }

  const boundNodes = (card.bound_nodes ?? [])
    .map((id) => ({ id, node: allNavNodes.find((n) => n.id === id) }))
    .filter((x) => x.node)

  const nodeCandidates = allNavNodes
    .filter((n) => !card.bound_nodes?.includes(n.id))
    .map((n) => ({ id: n.id, label: n.label, meta: n.id }))

  const handleAddCorpus = () => {
    if (!newCorpus.trim()) return
    addCorpus(card.id, newCorpus)
    setNewCorpus('')
    toast('已添加语料')
  }

  const handleDelete = () => {
    if (!confirmingDelete) {
      setConfirmingDelete(true)
      return
    }
    const result = deleteCard(card.id)
    setConfirmingDelete(false)
    if (result.ok) toast(`已删除卡片 ${card.id}`)
    else toast(result.reason ?? '删除失败')
  }

  return (
    <div className={mgrStyles.editPanel}>
      {/* 基本字段 */}
      <section className={mgrStyles.section}>
        <div className={mgrStyles.fieldRow}>
          <span className={mgrStyles.fieldLabel}>id（只读）</span>
          <span className={mgrStyles.readonly}>{card.id}</span>
        </div>
        <div className={mgrStyles.fieldRow}>
          <span className={mgrStyles.fieldLabel}>标题</span>
          <div className={styles.aiRow}>
            <input
              className={mgrStyles.input}
              value={draftTitle}
              onChange={(e) => {
                setDraftTitle(e.target.value)
                setDirty(true)
              }}
            />
            <button
              className={styles.aiButton}
              onClick={handleGenTitle}
              disabled={generating || !hasAiSource}
              title={hasAiSource ? 'AI 生成标题' : aiDisabledHint}
              aria-label="AI 生成标题"
            >
              {generating ? '⏳' : '✨'}
            </button>
          </div>
        </div>
        <div className={mgrStyles.fieldRow}>
          <span className={mgrStyles.fieldLabel}>类型 / 标签</span>
          <div className={styles.typeRow}>
            <span className={styles.typeBadge}>
              {card.type === 'folder' ? '文件夹' : '叶子卡片'}
            </span>
            <select
              className={mgrStyles.typeSelect}
              value={draftTag}
              onChange={(e) => {
                setDraftTag(e.target.value)
                setDirty(true)
              }}
            >
              {TAG_OPTIONS.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div className={mgrStyles.fieldRow}>
          <span className={mgrStyles.fieldLabel}>描述</span>
          <div className={styles.aiRow}>
            <textarea
              className={mgrStyles.textarea}
              rows={2}
              placeholder="简短概述卡片内容（1-2 句话）"
              value={draftDesc}
              onChange={(e) => {
                setDraftDesc(e.target.value)
                setDirty(true)
              }}
            />
            <button
              className={styles.aiButton}
              onClick={handleGenDescription}
              disabled={generating || !hasAiSource}
              title={hasAiSource ? 'AI 生成描述' : aiDisabledHint}
              aria-label="AI 生成描述"
            >
              {generating ? '⏳' : '✨'}
            </button>
          </div>
        </div>
      </section>

      {/* ── 保存/取消按钮 ── */}
      <div className={mgrStyles.saveBar}>
        <button
          className={mgrStyles.saveBtn}
          onClick={handleSave}
          disabled={!dirty}
        >
          💾 保存
        </button>
        <button
          className={mgrStyles.cancelBtn}
          onClick={handleCancel}
          disabled={!dirty}
        >
          ↩ 取消
        </button>
        <span className={mgrStyles.saveHint}>
          {dirty ? '有未保存的更改' : '已是最新'}
        </span>
      </div>

      {/* 语料库 */}
      <section className={mgrStyles.section}>
        <h4 className={mgrStyles.sectionTitle}>语料库 ({card.corpus.length})</h4>
        {card.corpus.map((text, i) => (
          <div key={i} className={styles.corpusRow}>
            <textarea
              className={mgrStyles.textarea}
              rows={2}
              value={text}
              onChange={(e) => updateCorpus(card.id, i, e.target.value)}
            />
            <button
              className={`${mgrStyles.removeBtn} ${styles.corpusRemove}`}
              onClick={() => removeCorpus(card.id, i)}
              aria-label={`删除语料 ${i + 1}`}
            >
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                <path d="M18 6 6 18M6 6l12 12" />
              </svg>
            </button>
          </div>
        ))}
        {card.corpus.length === 0 && <p className={mgrStyles.historyNote}>暂无语料</p>}
        <div className={styles.corpusAdd}>
          <textarea
            className={mgrStyles.textarea}
            rows={2}
            placeholder="输入新的语料段落..."
            value={newCorpus}
            onChange={(e) => setNewCorpus(e.target.value)}
          />
          <button className={mgrStyles.addBtn} onClick={handleAddCorpus} disabled={!newCorpus.trim()}>
            + 添加语料
          </button>
        </div>
      </section>

      {/* 绑定导航节点 */}
      <section className={mgrStyles.section}>
        <h4 className={mgrStyles.sectionTitle}>绑定导航节点 ({boundNodes.length})</h4>
        {boundNodes.map(({ id, node }) => (
          <div key={id} className={mgrStyles.boundRow}>
            <span className={styles.nodeDot} />
            <span className={mgrStyles.boundMain}>{node!.label}</span>
            <span className={mgrStyles.boundMeta}>{id}</span>
            <button
              className={mgrStyles.removeBtn}
              onClick={() => removeBoundNode(card.id, id)}
              aria-label={`移除绑定 ${node!.label}`}
            >
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                <path d="M18 6 6 18M6 6l12 12" />
              </svg>
            </button>
          </div>
        ))}
        {boundNodes.length === 0 && <p className={mgrStyles.historyNote}>暂未绑定任何导航节点</p>}

        <button className={mgrStyles.addBtn} onClick={() => setSelectorOpen(true)}>
          + 添加绑定
        </button>

        {selectorOpen && (
          <NodeSelector
            title="绑定导航节点"
            items={nodeCandidates}
            onSelect={(id) => {
              addBoundNode(card.id, id)
              setSelectorOpen(false)
              toast('已添加绑定节点')
            }}
            onClose={() => setSelectorOpen(false)}
          />
        )}
      </section>

      {/* 删除卡片（两步确认；文件夹须为空） */}
      <section className={mgrStyles.section}>
        <div className={styles.deleteZone}>
          {confirmingDelete ? (
            <>
              <span className={styles.deleteHint}>
                {card.type === 'folder' ? '确认删除此文件夹？须为空文件夹' : '确认删除此卡片？'}
              </span>
              <button className={styles.deleteConfirmBtn} onClick={handleDelete}>
                确认删除
              </button>
              <button className={styles.deleteCancelBtn} onClick={() => setConfirmingDelete(false)}>
                取消
              </button>
            </>
          ) : (
            <button className={styles.deleteBtn} onClick={handleDelete}>
              删除卡片
            </button>
          )}
        </div>
      </section>
    </div>
  )
}

export default CardEditPanel
