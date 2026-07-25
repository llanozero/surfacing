import type { CommandModule } from '../types'
import { okMsg, errMsg, printJson, printLines, succeed } from '../formatter'
import { flagString } from '../parser'

/** kn-cli browse — 浏览操作 */
export const run: CommandModule['run'] = async (api, args, flags) => {
  const [sub] = args
  const json = Boolean(flags.json)

  switch (sub) {
    case 'start': {
      const planId = flagString(flags, 'plan')
      const sequence = flagString(flags, 'sequence')
      if (planId) {
        if (succeed(await api.initBrowseFromPlan(planId))) okMsg(`已从计划 ${planId} 开始浏览`)
        return
      }
      if (sequence) {
        const ids = sequence.split(',').map((s) => s.trim()).filter(Boolean)
        if (succeed(await api.initBrowseFromSequence(ids))) okMsg(`已从节点序列开始浏览（${ids.length} 站）`)
        return
      }
      // 默认：当前选中的计划
      const selected = await api.getSelectedPlan()
      if (!selected) return errMsg('请先选中一个计划（plan select / --plan / --sequence）')
      if (succeed(await api.initBrowseFromPlan(selected.id))) okMsg(`已从当前计划 ${selected.id} 开始浏览`)
      return
    }
    case 'status': {
      const progress = await api.getBrowseProgress()
      if (json) return printJson(progress)
      console.log(`  站点: ${progress.waypointIndex + 1} / ${progress.totalWaypoints}`)
      console.log(`  卡片: ${progress.cardIndex + 1} / ${progress.totalCards}`)
      return
    }
    case 'cards': {
      const cards = await api.getCurrentBrowseCards()
      if (json) return printJson(cards)
      printLines(cards.map((c, i) => `[${i}] ${c.title}${c.tag ? `  #${c.tag}` : ''}  ${c.desc.slice(0, 40)}`), '（无浏览卡片，请先 browse start）')
      return
    }
    case 'next': {
      if (succeed(await api.nextCard())) okMsg('已切换到下一张卡片')
      return
    }
    case 'prev': {
      if (succeed(await api.prevCard())) okMsg('已切换到上一张卡片')
      return
    }
    case 'waypoint': {
      if (succeed(await api.nextWaypoint())) okMsg('已切换到下一站')
      return
    }
    default:
      return errMsg(`未知子命令: browse ${sub ?? ''}（支持 start/status/cards/next/prev/waypoint）`)
  }
}
