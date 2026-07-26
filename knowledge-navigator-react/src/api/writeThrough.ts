import { BackendAdapter } from './BackendAdapter'
import { isRemoteMode } from '../config/backend'
import type { CognitiveCard, NavNode } from '../data/types'

/**
 * 远程模式写透传：store 本地变更完成后，把同一变更异步同步到后端。
 * 策略为「本地优先 + 火忘（fire-and-forget）」——UI 立即生效，
 * 后端失败仅 console.warn（下次水合时以后端为准）。
 * 更新一律 PUT 完整实体（去掉只读 id），后端按字段覆盖并持久化 YAML；
 * 删除由后端处理级联清理。
 */

function report(op: string, e: unknown): void {
  console.warn(`[remote-write] ${op} 同步后端失败：`, e)
}

/** 新建卡片 → POST /api/cards */
export function wtCreateCard(card: CognitiveCard): void {
  if (!isRemoteMode()) return
  void BackendAdapter.getInstance()
    .post('/api/cards', card)
    .catch((e) => report('新建卡片', e))
}

/** 卡片任意字段变更（标题/标签/语料/绑定节点等）→ PUT /api/cards/{id} */
export function wtUpdateCard(card: CognitiveCard): void {
  if (!isRemoteMode()) return
  const { id, ...fields } = card
  void BackendAdapter.getInstance()
    .put(`/api/cards/${id}`, fields)
    .catch((e) => report(`更新卡片 ${id}`, e))
}

/** 删除卡片 → DELETE /api/cards/{id}（后端级联清理节点 bound_cards） */
export function wtDeleteCard(id: string): void {
  if (!isRemoteMode()) return
  void BackendAdapter.getInstance()
    .delete(`/api/cards/${id}`)
    .catch((e) => report(`删除卡片 ${id}`, e))
}

/** 新建节点 → POST /api/nodes */
export function wtCreateNode(node: NavNode): void {
  if (!isRemoteMode()) return
  void BackendAdapter.getInstance()
    .post('/api/nodes', node)
    .catch((e) => report('新建节点', e))
}

/** 节点任意字段变更（标签/描述/绑定卡片/出向连接等）→ PUT /api/nodes/{id} */
export function wtUpdateNode(node: NavNode): void {
  if (!isRemoteMode()) return
  const { id, ...fields } = node
  void BackendAdapter.getInstance()
    .put(`/api/nodes/${id}`, fields)
    .catch((e) => report(`更新节点 ${id}`, e))
}

/** 删除节点 → DELETE /api/nodes/{id}（后端级联清理连接与卡片绑定） */
export function wtDeleteNode(id: string): void {
  if (!isRemoteMode()) return
  void BackendAdapter.getInstance()
    .delete(`/api/nodes/${id}`)
    .catch((e) => report(`删除节点 ${id}`, e))
}
