import type { CommandModule } from '../types'
import { okMsg, errMsg, printJson, printLines, succeed } from '../formatter'
import { flagString } from '../parser'
import { useSearchStore } from '../../store/searchStore'

/** kn-cli search — 搜索 */
export const run: CommandModule['run'] = async (api, args, flags) => {
  const [sub, ...rest] = args
  const json = Boolean(flags.json)

  switch (sub) {
    case 'query': {
      const text = rest.join(' ')
      if (!text) return errMsg('用法: search query <text> [--mode keyword|vector]')
      const mode = flagString(flags, 'mode') as 'keyword' | 'vector' | undefined
      if (mode && mode !== 'keyword' && mode !== 'vector') return errMsg('模式必须是 keyword 或 vector')
      const results = await api.search(text, mode)
      if (json) return printJson(results)
      if (results.length === 0) return console.log('无匹配结果')
      console.log(`共 ${results.length} 条匹配（${useSearchStore.getState().matchMode} 模式）：`)
      printLines(results.map((m) => `${m.card.id}  ${m.card.title}  score=${m.score.toFixed(2)}`))
      return
    }
    case 'mode': {
      const [op, value] = rest
      if (op === 'get') return console.log(useSearchStore.getState().matchMode)
      if (op === 'set') {
        if (value !== 'keyword' && value !== 'vector') return errMsg('模式必须是 keyword 或 vector')
        api.setMatchMode(value)
        return okMsg(`匹配模式已切换为 ${value}`)
      }
      return errMsg(`未知子命令: mode ${op ?? ''}（支持 get/set）`)
    }
    case 'results': {
      const results = api.getMatchedCards()
      if (json) return printJson(results)
      printLines(results.map((m) => `${m.card.id}  ${m.card.title}  score=${m.score.toFixed(2)}`), '（当前无匹配结果）')
      return
    }
    case 'select': {
      if (succeed(await api.selectMatchedCard(rest[0]))) okMsg(`已选中卡片 ${rest[0]}`)
      return
    }
    case 'bind-nodes': {
      const nodes = api.getBoundNodesForSelectedCard()
      if (json) return printJson(nodes)
      printLines(nodes.map((n) => `${n.id}  ${n.label}`), '（当前选中卡片无绑定节点）')
      return
    }
    default:
      return errMsg(`未知子命令: search ${sub ?? ''}（支持 query/mode/results/select/bind-nodes）`)
  }
}
