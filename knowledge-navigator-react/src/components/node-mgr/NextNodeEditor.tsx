import React, { useState } from 'react'
import type { NavNode, NextNodeRef } from '../../data/types'
import { useNavNodeStore } from '../../store/navNodeStore'
import { useToastStore } from '../shared/Toast'
import Button from '../shared/Button'
import styles from './NodeMgr.module.css'

interface NextNodeEditorProps {
  node: NavNode
}

const CONNECTION_TYPES: { value: NextNodeRef['connection_type']; label: string }[] = [
  { value: 'preset', label: 'preset' },
  { value: 'browse_derived', label: 'browse_derived' },
  { value: 'user_added', label: 'user_added' },
]

/** 指向节点权重编辑（NM-08 添加 / NM-09 权重 / NM-10 类型 / NM-11 删除） */
const NextNodeEditor: React.FC<NextNodeEditorProps> = ({ node }) => {
  const { allNodes, addNextNode, updateNextNode, removeNextNode } = useNavNodeStore()
  const toast = useToastStore((s) => s.show)

  const [formOpen, setFormOpen] = useState(false)
  const [targetId, setTargetId] = useState('')
  const [presetWeight, setPresetWeight] = useState(0.5)
  const [browseWeight, setBrowseWeight] = useState(0.3)
  const [connType, setConnType] = useState<NextNodeRef['connection_type']>('preset')

  // 候选目标：排除自身与已添加的节点
  const candidates = allNodes.filter(
    (n) => n.id !== node.id && !node.next_nodes.some((e) => e.target_id === n.id),
  )

  const openForm = () => {
    setTargetId(candidates[0]?.id ?? '')
    setFormOpen(true)
  }

  const handleConfirm = () => {
    if (!targetId) return
    addNextNode({
      target_id: targetId,
      preset_weight: presetWeight,
      browse_weight: browseWeight,
      connection_type: connType,
    })
    setFormOpen(false)
    toast('已添加指向节点')
  }

  return (
    <section className={styles.section}>
      <h4 className={styles.sectionTitle}>指向节点权重 ({node.next_nodes.length})</h4>

      {node.next_nodes.map((ref) => {
        const target = allNodes.find((n) => n.id === ref.target_id)
        return (
          <div key={ref.target_id} className={styles.nextCard}>
            <div className={styles.nextHead}>
              <span className={styles.nextTitle}>{target?.label ?? ref.target_id}</span>
              <span className={styles.boundMeta}>{ref.target_id}</span>
              <button
                className={styles.removeBtn}
                onClick={() => removeNextNode(ref.target_id)}
                aria-label={`删除指向 ${target?.label ?? ref.target_id}`}
              >
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                  <path d="M18 6 6 18M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className={styles.weightRow}>
              <label className={styles.weightField}>
                预设
                <input
                  type="number"
                  className={styles.weightInput}
                  min={0}
                  max={1}
                  step={0.01}
                  value={ref.preset_weight}
                  onChange={(e) => updateNextNode(ref.target_id, 'preset_weight', e.target.value)}
                />
              </label>
              <label className={styles.weightField}>
                浏览
                <input
                  type="number"
                  className={styles.weightInput}
                  min={0}
                  max={1}
                  step={0.01}
                  value={ref.browse_weight}
                  onChange={(e) => updateNextNode(ref.target_id, 'browse_weight', e.target.value)}
                />
              </label>
              <select
                className={styles.typeSelect}
                value={ref.connection_type}
                onChange={(e) => updateNextNode(ref.target_id, 'connection_type', e.target.value)}
              >
                {CONNECTION_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        )
      })}
      {node.next_nodes.length === 0 && <p className={styles.historyNote}>暂无出向连接</p>}

      {formOpen ? (
        <div className={styles.addForm}>
          <label className={styles.weightField}>
            目标节点
            <select
              className={styles.typeSelect}
              value={targetId}
              onChange={(e) => setTargetId(e.target.value)}
            >
              {candidates.map((n) => (
                <option key={n.id} value={n.id}>
                  {n.label}
                </option>
              ))}
            </select>
          </label>
          <div className={styles.weightRow}>
            <label className={styles.weightField}>
              预设权重
              <input
                type="number"
                className={styles.weightInput}
                min={0}
                max={1}
                step={0.01}
                value={presetWeight}
                onChange={(e) => setPresetWeight(Math.max(0, Math.min(1, Number(e.target.value) || 0)))}
              />
            </label>
            <label className={styles.weightField}>
              浏览权重
              <input
                type="number"
                className={styles.weightInput}
                min={0}
                max={1}
                step={0.01}
                value={browseWeight}
                onChange={(e) => setBrowseWeight(Math.max(0, Math.min(1, Number(e.target.value) || 0)))}
              />
            </label>
            <select
              className={styles.typeSelect}
              value={connType}
              onChange={(e) => setConnType(e.target.value as NextNodeRef['connection_type'])}
            >
              {CONNECTION_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>
          <div className={styles.addFormActions}>
            <Button variant="ghost" size="sm" onClick={() => setFormOpen(false)}>
              取消
            </Button>
            <Button variant="primary" size="sm" onClick={handleConfirm} disabled={!targetId}>
              确认
            </Button>
          </div>
        </div>
      ) : (
        <button className={styles.addBtn} onClick={openForm} disabled={candidates.length === 0}>
          + 添加指向
        </button>
      )}
    </section>
  )
}

export default NextNodeEditor
