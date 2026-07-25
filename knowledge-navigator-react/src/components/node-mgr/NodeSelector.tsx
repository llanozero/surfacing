import React, { useState } from 'react'
import SearchBar from '../shared/SearchBar'
import styles from './NodeMgr.module.css'

export interface SelectorItem {
  id: string
  label: string
  meta?: string
}

interface NodeSelectorProps {
  title: string
  items: SelectorItem[]
  onSelect: (id: string) => void
  onClose: () => void
}

/** 搜索式选择弹窗（NM-06：认知卡片选择器） */
const NodeSelector: React.FC<NodeSelectorProps> = ({ title, items, onSelect, onClose }) => {
  const [query, setQuery] = useState('')
  const q = query.trim().toLowerCase()
  const filtered = q
    ? items.filter((i) => i.label.toLowerCase().includes(q) || i.id.toLowerCase().includes(q))
    : items

  return (
    <div className={styles.selectorMask} onClick={onClose}>
      <div className={styles.selector} onClick={(e) => e.stopPropagation()}>
        <h3 className={styles.selectorTitle}>{title}</h3>
        <SearchBar placeholder="搜索..." value={query} onChange={setQuery} autoFocus />
        <div className={styles.selectorList}>
          {filtered.length > 0 ? (
            filtered.map((item) => (
              <button
                key={item.id}
                className={styles.selectorItem}
                onClick={() => onSelect(item.id)}
              >
                <span className={styles.selectorItemLabel}>{item.label}</span>
                {item.meta && <span className={styles.selectorItemMeta}>{item.meta}</span>}
              </button>
            ))
          ) : (
            <p className={styles.listEmpty}>无匹配项</p>
          )}
        </div>
      </div>
    </div>
  )
}

export default NodeSelector
