import React, { useState } from 'react'
import type { RoutePlan } from '../../utils/routePlanner'
import PlanDetail from './PlanDetail'
import ConnectionIndicator from '../nav/ConnectionIndicator'
import ConnectionEditPopover from '../nav/ConnectionEditPopover'
import { useToastStore } from '../shared/Toast'
import {
  ensureQuickConnection,
  updateQuickConnection,
  removeQuickConnection,
  getConnectionStatus,
} from '../../utils/quickConnectUtils'
import { getNavNode } from '../../data/allNavNodes'
import styles from './PlanCard.module.css'

interface PlanCardProps {
  plan: RoutePlan
  isSelected: boolean
  onSelect: () => void
}

const CIRCLED = ['①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧', '⑨', '⑩']

const PlanCard: React.FC<PlanCardProps> = ({ plan, isSelected, onSelect }) => {
  const [detailOpen, setDetailOpen] = useState(false)
  const [editingConn, setEditingConn] = useState<{ fromId: string; toId: string } | null>(null)
  const toast = useToastStore((s) => s.show)

  /** QC-05：在计划序列中一键新建连接 */
  const handleQuickConnect = (fromId: string, toId: string) => {
    const created = ensureQuickConnection(fromId, toId)
    toast(created ? '已建立跳转连接' : '连接已存在')
  }

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
            {i > 0 && (
              <span onClick={(e) => e.stopPropagation()}>
                <ConnectionIndicator
                  fromId={plan.sequence[i - 1].id}
                  toId={node.id}
                  onConnect={handleQuickConnect}
                  onEdit={(f, t) => setEditingConn({ fromId: f, toId: t })}
                />
              </span>
            )}
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

      {/* 连接编辑浮层（QC-06） */}
      {editingConn &&
        (() => {
          const { status, ref } = getConnectionStatus(editingConn.fromId, editingConn.toId)
          const fromNode = getNavNode(editingConn.fromId)
          const toNode = getNavNode(editingConn.toId)
          if (status !== 'connected' || !ref || !fromNode || !toNode) return null
          return (
            <ConnectionEditPopover
              fromId={editingConn.fromId}
              toId={editingConn.toId}
              fromLabel={fromNode.label}
              toLabel={toNode.label}
              initialRef={ref}
              onSave={(f, t, updates) => {
                updateQuickConnection(f, t, updates)
                toast('已更新跳转连接')
              }}
              onDelete={(f, t) => {
                removeQuickConnection(f, t)
                toast('已删除跳转连接')
              }}
              onClose={() => setEditingConn(null)}
            />
          )
        })()}
    </div>
  )
}

export default PlanCard
