import React, { useRef } from 'react'
import type { BrowseCard as BrowseCardData } from '../../data/types'
import BrowseCard from './BrowseCard'
import { useCardSwipe } from '../../hooks/useCardSwipe'
import styles from './CardStack.module.css'

interface CardStackProps {
  cards: BrowseCardData[]
  currentIndex: number
  onPrev: () => void
  onNext: () => void
}

const CardStack: React.FC<CardStackProps> = ({ cards, currentIndex, onPrev, onNext }) => {
  const stackRef = useRef<HTMLDivElement>(null)
  useCardSwipe(stackRef, onNext, onPrev)

  return (
    <div ref={stackRef} className={styles.stack}>
      {currentIndex + 2 < cards.length && (
        <BrowseCard key={`${currentIndex + 2}-${cards[currentIndex + 2].title}`} data={cards[currentIndex + 2]} layer={2} />
      )}
      {currentIndex + 1 < cards.length && (
        <BrowseCard key={`${currentIndex + 1}-${cards[currentIndex + 1].title}`} data={cards[currentIndex + 1]} layer={1} />
      )}
      {cards[currentIndex] && (
        <BrowseCard key={`${currentIndex}-${cards[currentIndex].title}`} data={cards[currentIndex]} layer={0} />
      )}
    </div>
  )
}

export default CardStack
