import React from 'react'
import styles from './SearchView.module.css'
import SearchBar from '../shared/SearchBar'
import Button from '../shared/Button'
import ModeToggle from '../search/ModeToggle'
import CardMatchItem from '../search/CardMatchItem'
import BoundNodeItem from '../search/BoundNodeItem'
import { useSearchStore, getSelectedCard, getSelectedNode } from '../../store/searchStore'
import { useNavStore } from '../../store/navStore'
import { useViewStore } from '../../store/viewStore'

const SearchView: React.FC = () => {
  const {
    query, matchedCards, selectedCardId, boundNodes, selectedNodeId,
    matchMode, isVectorLoading, vectorError,
    setQuery, setMatchMode, selectCard, selectNode, retryVectorMatch, enterNav,
  } = useSearchStore()
  const navInit = useNavStore((s) => s.init)
  const switchView = useViewStore((s) => s.switchView)

  const state = useSearchStore.getState()
  const selectedCard = getSelectedCard(state)
  const selectedNode = getSelectedNode(state)

  const handleEnterNav = () => {
    const node = enterNav()
    if (!node) return
    navInit(node.id, 'overview')
    switchView('nav')
  }

  const hasQuery = query.trim().length > 0

  return (
    <div className={styles.view}>
      <div className={styles.header}>
        <h1 className={styles.title}>搜索导航</h1>
        <p className={styles.subtitle}>输入关键词，匹配认知卡片并定位导航节点</p>
      </div>

      <ModeToggle mode={matchMode} onChange={setMatchMode} />

      <SearchBar
        placeholder={matchMode === 'vector' ? '输入自然语言描述，语义匹配语料库...' : '搜索认知卡片...'}
        value={query}
        onChange={setQuery}
        autoFocus
      />

      {/* 向量模式加载态 */}
      {hasQuery && matchMode === 'vector' && isVectorLoading && (
        <div className={styles.loading} role="status">
          <span className={styles.spinner} />
          <span>向量模型匹配中...</span>
        </div>
      )}

      {/* 向量模式错误态 */}
      {hasQuery && matchMode === 'vector' && vectorError && !isVectorLoading && (
        <div className={styles.errorBox}>
          <p className={styles.errorText}>匹配失败: {vectorError}</p>
          <Button variant="outline" size="sm" onClick={retryVectorMatch}>
            重试
          </Button>
        </div>
      )}

      {/* 卡片匹配结果 */}
      {hasQuery && !isVectorLoading && !vectorError && (
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>匹配的认知卡片 ({matchedCards.length})</h2>
          {matchedCards.length > 0 ? (
            <div className={styles.list}>
              {matchedCards.map(({ card, score }) => (
                <CardMatchItem
                  key={card.id}
                  card={card}
                  score={score}
                  isSelected={card.id === selectedCardId}
                  highlight={query}
                  matchMode={matchMode}
                  onClick={() => selectCard(card.id)}
                />
              ))}
            </div>
          ) : (
            <p className={styles.empty}>未找到匹配的认知卡片</p>
          )}
        </section>
      )}

      {/* 绑定导航节点 */}
      {selectedCard && (
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>
            绑定「{selectedCard.title}」的导航节点 ({boundNodes.length})
          </h2>
          {boundNodes.length > 0 ? (
            <div className={styles.list}>
              {boundNodes.map((node) => (
                <BoundNodeItem
                  key={node.id}
                  node={node}
                  isSelected={node.id === selectedNodeId}
                  onClick={() => selectNode(node.id)}
                />
              ))}
            </div>
          ) : (
            <p className={styles.empty}>此卡片暂未绑定任何导航节点</p>
          )}
        </section>
      )}

      {/* 初始空态 */}
      {!hasQuery && (
        <div className={styles.placeholder}>
          <p>输入关键词开始搜索</p>
          <p className={styles.hint}>
            {matchMode === 'vector' ? '支持自然语言描述，按语义相似度匹配' : '支持标题、描述、语料库模糊匹配'}
          </p>
        </div>
      )}

      {/* 底部操作区 */}
      {selectedNode && (
        <div className={styles.bottomAction}>
          <p className={styles.chosen}>
            已选择导航节点: <strong>{selectedNode.label}</strong>
          </p>
          <Button variant="primary" onClick={handleEnterNav}>
            进入导航
          </Button>
        </div>
      )}
    </div>
  )
}

export default SearchView
