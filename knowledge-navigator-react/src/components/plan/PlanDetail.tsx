import React, { useState } from 'react'
import type { NavNode, NextNodeRef } from '../../data/types'
import type { RoutePlan } from '../../utils/routePlanner'
import { getCard } from '../../data/cards'
import { useToastStore } from '../shared/Toast'
import {
  getConnectionStatus,
  weightToPriority,
  ensureQuickConnection,
  updateQuickConnection,
  removeQuickConnection,
} from '../../utils/quickConnectUtils'
import styles from './PlanDetail.module.css'

interface PlanDetailProps {
  plan: RoutePlan
}

const TYPE_OPTIONS: { value: NextNodeRef['connection_type']; label: string }[] = [
  { value: 'preset', label: 'preset' },
  { value: 'user_added', label: 'user_added' },
  { value: 'browse_derived', label: 'browse_derived' },
]

/** 单条连接的编辑行：已连接可改优先级/类型/删除，缺失可一键新建 */
const ConnectionRow: React.FC<{ from: NavNode; to: NavNode }> = ({ from, to }) => {
  const toast = useToastStore((s) => s.show)
  const { status, ref } = getConnectionStatus(from.id, to.id)
  const [priority, setPriority] = useState<number>(ref ? weightToPriority(ref.preset_weight) : 1)
  const [connType, setConnType] = useState<NextNodeRef['connection_type']>(
    ref?.connection_type ?? 'user_added',
  )

  if (status === 'missing') {
    return (
      <div className={styles.connRow}>
        <span className={styles.connTitle}>
          {from.label} → {to.label}
        </span>
        <button
          className={styles.connCreate}
          onClick={() => {
            const created = ensureQuickConnection(from.id, to.id)
            toast(created ? '已建立跳转连接' : '连接已存在')
          }}
        >
          ✚ 新建连接
        </button>
      </div>
    )
  }

  if (status !== 'connected' || !ref) return null

  return (
    <div className={styles.connRow}>
      <span className={styles.connTitle}>
        {from.label} → {to.label}
      </span>
      <div className={styles.connFields}>
        <label className={styles.connField}>
          优先级
          <input
            className={styles.connInput}
            type="number"
            min={1}
            step={1}
            value={priority}
            onChange={(e) => setPriority(Math.max(1, Math.round(Number(e.target.value) || 1)))}
          />
        </label>
        <label className={styles.connField}>
          类型
          <select
            className={styles.connSelect}
            value={connType}
            onChange={(e) => setConnType(e.target.value as NextNodeRef['connection_type'])}
          >
            {TYPE_OPTIONS.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </label>
        <button
          className={styles.connSave}
          onClick={() => {
            updateQuickConnection(from.id, to.id, { preset_priority: priority, connection_type: connType })
            toast('已更新跳转连接')
          }}
        >
          保存
        </button>
        <button
          className={styles.connDelete}
          onClick={() => {
            removeQuickConnection(from.id, to.id)
            toast('已删除跳转连接')
          }}
        >
          删除
        </button>
      </div>
    </div>
  )
}

/** 计划详情：逐站展示节点信息与绑定卡片预览（PL-05）+ 相邻连接编辑面板（QC-06） */
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

    {/* 连接编辑面板：逐对相邻节点 */}
    <div className={styles.connPanel}>
      <span className={styles.connPanelTitle}>连接操作</span>
      {plan.sequence.slice(0, -1).map((node, i) => (
        <ConnectionRow
          key={`${node.id}->${plan.sequence[i + 1].id}-${i}`}
          from={node}
          to={plan.sequence[i + 1]}
        />
      ))}
    </div>

    <p className={styles.algorithm}>算法: {plan.algorithm}</p>
  </div>
)

export default PlanDetail
