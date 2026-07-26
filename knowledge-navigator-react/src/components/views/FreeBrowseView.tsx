import React, { useCallback, useState } from 'react'
import styles from './FreeBrowseView.module.css'
import Button from '../shared/Button'
import TtsButton from '../shared/TtsButton'
import CardStack from '../cards/CardStack'
import SwipeHint from '../cards/SwipeHint'
import { useBrowseStore, type BranchNodeItem } from '../../store/browseStore'
import { useNavStore } from '../../store/navStore'
import { useViewStore } from '../../store/viewStore'
import { useToastStore } from '../shared/Toast'
import { getNavNode } from '../../data/allNavNodes'

const FreeBrowseView: React.FC = () => {
  const {
    freeNodeId,
    freeCards,
    freePrevNodes,
    freeNextNodes,
    jumpToNode,
    exitFreeBrowse,
  } = useBrowseStore()
  const setCurrentNode = useNavStore((s) => s.setCurrentNode)
  const addWaypoint = useNavStore((s) => s.addWaypoint)
  const switchView = useViewStore((s) => s.switchView)
  const toast = useToastStore((s) => s.show)

  const [cardIndex, setCardIndex] = useState(0)
  const currentNode = freeNodeId ? getNavNode(freeNodeId) : null

  const handleExit = useCallback(() => {
    exitFreeBrowse()
    switchView('nav')
  }, [exitFreeBrowse, switchView])

  const handleJump = useCallback(
    (targetId: string) => {
      jumpToNode(targetId)
      setCurrentNode(targetId)
      setCardIndex(0)
    },
    [jumpToNode, setCurrentNode],
  )

  const handleAddWaypoint = useCallback(() => {
    if (!currentNode) return
    addWaypoint(currentNode)
    toast(`已添加「${currentNode.label}」为途经点`)
  }, [currentNode, addWaypoint, toast])

  const handleSetCurrentNode = useCallback(() => {
    if (!currentNode) return
    setCurrentNode(currentNode.id)
    toast(`当前节点已设为「${currentNode.label}」`)
  }, [currentNode, setCurrentNode, toast])

  if (!currentNode) {
    return (
      <div className={styles.view}>
        <div className={styles.topBar}>
          <button className={styles.back} onClick={handleExit}>
            ← 返回导航
          </button>
        </div>
        <div className={styles.emptyState}>
          <p className={styles.emptyTitle}>没有当前节点</p>
          <p className={styles.emptyHint}>请先在导航界面选择一个节点</p>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.view}>
      <div className={styles.topBar}>
        <button className={styles.back} onClick={handleExit}>
          ← 返回导航
        </button>
        <span className={styles.nodeLabel}>{currentNode.label}</span>
        <span className={styles.spacer} />
      </div>

      {/* 节点标题与描述 */}
      <div className={styles.nodeHeader}>
        <div className={styles.nodeTitleRow}>
          <h2 className={styles.nodeTitle}>{currentNode.label}</h2>
          <TtsButton
            text={(currentNode.description
              ? `${currentNode.label}。${currentNode.description}`
              : currentNode.label)}
            size="md"
          />
        </div>
        {currentNode.description && (
          <p className={styles.nodeDesc}>{currentNode.description}</p>
        )}
      </div>

      {/* 关联卡片 */}
      {freeCards.length > 0 ? (
        <div className={styles.cardsSection}>
          <div className={styles.sectionLabel}>关联卡片</div>
          {cardIndex > 0 && <SwipeHint direction="down" />}
          <CardStack
            cards={freeCards}
            currentIndex={cardIndex}
            onPrev={() => setCardIndex((i) => Math.max(0, i - 1))}
            onNext={() => setCardIndex((i) => Math.min(freeCards.length - 1, i + 1))}
          />
          {cardIndex < freeCards.length - 1 && <SwipeHint direction="up" />}
          <div className={styles.cardCounter}>
            {cardIndex + 1} / {freeCards.length}
          </div>
        </div>
      ) : (
        <div className={styles.noCards}>
          「{currentNode.label}」暂无绑定卡片
        </div>
      )}

      {/* 分支跳转 */}
      <div className={styles.branchArea}>
        <BranchSection
          title="前驱节点"
          items={freePrevNodes}
          onJump={handleJump}
          emptyText="没有前驱节点（此节点无入向连接）"
        />
        <BranchSection
          title="后继节点"
          items={freeNextNodes}
          onJump={handleJump}
          emptyText="没有后继节点（此节点无出向连接）"
        />
      </div>

      {/* 底部操作栏 */}
      <div className={styles.bottomBar}>
        <Button variant="outline" size="sm" onClick={handleAddWaypoint}>
          添加为途经点
        </Button>
        <Button variant="outline" size="sm" onClick={handleSetCurrentNode}>
          设为当前节点
        </Button>
      </div>
    </div>
  )
}

/* ─── 分支节点子组件 ─── */

const BranchSection: React.FC<{
  title: string
  items: BranchNodeItem[]
  onJump: (id: string) => void
  emptyText: string
}> = ({ title, items, onJump, emptyText }) => (
  <div className={styles.branchSection}>
    <div className={styles.branchTitle}>{title}</div>
    {items.length === 0 ? (
      <div className={styles.branchEmpty}>{emptyText}</div>
    ) : (
      items.map((item) => (
        <button
          key={item.node.id}
          className={styles.branchItem}
          onClick={() => onJump(item.node.id)}
        >
          <span className={styles.branchLabel}>{item.node.label}</span>
          <span className={styles.branchWeight}>w {item.weight.toFixed(2)}</span>
        </button>
      ))
    )}
  </div>
)

export default FreeBrowseView
