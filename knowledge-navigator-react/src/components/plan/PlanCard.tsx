import React, { useState } from 'react'
import type { RoutePlan } from '../../utils/routePlanner'
import PlanDetail from './PlanDetail'
import styles from './PlanCard.module.css'

interface PlanCardProps {
  plan: RoutePlan
  isSelected: boolean
  onSelect: () => void
}

const CIRCLED = ['①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧', '⑨', '⑩']

const PlanCard: React.FC<PlanCardProps> = ({ plan, isSelected, onSelect }) => {
  const [detailOpen, setDetailOpen] = useState(false)

  return (
    <div
      className={`${styles.card} ${isSelected ? styles.selected : ''}`}
      onClick={onSelect}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onSelect()}
    >
      <div className={styles.head}>
        <span className={`${styles.radio} ${isSelected ? styles.radioOn : ''}`} />
        <span className={styles.label}>{plan.label}</span>
        <span className={styles.weight}>总权重: {plan.totalWeight.toFixed(2)}</span>
        {plan.isRecommended && <span className={styles.badge}>推荐</span>}
      </div>

      <div className={styles.sequence}>
        {plan.sequence.map((node, i) => (
          <React.Fragment key={`${node.id}-${i}`}>
            {i > 0 && <span className={styles.arrow}>→</span>}
            <span className={styles.seqNode}>
              <span className={styles.seqIndex}>{CIRCLED[i] ?? `${i + 1}.`}</span>
              {node.label}
            </span>
          </React.Fragment>
        ))}
      </div>

      <button
        className={styles.detailToggle}
        onClick={(e) => {
          e.stopPropagation()
          setDetailOpen((v) => !v)
        }}
      >
        {detailOpen ? '收起详情 ⌃' : '查看详情 >'}
      </button>

      {detailOpen && <PlanDetail plan={plan} />}
    </div>
  )
}

export default PlanCard
