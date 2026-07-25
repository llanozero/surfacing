import type { TreeNodeData } from '../data/types'

/** 去掉 id 最后一段 "/数字"，得到父级 id。root/1/2 → root/1；root/1 → root */
export function deriveParent(id: string): string {
  const idx = id.lastIndexOf('/')
  if (idx === -1) throw new Error(`invalid id: ${id}`)
  return id.substring(0, idx)
}

export function getTreeChildren(data: TreeNodeData[], parentId: string): TreeNodeData[] {
  return data.filter((n) => deriveParent(n.id) === parentId)
}

export function getTreeNode(data: TreeNodeData[], id: string): TreeNodeData | undefined {
  return data.find((n) => n.id === id)
}

/** 一级卡片（parent 为 root） */
export function getRootNodes(data: TreeNodeData[]): TreeNodeData[] {
  return getTreeChildren(data, 'root')
}

/** 面包屑路径段：root/1/2 → [root, root/1, root/1/2] */
export function getFullPath(data: TreeNodeData[], nodeId: string): { path: string; label: string }[] {
  const parts = nodeId.split('/')
  const result: { path: string; label: string }[] = []
  let cum = ''
  parts.forEach((p, i) => {
    cum = i === 0 ? p : `${cum}/${p}`
    const node = getTreeNode(data, cum)
    result.push({ path: cum, label: node ? node.title : cum })
  })
  return result
}

/** 某节点的所有祖先 id（不含自身） */
export function getAncestorIds(id: string): string[] {
  const ids: string[] = []
  let cur = id
  while (cur.includes('/')) {
    cur = deriveParent(cur)
    if (cur !== 'root') ids.push(cur)
  }
  return ids
}
