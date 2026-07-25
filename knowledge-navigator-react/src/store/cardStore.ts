import { create } from 'zustand'
import type { CognitiveCard } from '../data/types'
import { cognitiveCards } from '../data/cards'
import { allNavNodes } from '../data/allNavNodes'
import { deriveParent } from '../utils/treeUtils'
import { useTreeStore } from './treeStore'
import { useNavNodeStore } from './navNodeStore'

interface CardStore {
  /** 全部认知卡片（与 data/cards 共享数据源，编辑即时同步） */
  allCards: CognitiveCard[]
  /**
   * 新建卡片：parentId 为父文件夹 id，null 表示创建一级卡片。
   * id 按层级路径规则自动生成（同级最大序号 + 1）。
   */
  createCard: (parentId: string | null) => CognitiveCard
  /**
   * 删除卡片：叶子直接删除；文件夹须为空（无子卡片）才可删除。
   * 同时清理所有导航节点 bound_cards 中的引用。
   * 返回失败原因（有子卡片 / 卡片不存在）。
   */
  deleteCard: (id: string) => { ok: boolean; reason?: string }
  updateField: <K extends keyof CognitiveCard>(id: string, field: K, value: CognitiveCard[K]) => void
  addCorpus: (id: string, text: string) => void
  updateCorpus: (id: string, index: number, text: string) => void
  removeCorpus: (id: string, index: number) => void
  addBoundNode: (id: string, nodeId: string) => void
  removeBoundNode: (id: string, nodeId: string) => void
}

/**
 * 将更新后的卡片写回共享数据源：
 * 1. cognitiveCards 数组（搜索匹配、浏览卡片派生等直接读取）
 * 2. treeStore.flatData（树形视图展示 title/tag/type）
 * 当前阶段仅内存生效，YAML 持久化由后续 data-saver 实现。
 */
function commitToSource(updated: CognitiveCard, allCards: CognitiveCard[]) {
  const idx = cognitiveCards.findIndex((c) => c.id === updated.id)
  if (idx >= 0) cognitiveCards[idx] = updated

  const treeStore = useTreeStore.getState()
  useTreeStore.setState({
    flatData: treeStore.flatData.map((n) =>
      n.id === updated.id
        ? { ...n, title: updated.title, type: updated.type, tag: updated.tag }
        : n,
    ),
  })

  return allCards.map((c) => (c.id === updated.id ? updated : c))
}

export const useCardStore = create<CardStore>((set, get) => {
  const mutate = (id: string, fn: (card: CognitiveCard) => CognitiveCard) => {
    const { allCards } = get()
    const card = allCards.find((c) => c.id === id)
    if (!card) return
    set({ allCards: commitToSource(fn(card), allCards) })
  }

  return {
    allCards: cognitiveCards,

    createCard: (parentId) => {
      const { allCards } = get()
      const parent = parentId ?? 'root'
      // 同级最大序号 + 1（data-model.md 层级路径规则）
      const maxIdx = allCards.reduce((m, c) => {
        if (deriveParent(c.id) !== parent) return m
        const seg = Number(c.id.split('/').pop())
        return Number.isFinite(seg) ? Math.max(m, seg) : m
      }, 0)
      const newCard: CognitiveCard = {
        id: parent === 'root' ? `root/${maxIdx + 1}` : `${parent}/${maxIdx + 1}`,
        title: '新建卡片',
        type: 'leaf',
        corpus: [],
        bound_nodes: [],
        metadata: { created_at: new Date().toISOString() },
      }
      // 写回共享数据源
      cognitiveCards.push(newCard)
      set({ allCards: [...allCards, newCard] })
      // 同步树形视图扁平数据
      const treeStore = useTreeStore.getState()
      useTreeStore.setState({
        flatData: [
          ...treeStore.flatData,
          { id: newCard.id, title: newCard.title, type: newCard.type, tag: newCard.tag },
        ],
      })
      return newCard
    },

    deleteCard: (id) => {
      const { allCards } = get()
      const card = allCards.find((c) => c.id === id)
      if (!card) return { ok: false, reason: '卡片不存在' }
      // 文件夹须为空才可删除
      const hasChildren = allCards.some((c) => deriveParent(c.id) === id)
      if (hasChildren) return { ok: false, reason: '文件夹内还有子卡片，请先删除或移出子卡片' }

      // 共享数据源移除
      const idx = cognitiveCards.findIndex((c) => c.id === id)
      if (idx >= 0) cognitiveCards.splice(idx, 1)
      set({ allCards: allCards.filter((c) => c.id !== id) })

      // 清理导航节点 bound_cards 中的引用（原地过滤，所有读取方即时一致）
      allNavNodes.forEach((n) => {
        if (n.bound_cards?.includes(id)) {
          n.bound_cards = n.bound_cards.filter((cid) => cid !== id)
        }
      })
      useNavNodeStore.setState({ allNodes: [...allNavNodes] })

      // 树形视图同步：移除节点 + 清除选中
      const treeStore = useTreeStore.getState()
      useTreeStore.setState({
        flatData: treeStore.flatData.filter((n) => n.id !== id),
        ...(treeStore.selectedId === id ? { selectedId: null } : {}),
      })
      return { ok: true }
    },

    updateField: (id, field, value) => {
      if (field === 'id') return // id 只读
      mutate(id, (c) => ({ ...c, [field]: value }))
    },

    addCorpus: (id, text) => {
      const t = text.trim()
      if (!t) return
      mutate(id, (c) => ({ ...c, corpus: [...c.corpus, t] }))
    },

    updateCorpus: (id, index, text) => {
      mutate(id, (c) => ({
        ...c,
        corpus: c.corpus.map((item, i) => (i === index ? text : item)),
      }))
    },

    removeCorpus: (id, index) => {
      mutate(id, (c) => ({ ...c, corpus: c.corpus.filter((_, i) => i !== index) }))
    },

    addBoundNode: (id, nodeId) => {
      const card = get().allCards.find((c) => c.id === id)
      if (!card || card.bound_nodes?.includes(nodeId)) return // 重复添加忽略
      mutate(id, (c) => ({ ...c, bound_nodes: [...(c.bound_nodes ?? []), nodeId] }))
    },

    removeBoundNode: (id, nodeId) => {
      mutate(id, (c) => ({
        ...c,
        bound_nodes: (c.bound_nodes ?? []).filter((n) => n !== nodeId),
      }))
    },
  }
})

/** 按 id 取当前卡片（派生） */
export function getEditingCard(allCards: CognitiveCard[], id: string | null): CognitiveCard | null {
  return id ? allCards.find((c) => c.id === id) ?? null : null
}
