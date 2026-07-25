import React from 'react'
import styles from './NavCanvas.module.css'

/**
 * 统一画布容器 —— D3 实例由父级 NavView 通过 useNavCanvas 管理，
 * 本组件只提供挂载节点。
 */
const NavCanvas = React.forwardRef<HTMLDivElement>((_props, ref) => (
  <div ref={ref} className={styles.canvas} />
))

NavCanvas.displayName = 'NavCanvas'
export default NavCanvas
