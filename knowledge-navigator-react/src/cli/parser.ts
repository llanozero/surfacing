/** CLI 参数解析：位置参数 + --flag value / --boolean-flag */

export interface ParsedArgs {
  _: string[]
  flags: Record<string, string | boolean>
}

/** 已知布尔标志（不消费后续值） */
const BOOLEAN_FLAGS = new Set(['json', 'help', 'version'])

export function parseArgs(argv: string[]): ParsedArgs {
  const _: string[] = []
  const flags: Record<string, string | boolean> = {}

  for (let i = 0; i < argv.length; i++) {
    const token = argv[i]
    if (token.startsWith('--')) {
      const key = token.slice(2)
      if (BOOLEAN_FLAGS.has(key)) {
        flags[key] = true
      } else if (i + 1 < argv.length && !argv[i + 1].startsWith('--')) {
        flags[key] = argv[++i]
      } else {
        flags[key] = true
      }
    } else {
      _.push(token)
    }
  }
  return { _, flags }
}

export function flagString(flags: Record<string, string | boolean>, key: string): string | undefined {
  const v = flags[key]
  return typeof v === 'string' ? v : undefined
}

export function flagInt(flags: Record<string, string | boolean>, key: string): number | undefined {
  const v = flagString(flags, key)
  if (v === undefined) return undefined
  const n = Number(v)
  return Number.isFinite(n) ? Math.round(n) : undefined
}
