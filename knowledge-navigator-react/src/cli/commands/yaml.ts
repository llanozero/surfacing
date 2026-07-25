import { readFileSync, writeFileSync } from 'node:fs'
import type { CommandModule } from '../types'
import { okMsg, errMsg, printJson, unwrap } from '../formatter'
import { flagString } from '../parser'

/** kn-cli yaml — YAML 导入导出 */
export const run: CommandModule['run'] = async (api, args, flags) => {
  const [sub, ...rest] = args
  const json = Boolean(flags.json)

  switch (sub) {
    case 'export': {
      const yaml = api.exportToYAML()
      const file = flagString(flags, 'file')
      if (file) {
        writeFileSync(file, yaml, 'utf-8')
        const cards = api.getAllCards().length
        const nodes = api.getAllNavNodes().length
        return okMsg(`已导出 ${cards} 张认知卡片和 ${nodes} 个导航节点 → ${file}`)
      }
      // 未指定文件：输出到 stdout
      console.log(yaml)
      return
    }
    case 'preview': {
      const raw = readFile(rest[0])
      if (raw === null) return
      const preview = unwrap(api.computeImportPreview(raw))
      if (!preview) return
      if (json) return printJson({ ok: true, data: preview })
      console.log('导入预览：')
      console.log(`  认知卡片: 共 ${preview.cards.total} 张（新增 ${preview.cards.added}，覆盖 ${preview.cards.overwritten}）`)
      console.log(`  导航节点: 共 ${preview.nodes.total} 个（新增 ${preview.nodes.added}，覆盖 ${preview.nodes.overwritten}）`)
      return
    }
    case 'import': {
      const raw = readFile(rest[0])
      if (raw === null) return
      const preview = unwrap(api.importYAML(raw))
      if (!preview) return
      if (json) return printJson({ ok: true, data: preview })
      okMsg(`已导入 ${preview.cards.total} 张认知卡片和 ${preview.nodes.total} 个导航节点`)
      console.log(`  卡片: 新增 ${preview.cards.added}，覆盖 ${preview.cards.overwritten}`)
      console.log(`  节点: 新增 ${preview.nodes.added}，覆盖 ${preview.nodes.overwritten}`)
      return
    }
    case 'validate': {
      const raw = readFile(rest[0])
      if (raw === null) return
      const result = api.parseYAML(raw)
      if (json) return printJson(result.ok ? { ok: true, data: { cards: result.data.cognitive_cards.length, nodes: result.data.navigation_nodes.length } } : result)
      if (!result.ok) return errMsg(`校验未通过：\n${result.error}`)
      okMsg(`YAML 合法：${result.data.cognitive_cards.length} 张卡片，${result.data.navigation_nodes.length} 个节点`)
      return
    }
    default:
      return errMsg(`未知子命令: yaml ${sub ?? ''}（支持 export/preview/import/validate）`)
  }
}

function readFile(path: string | undefined): string | null {
  if (!path) {
    errMsg('缺少文件路径参数')
    return null
  }
  try {
    return readFileSync(path, 'utf-8')
  } catch (e) {
    errMsg(`无法读取文件 ${path}: ${(e as Error).message}`)
    return null
  }
}
