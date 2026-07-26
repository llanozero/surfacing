import { KnowledgeNavigatorAPI } from '../api/index'
import { initBackendConfig } from '../config/backend'
import { parseArgs } from './parser'
import { errMsg } from './formatter'
import type { CommandModule } from './types'
import * as card from './commands/card'
import * as node from './commands/node'
import * as nav from './commands/nav'
import * as plan from './commands/plan'
import * as browse from './commands/browse'
import * as search from './commands/search'
import * as tree from './commands/tree'
import * as yaml from './commands/yaml'
import * as view from './commands/view'
import * as help from './commands/help'

const VERSION = '0.1.0'

const COMMANDS: Record<string, CommandModule> = {
  card,
  node,
  nav,
  plan,
  browse,
  search,
  tree,
  yaml,
  view,
  help,
}

/** 命令执行器：解析 argv → 分发到命令模块 */
export async function main(argv: string[] = process.argv.slice(2)): Promise<void> {
  const { _, flags } = parseArgs(argv)
  const cmd = _[0]

  if (flags.version) {
    console.log(`kn-cli ${VERSION}`)
    return
  }

  if (!cmd || flags.help) {
    await help.run(null as never, cmd ? [cmd] : [], flags)
    return
  }

  const mod = COMMANDS[cmd]
  if (!mod) {
    errMsg(`未知命令: ${cmd}`)
    console.error(`可用命令: ${Object.keys(COMMANDS).join(', ')}（kn-cli help 查看详情）`)
    return
  }

  // 读取 KN_BACKEND_MODE / KN_BACKEND_URL 环境变量（pro 模式（完整模式）走 HTTP 后端）
  initBackendConfig()

  const api = new KnowledgeNavigatorAPI()
  await mod.run(api, _.slice(1), flags)
}
