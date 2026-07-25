import React from 'react'
import NodeList from './NodeList'
import NodeEditPanel from './NodeEditPanel'
import styles from './NodeMgr.module.css'

/**
 * 导航节点管理主容器。
 * 移动端（产品基准 < 480px）：列表在上、编辑面板在下（NM-布局适配）。
 */
const NodeManagementView: React.FC = () => (
  <div className={styles.container}>
    <NodeList />
    <NodeEditPanel />
  </div>
)

export default NodeManagementView
