/** CLI 输出格式化：文本（默认）/ JSON（--json） */

import type { ApiResult } from '../api/index'

export type Flags = Record<string, string | boolean>

/** 打印成功信息 */
export function okMsg(msg: string): void {
  console.log(`✓ ${msg}`)
}

/** 打印错误信息并设置非零退出码 */
export function errMsg(msg: string): void {
  console.error(`✗ ${msg}`)
  process.exitCode = 1
}

/** 按模式打印数据（JSON 或缩进 JSON 文本） */
export function printJson(data: unknown): void {
  console.log(JSON.stringify(data, null, 2))
}

/**
 * 解开 ApiResult：成功返回 data，失败打印错误并返回 undefined。
 * 调用方对 undefined 直接 return 即可。
 */
export function unwrap<T>(result: ApiResult<T>): T | undefined {
  if (result.ok) return result.data
  errMsg(result.error)
  return undefined
}

/** 用于 ApiResult<void>：成功返回 true，失败打印错误并返回 false */
export function succeed(result: ApiResult<unknown>): boolean {
  if (result.ok) return true
  errMsg(result.error)
  return false
}

/** 打印列表：每行一项 */
export function printLines(lines: string[], emptyHint = '（无）'): void {
  if (lines.length === 0) {
    console.log(`  ${emptyHint}`)
    return
  }
  for (const line of lines) console.log(`  ${line}`)
}
