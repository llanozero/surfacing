import type { CommandModule } from '../types'
import { okMsg, errMsg, printJson, printLines, unwrap, succeed } from '../formatter'
import { flagString, flagInt } from '../parser'
import { weightToPriority } from '../../utils/quickConnectUtils'

/** kn-cli node — 导航节点管理 */
export const run: CommandModule['run'] = async (api, args, flags) => {
  const [sub, ...rest] = args
  const json = Boolean(flags.json)

  switch (sub) {
    case 'list': {
      const query = flagString(flags, 'query')
      const nodes = query ? api.searchNavNodes(query) : api.getAllNavNodes()
      if (json) return printJson(nodes)
      console.log(`共 ${nodes.length} 个节点：`)
      printLines(nodes.map((n) => `${n.id}  ${n.label}  (${n.next_nodes.length} 出口)`))
      return
    }
    case 'get': {
      const node = rest[0] ? api.getNavNode(rest[0]) : undefined
      if (!node) return errMsg(`节点 ${rest[0] ?? ''} 不存在`)
      if (json) return printJson(node)
      console.log(`${node.id}  ${node.label}`)
      if (node.description) console.log(`  description: ${node.description}`)
      if (node.bound_cards?.length) console.log(`  bound_cards: ${node.bound_cards.join(', ')}`)
      printLines(
        node.next_nodes.map((e) => `→ ${e.target_id}  #${weightToPriority(e.preset_weight)}  [${e.connection_type}]`),
        '（无出向连接）',
      )
      return
    }
    case 'create': {
      const result = unwrap(api.createNavNode())
      if (!result) return
      const label = flagString(flags, 'label')
      if (label) api.updateNavNodeField(result.id, 'label', label)
      const node = api.getNavNode(result.id)!
      if (json) return printJson({ ok: true, data: node })
      okMsg(`已创建节点 ${node.id}（${node.label}）`)
      return
    }
    case 'delete': {
      if (succeed(api.deleteNavNode(rest[0]))) okMsg(`已删除节点 ${rest[0]}（引用已级联清理）`)
      return
    }
    case 'update': {
      const [id, field, ...valueParts] = rest
      const value = valueParts.join(' ')
      if (!id || !field || !value) return errMsg('用法: node update <id> <field> <value>')
      if (succeed(api.updateNavNodeField(id, field, value))) okMsg(`已更新 ${id} 的 ${field}`)
      return
    }
    case 'bind': {
      const [op, id, cardId] = rest
      if (op === 'list') {
        const node = api.getNavNode(id)
        if (!node) return errMsg(`节点 ${id} 不存在`)
        const cards = node.bound_cards ?? []
        if (json) return printJson(cards)
        return printLines(cards, '（未绑定认知卡片）')
      }
      if (!id || !cardId) return errMsg(`用法: node bind ${op ?? ''} <nodeId> <cardId>`)
      if (op === 'add') {
        if (succeed(api.addNavNodeBoundCard(id, cardId))) okMsg(`已绑定 ${id} → ${cardId}`)
        return
      }
      if (op === 'remove') {
        if (succeed(api.removeNavNodeBoundCard(id, cardId))) okMsg(`已解绑 ${id} → ${cardId}`)
        return
      }
      return errMsg(`未知子命令: bind ${op}`)
    }
    case 'next': {
      const [op, ...vals] = rest
      if (op === 'list') {
        const items = api.getNextNodes(vals[0])
        if (json) return printJson(items)
        return printLines(
          items.map((x) => `→ ${x.node.id}  ${x.node.label}  #${weightToPriority(x.ref.preset_weight)}  w=${x.ref.weight.toFixed(2)}`),
          '（无出向连接）',
        )
      }
      if (op === 'add') {
        const [fromId, toId] = vals
        if (!fromId || !toId) return errMsg('用法: node next add <fromId> <toId> [--priority <n>] [--type <t>]')
        const result = api.addNextNodeRef(fromId, {
          target_id: toId,
          preset_priority: flagInt(flags, 'priority'),
          connection_type: flagString(flags, 'type') as 'preset' | 'browse_derived' | 'user_added' | undefined,
        })
        if (succeed(result)) okMsg(`已添加连接 ${fromId} → ${toId}`)
        return
      }
      if (op === 'update') {
        const [fromId, toId, field, value] = vals
        if (!fromId || !toId || !field || value === undefined) {
          return errMsg('用法: node next update <fromId> <toId> <preset_priority|browse_priority|connection_type> <value>')
        }
        const updates =
          field === 'connection_type'
            ? { connection_type: value as 'preset' | 'browse_derived' | 'user_added' }
            : { [field]: Number(value) }
        if (succeed(api.updateNextNodeRef(fromId, toId, updates))) okMsg(`已更新连接 ${fromId} → ${toId} 的 ${field}`)
        return
      }
      if (op === 'remove') {
        if (succeed(api.removeNextNodeRef(vals[0], vals[1]))) okMsg(`已删除连接 ${vals[0]} → ${vals[1]}`)
        return
      }
      if (op === 'status') {
        const result = api.getConnectionStatus(vals[0], vals[1])
        if (json) return printJson(result)
        if (result.status === 'connected' && result.ref) {
          console.log(`✓ 已连接 · 优先级 #${weightToPriority(result.ref.preset_weight)} · ${result.ref.connection_type}`)
        } else if (result.status === 'missing') {
          console.log('✚ 缺失连接（可新建）')
        } else {
          console.log('⚠ 节点不可用')
        }
        return
      }
      return errMsg(`未知子命令: next ${op ?? ''}（支持 list/add/update/remove/status）`)
    }
    case 'prev': {
      const items = api.getPrevNodes(rest[0])
      if (json) return printJson(items.map((x) => x.node))
      printLines(items.map((x) => `${x.node.id}  ${x.node.label}`), '（无前驱节点）')
      return
    }
    case 'generate': {
      const [kind, id] = rest
      if (!id) return errMsg('用法: node generate <label|desc> <id>')
      const result = kind === 'label' ? await api.generateNodeLabel(id) : kind === 'desc' ? await api.generateNodeDescription(id) : null
      if (!result) return errMsg(`未知生成类型: ${kind}（支持 label / desc）`)
      const text = unwrap(result)
      if (!text) return
      if (json) return printJson({ ok: true, data: text })
      okMsg(`生成结果：${text}`)
      return
    }
    default:
      return errMsg(`未知子命令: node ${sub ?? ''}（支持 list/get/create/delete/update/bind/next/prev/generate）`)
  }
}
