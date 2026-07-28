/** 活动导航图配置（localStorage 持久化）。 */

const STORAGE_KEY = 'kn_active_graph'

let _activeGraphId = 'g1'

export function getActiveGraphId(): string {
  return _activeGraphId
}

export function setActiveGraphId(id: string): void {
  _activeGraphId = id
  try {
    localStorage.setItem(STORAGE_KEY, id)
  } catch {
    /* 存储不可用时忽略 */
  }
}

/** 初始化：从 localStorage 恢复 */
export function initGraphConfig(): void {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) _activeGraphId = saved
  } catch {
    /* 忽略 */
  }
}

/** 解析跨图引用，返回 { graphId, resourceId }；无前缀时默认属于当前活动图。 */
export function parseGraphRef(ref: string): { graphId: string; resourceId: string } {
  if (ref.includes('::')) {
    const [graphId, ...rest] = ref.split('::')
    return { graphId, resourceId: rest.join('::') }
  }
  return { graphId: _activeGraphId, resourceId: ref }
}

/** 构建跨图引用字符串 */
export function buildGraphRef(graphId: string, resourceId: string): string {
  return `${graphId}::${resourceId}`
}

/** 跨图节点/卡片带来源图的轻量包装 */
export interface CrossGraphResource<T> {
  data: T
  graphId: string
  graphLabel: string
}

/** 全量聚合模式特殊 ID */
export const CANVAS_ALL_GRAPH_ID = '__all__'

/** 顶层虚拟图 ID（面包屑根路径） */
export const TOP_GRAPH_ID = 'top'

/** 构建命名空间化 ID："{graph_id}::{node_id}" */
export function nsId(graphId: string, nodeId: string): string {
  return `${graphId}::${nodeId}`
}

/** 解析命名空间化 ID（兼容不带前缀的旧格式） */
export function parseNsId(id: string): { graphId: string | null; nodeId: string } {
  if (id.includes('::')) {
    const [graphId, ...rest] = id.split('::')
    return { graphId, nodeId: rest.join('::') }
  }
  return { graphId: null, nodeId: id }
}
