import type { CommandModule } from '../types'
import { okMsg, errMsg, printJson, printLines, succeed } from '../formatter'
import { useNavStore } from '../../store/navStore'

/** kn-cli nav — 导航图操作 */
export const run: CommandModule['run'] = async (api, args, flags) => {
  const [group, op, ...rest] = args
  const json = Boolean(flags.json)

  switch (group) {
    case 'graph': {
      if (op === 'nodes') {
        const nodes = api.getAllNavNodes()
        if (json) return printJson(nodes)
        return printLines(nodes.map((n) => `${n.id}  ${n.label}`))
      }
      if (op === 'edges') {
        const edges = api.getAllEdges()
        if (json) return printJson(edges)
        console.log(`共 ${edges.length} 条有向边：`)
        return printLines(edges.map((e) => `${e.source} → ${e.target}  w=${e.weight}`))
      }
      if (op === 'sync') {
        api.syncGraphFromSource()
        return okMsg('已从数据源重算图')
      }
      return errMsg(`未知子命令: graph ${op ?? ''}（支持 nodes/edges/sync）`)
    }
    case 'current': {
      if (op === 'get') {
        const current = api.getNavNode(useNavStore.getState().currentNodeId)
        if (json) return printJson(current ?? null)
        return console.log(current ? `${current.id}  ${current.label}` : '（未设置）')
      }
      if (op === 'set') {
        if (!rest[0] || !api.getNavNode(rest[0])) return errMsg(`节点 ${rest[0] ?? ''} 不存在`)
        api.setCurrentNode(rest[0])
        return okMsg(`当前中心节点已设置为 ${rest[0]}`)
      }
      return errMsg(`未知子命令: current ${op ?? ''}（支持 get/set）`)
    }
    case 'mode': {
      if (op === 'get') return console.log(useNavStore.getState().mode)
      if (op === 'set') {
        if (rest[0] !== 'overview' && rest[0] !== 'station') return errMsg('模式必须是 overview 或 station')
        api.setNavMode(rest[0])
        return okMsg(`导航模式已切换为 ${rest[0]}`)
      }
      return errMsg(`未知子命令: mode ${op ?? ''}（支持 get/set）`)
    }
    case 'waypoint': {
      if (op === 'list') {
        const wps = api.getWaypoints()
        if (json) return printJson(wps)
        return printLines(wps.map((w, i) => `${i + 1}. ${w.id}  ${w.label}`), '（无途经点）')
      }
      if (op === 'add') {
        if (succeed(api.addWaypoint(rest[0]))) okMsg(`已添加途经点 ${rest[0]}`)
        return
      }
      if (op === 'remove') {
        api.removeWaypoint(Number(rest[0]))
        return okMsg(`已移除途经点 #${rest[0]}`)
      }
      if (op === 'clear') {
        api.clearWaypoints()
        return okMsg('已清空途经点')
      }
      if (op === 'fill') {
        const count = api.fillAllMissingConnections(api.getWaypoints().map((w) => w.id))
        return okMsg(count > 0 ? `已建立 ${count} 条跳转连接` : '所有相邻途经点均已连接')
      }
      return errMsg(`未知子命令: waypoint ${op ?? ''}（支持 list/add/remove/clear/fill）`)
    }
    case 'next': {
      const items = api.getWeightedNextNodes(op)
      if (json) return printJson(items)
      return printLines(
        items.map((r) => `→ ${r.target_id}  seq=${r.seq}  w=${r.weight.toFixed(2)}  [${r.source}]`),
        '（无后继节点）',
      )
    }
    case 'prev': {
      const items = api.getPrevNodes(op)
      if (json) return printJson(items.map((x) => x.node))
      return printLines(items.map((x) => `${x.node.id}  ${x.node.label}`), '（无前驱节点）')
    }
    default:
      return errMsg(`未知子命令: nav ${group ?? ''}（支持 graph/current/mode/waypoint/next/prev）`)
  }
}
