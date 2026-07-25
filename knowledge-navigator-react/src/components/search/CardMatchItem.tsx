import React from 'react'
import type { CognitiveCard } from '../../data/types'
import type { MatchMode } from '../../store/searchStore'
import styles from './CardMatchItem.module.css'

interface CardMatchItemProps {
  card: CognitiveCard
  score: number
  isSelected: boolean
  highlight: string
  matchMode?: MatchMode
  onClick: () => void
}

/** 高亮与 query 匹配的文本片段 */
export function Highlight({ text, query }: { text: string; query: string }) {
  const q = query.trim()
  if (!q) return <>{text}</>
  const idx = text.toLowerCase().indexOf(q.toLowerCase())
  if (idx === -1) return <>{text}</>
  return (
    <>
      {text.slice(0, idx)}
      <mark className={styles.mark}>{text.slice(idx, idx + q.length)}</mark>
      {text.slice(idx + q.length)}
    </>
  )
}

const CardMatchItem: React.FC<CardMatchItemProps> = ({ card, score, isSelected, highlight, matchMode = 'keyword', onClick }) => (
  <button className={`${styles.item} ${isSelected ? styles.selected : ''}`} onClick={onClick}>
    <span className={styles.icon}>
      {card.type === 'folder' ? (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
        </svg>
      ) : (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
          <polyline points="14 2 14 8 20 8" />
        </svg>
      )}
    </span>
    <span className={styles.body}>
      <span className={styles.title}>
        <Highlight text={card.title} query={highlight} />
        {card.tag && <span className={styles.tag}>{card.tag}</span>}
      </span>
      <span className={styles.desc}>
        <Highlight text={card.description ?? card.corpus[0] ?? ''} query={highlight} />
      </span>
    </span>
    <span className={`${styles.score} ${matchMode === 'vector' ? styles.scoreVector : ''}`}>
      {matchMode === 'vector' ? '~' : ''}{Math.round(score * 100)}%
    </span>
  </button>
)

export default CardMatchItem
