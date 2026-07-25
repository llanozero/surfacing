import type { TreeNodeData } from './types'
import { cognitiveCards } from './cards'

/**
 * 树形视图扁平数据 —— 由认知卡片派生（单一数据源）。
 * 嵌套结构由 treeUtils 在渲染时按 id 层级推导。
 */
export const treeData: TreeNodeData[] = cognitiveCards.map((c) => ({
  id: c.id,
  title: c.title,
  type: c.type,
  tag: c.tag,
}))
