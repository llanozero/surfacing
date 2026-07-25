import React from 'react'
import styles from './SearchBar.module.css'

interface SearchBarProps {
  placeholder: string
  value: string
  onChange: (value: string) => void
  autoFocus?: boolean
}

const SearchBar: React.FC<SearchBarProps> = ({ placeholder, value, onChange, autoFocus }) => (
  <div className={styles.box}>
    <svg
      width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={styles.icon}
    >
      <circle cx="11" cy="11" r="8" /><path d="m21 21-4.3-4.3" />
    </svg>
    <input
      type="text"
      className={styles.input}
      placeholder={placeholder}
      value={value}
      autoFocus={autoFocus}
      onChange={(e) => onChange(e.target.value)}
    />
    {value && (
      <button className={styles.clear} onClick={() => onChange('')} aria-label="清空">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <path d="M18 6 6 18M6 6l12 12" />
        </svg>
      </button>
    )}
  </div>
)

export default SearchBar
