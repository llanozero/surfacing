import type { CommandModule } from '../types'
import { okMsg, errMsg } from '../formatter'
import { useViewStore, type ViewName } from '../../store/viewStore'

const VALID_VIEWS: ViewName[] = ['search', 'nav', 'plan', 'browse', 'tree']

/** kn-cli view — 视图切换 */
export const run: CommandModule['run'] = async (api, args) => {
  const [sub, value] = args

  if (sub === 'get') {
    console.log(useViewStore.getState().activeView)
    return
  }
  if (sub === 'set') {
    if (!VALID_VIEWS.includes(value as ViewName)) {
      return errMsg(`视图必须是: ${VALID_VIEWS.join(' | ')}`)
    }
    api.switchView(value as ViewName)
    return okMsg(`已切换到 ${value} 视图`)
  }
  return errMsg(`未知子命令: view ${sub ?? ''}（支持 get/set）`)
}
