import React from 'react'
import styles from './DropDownPanel.module.css'
import Button from '../shared/Button'
import { usePanelStore } from '../../store/panelStore'
import { useNavStore } from '../../store/navStore'
import { useNavNodeStore } from '../../store/navNodeStore'
import { useViewStore } from '../../store/viewStore'
import { useToastStore } from '../shared/Toast'
import { useDragPanel } from '../../hooks/useDragPanel'
import { getCard } from '../../data/cards'
import { getNavNode } from '../../data/allNavNodes'

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
          <span className={styles.collapsedLabel}>{node.label}</span>
          <Button variant="primary" size="sm" onClick={handleAddWaypoint}>
            添加为途径点
          </Button>
        </div>
      ) : (
        <div className={styles.content}>
          <div className={styles.head}>
            <h3 className={styles.nodeLabel}>{node.label}</h3>
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
