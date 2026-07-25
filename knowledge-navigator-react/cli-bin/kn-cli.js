#!/usr/bin/env node
/**
 * kn-cli 全局命令入口。
 * 通过 tsx 直接运行 TypeScript 源码（src/cli/index.ts），无需预编译。
 */
import { spawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const here = dirname(fileURLToPath(import.meta.url))
const entry = join(here, '..', 'src', 'cli', 'index.ts')

const result = spawnSync(process.execPath, ['--import', 'tsx', entry, ...process.argv.slice(2)], {
  stdio: 'inherit',
  cwd: join(here, '..'),
})

process.exit(result.status ?? 1)
