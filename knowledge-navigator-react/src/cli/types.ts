import type { KnowledgeNavigatorAPI } from '../api/index'
import type { Flags } from './formatter'

/** 命令模块统一签名 */
export interface CommandModule {
  run: (api: KnowledgeNavigatorAPI, args: string[], flags: Flags) => Promise<void>
}
