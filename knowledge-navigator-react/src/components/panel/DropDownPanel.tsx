import React from 'react'
import styles from './DropDownPanel.module.css'
import Button from '../shared/Button'
import TtsButton from '../shared/TtsButton'
import { usePanelStore, type PanelPosition } from '../../store/panelStore'
import { useNavStore } from '../../store/navStore'
import { useNavNodeStore } from '../../store/navNodeStore'
import { useGraphStore } from '../../store/graphStore'
import { useViewStore } from '../../store/viewStore'
import { useToastStore } from '../shared/Toast'
import { useDragPanel } from '../../hooks/useDragPanel'
import { getCard } from '../../data/cards'
import { getNavNode } from '../../data/allNavNodes'

/** 尺寸按钮配置 */
const SIZE_BTNS: { pos: PanelPosition; label: string; title: string }[] = [
  { pos: 'collapsed', label: '📄', title: '隐藏' },
  { pos: 'half', label: '⊞', title: '半屏' },
  { pos: 'full', label: '⛶', title: '全屏' },
]

/**
 * 下拉面板（仅 NavView 内嵌）。
 * 三段停靠：收起 85% / 半屏 50% / 全屏 0，拖拽手柄吸附。
 */
const DropDownPanel: React.FC = () => {
  const { node, position, hidden, setPosition } = usePanelStore()
  const addWaypoint = useNavStore((s) => s.addWaypoint)
  const toast = useToastStore((s) => s.show)

  const { panelRef, currentPct, dragging, onDragStart } = useDragPanel(
    position,
    setPosition,
    node !== null,
  )

  if (!node || hidden) return null

  // 检查是否为引用节点（聚合画布数据中的 _nodeType 标记）
  const nodeAny = node as any
  const isRef = nodeAny._nodeType === 'ref' || node.type === 'ref'
  const isSubgraph = nodeAny._nodeType === 'subgraph' || node.type === 'subgraph'
  const sourceGraphLabel = nodeAny._sourceGraphLabel || ''
  const sourceGraphId = nodeAny._sourceGraphId || ''
  const sourceNodeId = nodeAny._sourceNodeId || ''

  const handleAddWaypoint = () => {
    addWaypoint(node)
    toast(`已添加途径点: ${node.label}`)
    setPosition('collapsed')
  }

  // 跳转到管理视图并选中此节点（spec §6.1）
  const handleEditNode = () => {
    useNavNodeStore.getState().selectNode(node.id)
    useNavNodeStore.getState().setActiveSubTab('nodes')
    useViewStore.getState().switchView('tree')
  }

  /** 跳转到引用节点的源图 */
  const handleJumpToSource = () => {
    if (sourceGraphId) {
      useGraphStore.getState().setActiveGraph(sourceGraphId)
      toast(`已切换到「${sourceGraphLabel || sourceGraphId}」`)
    }
  }

  const boundCards = (node.bound_cards ?? [])
    .map((id) => getCard(id))
    .filter((c): c is NonNullable<typeof c> => Boolean(c))
  const nextNodes = node.next_nodes
    .map((e) => ({ ref: e, node: getNavNode(e.target_id) }))
    .filter((x) => x.node)

  return (
    <div
      ref={panelRef}
      className={`${styles.panel} ${dragging ? styles.dragging : ''}`}
      style={{ transform: `translateY(${currentPct}%)` }}
    >
      <div
        className={styles.handleZone}
        onTouchStart={onDragStart}
        onMouseDown={onDragStart}
      >
        <div className={styles.handle} />
      </div>

      {position === 'collapsed' ? (
        <div className={styles.collapsed}>
          <div className={styles.sizeBar}>
            {SIZE_BTNS.map((b) => (
              <button
                key={b.pos}
                className={position === b.pos ? styles.sizeBtnActive : styles.sizeBtn}
                title={b.title}
                onClick={() => setPosition(b.pos)}
              >
                {b.label}
              </button>
            ))}
          </div>
          <span className={styles.collapsedLabel}>
            {isRef && '↻ '}
            {isSubgraph && '📂 '}
            {node.label}
          </span>
          <Button variant="primary" size="sm" onClick={handleAddWaypoint}>
            添加为途径点
          </Button>
        </div>
      ) : (
        <div className={styles.content}>
          <div className={styles.head}>
            <div className={styles.headRow}>
              <h3 className={styles.nodeLabel}>
                {isRef && <span className={styles.refIcon} title="引用节点">↻ </span>}
                {isSubgraph && <span className={styles.subIcon} title="子图节点">📂 </span>}
                {node.label}
              </h3>
              <div className={styles.sizeBar}>
                {SIZE_BTNS.map((b) => (
                  <button
                    key={b.pos}
                    className={position === b.pos ? styles.sizeBtnActive : styles.sizeBtn}
                    title={b.title}
                    onClick={() => setPosition(b.pos)}
                  >
                    {b.label}
                  </button>
                ))}
              </div>
              {node.description && <TtsButton text={node.description} size="sm" />}
            </div>
            {isRef && sourceGraphLabel && (
              <p className={styles.sourceInfo}>
                来自 <strong>{sourceGraphLabel}</strong>
                {sourceNodeId && <> · {sourceNodeId}</>}
              </p>
            )}
            <p className={styles.nodeDesc}>{node.description}</p>
            <div className={styles.stats}>
              <span className={styles.stat}>绑定卡片 {boundCards.length}</span>
              <span className={styles.stat}>出向连接 {node.next_nodes.length}</span>
            </div>
          </div>

          {position === 'full' && (
            <div className={styles.expanded}>
              {boundCards.length > 0 && (
                <section className={styles.panelSection}>
                  <h4 className={styles.sectionTitle}>绑定的认知卡片</h4>
                  {boundCards.map((c) => (
                    <div key={c.id} className={styles.row}>
                      <span className={styles.rowMain}>{c.title}</span>
                      <span className={styles.rowMeta}>{c.id}</span>
                    </div>
                  ))}
                </section>
              )}
              {nextNodes.length > 0 && (
                <section className={styles.panelSection}>
                  <h4 className={styles.sectionTitle}>下一节点</h4>
                  {nextNodes.map(({ ref, node: n }) => (
                    <div key={ref.target_id} className={styles.row}>
                      <span className={styles.rowMain}>{n!.label}</span>
                      <span className={styles.rowMeta}>
                        预设 {ref.preset_weight.toFixed(2)} · 浏览 {ref.browse_weight.toFixed(2)}
                      </span>
                    </div>
                  ))}
                </section>
              )}
            </div>
          )}

          <div className={styles.actions}>
            {isRef && sourceGraphId && (
              <Button variant="outline" onClick={handleJumpToSource}>
                跳转到源图「{sourceGraphLabel || sourceGraphId}」
              </Button>
            )}
            <Button variant="primary" onClick={handleAddWaypoint}>
              添加为途径点
            </Button>
            <Button variant="outline" onClick={handleEditNode}>
              编辑节点
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}

export default DropDownPanel
