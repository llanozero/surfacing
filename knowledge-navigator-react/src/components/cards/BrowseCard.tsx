import React, { useState } from 'react'
import type { BrowseCard as BrowseCardData } from '../../data/types'
import TtsButton from '../shared/TtsButton'
import styles from './BrowseCard.module.css'

interface BrowseCardProps {
  data: BrowseCardData
  /** 堆叠层级：0 为顶层活跃卡片 */
  layer: 0 | 1 | 2
}

const BrowseCard: React.FC<BrowseCardProps> = ({ data, layer }) => {
  const [corpusOpen, setCorpusOpen] = useState(false)

  if (layer === 2) {
    return (
      <div className={`${styles.card} ${styles.layer2}`}>
        <div className={styles.barDim} />
        <div className={styles.body}>
          <h3 className={styles.titleDim}>{data.title}</h3>
          <p className={styles.descDim}>{data.desc.slice(0, 60)}...</p>
        </div>
      </div>
    )
  }

  if (layer === 1) {
    return (
      <div className={`${styles.card} ${styles.layer1}`}>
        <div className={styles.barMid} />
        <div className={styles.body}>
          <h3 className={styles.titleMid}>{data.title}</h3>
          <p className={styles.descMid}>{data.desc}</p>
        </div>
      </div>
    )
  }

  return (
    <div className={`${styles.card} ${styles.layer0}`}>
      <div className={styles.bar} />
      <div className={styles.bodyScroll}>
        <div className={styles.titleRow}>
          <h2 className={styles.title}>{data.title}</h2>
          <TtsButton text={`${data.title}。${data.desc}`} size="sm" />
        </div>
        <p className={styles.desc}>{data.desc}</p>

        <div className={styles.chips}>
          {data.tag && <span className={styles.chipAccent}>{data.tag}</span>}
          <span className={styles.chip}>权重 {data.weight.toFixed(2)}</span>
          <span className={styles.chip}>语料 {data.cards} 段</span>
        </div>

        <button className={styles.corpusToggle} onClick={() => setCorpusOpen((v) => !v)}>
          {corpusOpen ? '收起语料库' : `展开语料库 (${data.corpus.length})`}
          <svg
            width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor"
            strokeWidth="2" style={{ transform: corpusOpen ? 'rotate(90deg)' : 'none', transition: 'transform .2s' }}
          >
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </button>

        {corpusOpen && (
          <div className={styles.corpus}>
            {data.corpus.map((c, i) => (
              <p key={i} className={styles.corpusItem}>{c}</p>
            ))}
          </div>
        )}

        {data.related.length > 0 && (
          <div className={styles.related}>
            <h4 className={styles.relatedTitle}>关联节点</h4>
            <div className={styles.relatedList}>
              {data.related.map((r, i) => (
                <span
                  key={i}
                  className={r.pos === '前置' ? styles.relatedPrev : styles.relatedNext}
                >
                  {r.pos} · {r.name}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default BrowseCard
