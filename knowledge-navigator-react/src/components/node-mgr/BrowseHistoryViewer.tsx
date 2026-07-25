import React from 'react'
import type { NavNode } from '../../data/types'
import { getNavNode } from '../../data/allNavNodes'
import { formatDate } from '../../utils/format'
import styles from './NodeMgr.module.css'

interface BrowseHistoryViewerProps {
  node: NavNode
}

/** 浏览记录只读查看（NM-12）：按 last_at 倒序 */
const BrowseHistoryViewer: React.FC<BrowseHistoryViewerProps> = ({ node }) => {
  const history = [...(node.browse_history ?? [])].sort(
    (a, b) => new Date(b.last_at).getTime() - new Date(a.last_at).getTime(),
  )
  const total = history.reduce((sum, h) => sum + h.count, 0)

  return (
    <section className={styles.section}>
      <h4 className={styles.sectionTitle}>
        浏览记录{history.length > 0 ? ` (共 ${total} 次)` : ''}
      </h4>
      {history.length > 0 ? (
        <>
          {history.map((h) => (
            <div key={h.from} className={styles.historyRow}>
              <span className={styles.boundMain}>
                来自: {getNavNode(h.from)?.label ?? h.from}
              </span>
              <span className={styles.boundMeta}>
                {h.count} 次 · 最后 {formatDate(h.last_at)}
              </span>
            </div>
          ))}
          <p className={styles.historyNote}>浏览记录由用户行为自动生成</p>
        </>
      ) : (
        <p className={styles.historyNote}>暂无浏览记录</p>
      )}
    </section>
  )
}

export default BrowseHistoryViewer
