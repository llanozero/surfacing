import type { CommandModule } from '../types'
import { okMsg, errMsg, printJson, printLines, unwrap, succeed } from '../formatter'
import { flagString } from '../parser'
import { usePlanStore } from '../../store/planStore'

/** 计划摘要行 */
function planLine(p: { id: string; label: string; totalWeight: number; isRecommended?: boolean; sequence: { label: string }[] }): string {
  return `${p.id}  ${p.label}  总权重 ${p.totalWeight.toFixed(2)}${p.isRecommended ? '  [推荐]' : ''}  ${p.sequence.map((n) => n.label).join(' → ')}`
}

/** kn-cli plan — 路线规划 */
export const run: CommandModule['run'] = async (api, args, flags) => {
  const [sub, ...rest] = args
  const json = Boolean(flags.json)

  switch (sub) {
    case 'generate': {
      const ids = flagString(flags, 'ids')?.split(',').map((s) => s.trim()).filter(Boolean)
      const plans = unwrap(await api.generatePlans(ids))
      if (!plans) return
      if (json) return printJson({ ok: true, data: plans })
      okMsg(`已生成 ${plans.length} 个候选计划：`)
      printLines(plans.map(planLine))
      return
    }
    case 'list': {
      const plans = await api.getAllPlans()
      if (json) return printJson(plans)
      printLines(plans.map(planLine), '（尚无候选计划，请先 plan generate）')
      return
    }
    case 'get': {
      const plan = (await api.getAllPlans()).find((p) => p.id === rest[0])
      if (!plan) return errMsg(`计划 ${rest[0] ?? ''} 不存在`)
      if (json) return printJson(plan)
      console.log(planLine(plan))
      console.log(`  算法: ${plan.algorithm}`)
      printLines(plan.sequence.map((n, i) => `${i + 1}. ${n.id}  ${n.label}`))
      return
    }
    case 'select': {
      if (succeed(await api.selectPlan(rest[0]))) okMsg(`已选中计划 ${rest[0]}`)
      return
    }
    case 'recommend': {
      const plan = await api.getRecommendedPlan()
      if (json) return printJson(plan ?? null)
      if (!plan) return console.log('（无推荐计划）')
      console.log(planLine(plan))
      return
    }
    case 'mode': {
      const [kind, value] = rest
      if (kind === 'get') {
        const { waypointMode, weightMode } = usePlanStore.getState()
        const data = { waypointMode, weightMode }
        if (json) return printJson(data)
        console.log(`  waypointMode: ${waypointMode}`)
        console.log(`  weightMode: ${weightMode}`)
        return
      }
      if (kind === 'waypoint') {
        if (value !== 'ordered' && value !== 'unordered') return errMsg('途经点模式必须是 ordered 或 unordered')
        api.setWaypointMode(value)
        return okMsg(`途经点模式已设置为 ${value}`)
      }
      if (kind === 'weight') {
        if (value !== 'mixed' && value !== 'user_only') return errMsg('权重模式必须是 mixed 或 user_only')
        api.setWeightMode(value)
        return okMsg(`权重模式已设置为 ${value}`)
      }
      return errMsg(`未知子命令: mode ${kind ?? ''}（支持 get/waypoint/weight）`)
    }
    case 'replan': {
      await api.replan()
      const plans = await api.getAllPlans()
      if (json) return printJson({ ok: true, data: plans })
      okMsg(`已重新规划，共 ${plans.length} 个候选计划`)
      return
    }
    default:
      return errMsg(`未知子命令: plan ${sub ?? ''}（支持 generate/list/get/select/recommend/mode/replan）`)
  }
}
