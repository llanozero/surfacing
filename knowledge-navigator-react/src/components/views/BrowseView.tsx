import React from 'react'
import styles from './BrowseView.module.css'
import Button from '../shared/Button'
import CardStack from '../cards/CardStack'
import SwipeHint from '../cards/SwipeHint'
import { useBrowseStore } from '../../store/browseStore'
import { useViewStore } from '../../store/viewStore'
import { useToastStore } from '../shared/Toast'

const BrowseView: React.FC = () => {
  const { waypoints, wpIndex, cards, currentIndex, nextCard, prevCard, nextWaypoint } =
    useBrowseStore()
  const switchView = useViewStore((s) => s.switchView)
  const toast = useToastStore((s) => s.show)

  const currentWaypoint = waypoints[wpIndex]

  if (waypoints.length === 0) {
    return (
      <div className={styles.view}>
        <div className={styles.emptyState}>
          <p className={styles.emptyTitle}>尚未规划浏览路线</p>
          <p className={styles.emptyHint}>先在「导航」视图中添加途径点，再点击「开始浏览」</p>
          <Button variant="outline" size="sm" onClick={() => switchView('nav')}>
            前往导航
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.view}>
      <div className={styles.topBar}>
        <button className={styles.back} onClick={() => switchView('nav')}>
          ← 返回
        </button>
        <span className={styles.progress}>
          第 {wpIndex + 1}/{waypoints.length} 站 · {currentIndex + 1}/{Math.max(cards.length, 1)}
        </span>
        <span className={styles.wpLabel}>{currentWaypoint?.label}</span>
      </div>

      {currentIndex > 0 && <SwipeHint direction="down" />}

      {cards.length > 0 ? (
        <CardStack
          cards={cards}
          currentIndex={currentIndex}
          onPrev={prevCard}
          onNext={nextCard}
        />
      ) : (
        <div className={styles.emptyState}>
          <p className={styles.emptyTitle}>「{currentWaypoint?.label}」暂无绑定卡片</p>
          <p className={styles.emptyHint}>可直接前往下一站</p>
        </div>
      )}

      {currentIndex < cards.length - 1 && <SwipeHint direction="up" />}

      <div className={styles.bottomBar}>
        <Button variant="ghost" size="sm" onClick={() => toast('已收藏')}>
          收藏
        </Button>
        {wpIndex < waypoints.length - 1 ? (
          <Button variant="outline" size="sm" onClick={nextWaypoint}>
            下一站: {waypoints[wpIndex + 1].label}
          </Button>
        ) : (
          <Button variant="outline" size="sm" onClick={() => toast('已是最后一站')}>
            已到终点
          </Button>
        )}
      </div>
    </div>
  )
}

export default BrowseView
