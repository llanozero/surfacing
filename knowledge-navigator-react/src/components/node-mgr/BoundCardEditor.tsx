import React, { useState } from 'react'
import type { NavNode } from '../../data/types'
import { getCard, cognitiveCards } from '../../data/cards'
import { useNavNodeStore } from '../../store/navNodeStore'
import { useToastStore } from '../shared/Toast'
import NodeSelector from './NodeSelector'
import styles from './NodeMgr.module.css'

interface BoundCardEditorProps {
  node: NavNode
}

/** 绑定认知卡片管理（NM-06 添加 / NM-07 移除） */
const BoundCardEditor: React.FC<BoundCardEditorProps> = ({ node }) => {
  const { addBoundCard, removeBoundCard } = useNavNodeStore()
  const toast = useToastStore((s) => s.show)
  const [selectorOpen, setSelectorOpen] = useState(false)

  const bound = (node.bound_cards ?? [])
    .map((id) => ({ id, card: getCard(id) }))
    .filter((x) => x.card)

  const candidates = cognitiveCards
    .filter((c) => !node.bound_cards?.includes(c.id))
    .map((c) => ({ id: c.id, label: c.title, meta: c.id }))

  return (
    <section className={styles.section}>
      <h4 className={styles.sectionTitle}>绑定认知卡片 ({bound.length})</h4>
      {bound.map(({ id, card }) => (
        <div key={id} className={styles.boundRow}>
          <span className={styles.boundMain}>{card!.title}</span>
          <span className={styles.boundMeta}>{id}</span>
          <button
            className={styles.removeBtn}
            onClick={() => removeBoundCard(id)}
            aria-label={`移除绑定 ${card!.title}`}
          >
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
              <path d="M18 6 6 18M6 6l12 12" />
            </svg>
          </button>
        </div>
      ))}
      {bound.length === 0 && <p className={styles.historyNote}>暂未绑定任何认知卡片</p>}

      <button className={styles.addBtn} onClick={() => setSelectorOpen(true)}>
        + 添加
      </button>

      {selectorOpen && (
        <NodeSelector
          title="绑定认知卡片"
          items={candidates}
          onSelect={(id) => {
            addBoundCard(id)
            setSelectorOpen(false)
            toast('已添加绑定卡片')
          }}
          onClose={() => setSelectorOpen(false)}
        />
      )}
    </section>
  )
}

export default BoundCardEditor
