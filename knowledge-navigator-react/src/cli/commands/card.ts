import type { CommandModule } from '../types'
import { okMsg, errMsg, printJson, printLines, unwrap, succeed } from '../formatter'
import { flagString } from '../parser'

/** kn-cli card — 认知卡片管理 */
export const run: CommandModule['run'] = async (api, args, flags) => {
  const [sub, ...rest] = args
  const json = Boolean(flags.json)

  switch (sub) {
    case 'list': {
      const cards = api.getAllCards()
      if (json) return printJson(cards)
      console.log(`共 ${cards.length} 张卡片：`)
      printLines(cards.map((c) => `${c.id}  ${c.title}  [${c.type}]${c.tag ? `  #${c.tag}` : ''}`))
      return
    }
    case 'get': {
      const card = rest[0] ? api.getCard(rest[0]) : undefined
      if (!card) return errMsg(`卡片 ${rest[0] ?? ''} 不存在`)
      if (json) return printJson(card)
      console.log(`${card.id}  ${card.title}  [${card.type}]`)
      if (card.tag) console.log(`  tag: ${card.tag}`)
      if (card.description) console.log(`  description: ${card.description}`)
      printLines(card.corpus.map((t, i) => `corpus[${i}]: ${t}`), '（暂无语料）')
      if (card.bound_nodes?.length) console.log(`  bound_nodes: ${card.bound_nodes.join(', ')}`)
      return
    }
    case 'create': {
      const result = unwrap(api.createCard(flagString(flags, 'parent')))
      if (!result) return
      const title = flagString(flags, 'title')
      const type = flagString(flags, 'type') as 'folder' | 'leaf' | undefined
      if (title) api.updateCardField(result.id, 'title', title)
      if (type) api.updateCardField(result.id, 'type', type)
      const card = api.getCard(result.id)!
      if (json) return printJson({ ok: true, data: card })
      okMsg(`已创建卡片 ${card.id}`)
      console.log(`  title: "${card.title}"`)
      console.log(`  type: ${card.type}`)
      return
    }
    case 'delete': {
      if (succeed(api.deleteCard(rest[0]))) okMsg(`已删除卡片 ${rest[0]}`)
      return
    }
    case 'update': {
      const [id, field, ...valueParts] = rest
      const value = valueParts.join(' ')
      if (!id || !field || !value) return errMsg('用法: card update <id> <field> <value>')
      if (succeed(api.updateCardField(id, field, value))) okMsg(`已更新 ${id} 的 ${field}`)
      return
    }
    case 'corpus': {
      const [op, id, ...vals] = rest
      if (!id) return errMsg('用法: card corpus <list|add|update|remove> <id> ...')
      if (op === 'list') {
        const card = api.getCard(id)
        if (!card) return errMsg(`卡片 ${id} 不存在`)
        if (json) return printJson(card.corpus)
        return printLines(card.corpus.map((t, i) => `[${i}] ${t}`), '（暂无语料）')
      }
      if (op === 'add') {
        if (succeed(api.addCardCorpus(id, vals.join(' ')))) okMsg(`已为 ${id} 添加语料`)
        return
      }
      if (op === 'update') {
        const [index, ...text] = vals
        if (succeed(api.updateCardCorpus(id, Number(index), text.join(' ')))) okMsg(`已更新 ${id} 的语料[${index}]`)
        return
      }
      if (op === 'remove') {
        if (succeed(api.removeCardCorpus(id, Number(vals[0])))) okMsg(`已删除 ${id} 的语料[${vals[0]}]`)
        return
      }
      return errMsg(`未知子命令: corpus ${op}`)
    }
    case 'bind': {
      const [op, id, nodeId] = rest
      if (op === 'list') {
        const card = api.getCard(id)
        if (!card) return errMsg(`卡片 ${id} 不存在`)
        const nodes = card.bound_nodes ?? []
        if (json) return printJson(nodes)
        return printLines(nodes, '（未绑定导航节点）')
      }
      if (!id || !nodeId) return errMsg(`用法: card bind ${op ?? ''} <cardId> <nodeId>`)
      if (op === 'add') {
        if (succeed(api.addCardBoundNode(id, nodeId))) okMsg(`已绑定 ${id} → ${nodeId}`)
        return
      }
      if (op === 'remove') {
        if (succeed(api.removeCardBoundNode(id, nodeId))) okMsg(`已解绑 ${id} → ${nodeId}`)
        return
      }
      return errMsg(`未知子命令: bind ${op}`)
    }
    case 'children': {
      const children = api.getChildCards(rest[0])
      if (json) return printJson(children)
      printLines(children.map((c) => `${c.id}  ${c.title}  [${c.type}]`), '（无子卡片）')
      return
    }
    case 'generate': {
      const [kind, id] = rest
      if (!id) return errMsg('用法: card generate <title|desc> <id>')
      const result = kind === 'title' ? await api.generateCardTitle(id) : kind === 'desc' ? await api.generateCardDescription(id) : null
      if (!result) return errMsg(`未知生成类型: ${kind}（支持 title / desc）`)
      const text = unwrap(result)
      if (!text) return
      if (json) return printJson({ ok: true, data: text })
      okMsg(`生成结果：${text}`)
      return
    }
    default:
      return errMsg(`未知子命令: card ${sub ?? ''}（支持 list/get/create/delete/update/corpus/bind/children/generate）`)
  }
}
