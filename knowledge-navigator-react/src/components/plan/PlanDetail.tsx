import React from 'react'
import type { RoutePlan } from '../../utils/routePlanner'
import { getCard } from '../../data/cards'
import styles from './PlanDetail.module.css'

interface PlanDetailProps {
  plan: RoutePlan
}

/** 计划详情：逐站展示节点信息与其绑定认知卡片预览（PL-05） */
const PlanDetail: React.FC<PlanDetailProps> = ({ plan }) => (
  <div className={styles.detail}>
    {plan.sequence.map((node, i) => {
      const boundCards = (node.bound_cards ?? [])
        .map((id) => getCard(id))
        .filter((c): c is NonNullable<typeof c> => Boolean(c))
      return (
        <div key={`${node.id}-${i}`} className={styles.stop}>
          <div className={styles.stopHead}>
            <span className={styles.stopIndex}>{i + 1}</span>
            <span className={styles.stopLabel}>{node.label}</span>
          </div>
          <p className={styles.stopDesc}>{node.description}</p>
          {boundCards.length > 0 && (
            <div className={styles.cards}>
              {boundCards.map((c) => (
                <span key={c.id} className={styles.cardChip}>
                  {c.title}
                </span>
              ))}
            </div>
          )}
        </div>
      )
    })}
    <p className={styles.algorithm}>算法: {plan.algorithm}</p>
  </div>
)

export default PlanDetail
