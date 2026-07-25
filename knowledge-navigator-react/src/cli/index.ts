import { main } from './runner'

main().catch((e: unknown) => {
  console.error('✗', e instanceof Error ? e.message : e)
  process.exitCode = 1
})
