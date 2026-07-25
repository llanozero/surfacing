import type { CommandModule } from '../types'
import { okMsg, errMsg, printJson, printLines } from '../formatter'

/** kn-cli tree — 树形管理 */
export const run: CommandModule['run'] = async (api, args, flags) => {
  const [sub, ...rest] = args
  const json = Boolean(flags.json)

  switch (sub) {
    case 'list': {
      const roots = await api.getRootNodes()
      if (json) return printJson(roots)
      printLines(roots.map((n) => `${n.id}  ${n.title}  [${n.type}]`))
      return
    }
    case 'children': {
      const children = await api.getTreeChildren(rest[0])
      if (json) return printJson(children)
      printLines(children.map((n) => `${n.id}  ${n.title}  [${n.type}]`), '（无子节点）')
      return
    }
    case 'path': {
      const path = await api.getTreePath(rest[0])
      if (json) return printJson(path)
      console.log(path.map((p) => p.label).join(' / '))
      return
    }
    case 'select': {
      if (!rest[0]) return errMsg('用法: tree select <id>')
      api.selectTreeNode(rest[0])
      return okMsg(`已选中树节点 ${rest[0]}`)
    }
    case 'expand': {
      if (!rest[0]) return errMsg('用法: tree expand <id>')
      api.expandTreeAncestors(rest[0])
      return okMsg(`已展开 ${rest[0]} 的所有祖先节点`)
    }
    case 'toggle': {
      if (!rest[0]) return errMsg('用法: tree toggle <id>')
      api.toggleTreeNode(rest[0])
      return okMsg(`已切换 ${rest[0]} 的展开状态`)
    }
    case 'search': {
      const query = rest.join(' ')
      if (!query) return errMsg('用法: tree search <query>')
      api.searchTree(query)
      const q = query.toLowerCase()
      const matched = (await api.getTreeFlatData()).filter((n) => n.title.toLowerCase().includes(q))
      if (json) return printJson(matched)
      printLines(matched.map((n) => `${n.id}  ${n.title}  [${n.type}]`), '无匹配结果')
      return
    }
    default:
      return errMsg(`未知子命令: tree ${sub ?? ''}（支持 list/children/path/select/expand/toggle/search）`)
  }
}
