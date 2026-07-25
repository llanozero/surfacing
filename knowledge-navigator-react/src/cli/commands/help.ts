import type { CommandModule } from '../types'

const GENERAL_HELP = `kn-cli — Knowledge Navigator 命令行工具

用法: kn-cli <command> [subcommand] [options] [arguments]

命令组:
  card      认知卡片管理（list/get/create/delete/update/corpus/bind/children/generate）
  node      导航节点管理（list/get/create/delete/update/bind/next/prev/generate）
  nav       导航图操作（graph/current/mode/waypoint/next/prev）
  plan      路线规划（generate/list/get/select/recommend/mode/replan）
  browse    浏览操作（start/status/cards/next/prev/waypoint）
  search    搜索（query/mode/results/select/bind-nodes）
  tree      树形管理（list/children/path/select/expand/toggle/search）
  yaml      YAML 导入导出（export/preview/import/validate）
  view      视图切换（get/set）
  help      查看帮助

全局选项:
  --json      输出 JSON 格式（供程序解析）
  --help      显示帮助
  --version   显示版本号

示例:
  kn-cli card list --json
  kn-cli node next add node-a node-b --priority 1
  kn-cli nav waypoint fill
  kn-cli plan generate --ids node-a,node-b,node-c
  kn-cli yaml export --file ./backup.yaml
  kn-cli search query "神经网络" --mode vector
`

const GROUP_HELP: Record<string, string> = {
  card: `kn-cli card — 认知卡片管理
  card list [--json]                       列出所有卡片
  card get <id> [--json]                   查看单张卡片
  card create [--parent <id>] [--title <t>] [--type <folder|leaf>]
  card delete <id>                         删除卡片（文件夹须为空）
  card update <id> <field> <value>         更新字段（title/description/tag/type）
  card corpus list|add|update|remove ...   语料库管理
  card bind list|add|remove ...            绑定导航节点
  card children <id>                       列出子卡片
  card generate title|desc <id>            AI 生成标题/描述`,
  node: `kn-cli node — 导航节点管理
  node list [--query <q>]                  列出节点（可搜索）
  node get <id>                            查看单个节点
  node create [--label <l>]                新建节点
  node delete <id>                         删除节点（级联清理引用）
  node update <id> <field> <value>         更新字段（label/description）
  node bind list|add|remove ...            绑定认知卡片
  node next list|add|update|remove|status  出向连接管理
  node prev <id>                           列出前驱节点
  node generate label|desc <id>            AI 生成标签/描述`,
  nav: `kn-cli nav — 导航图操作
  nav graph nodes|edges|sync               图节点 / 有向边 / 重算
  nav current get|set <id>                 当前中心节点
  nav mode get|set <overview|station>      导航模式
  nav waypoint list|add|remove|clear|fill  途经点管理（fill = 补齐缺失连接）
  nav next <id>                            按合成权重排序的后继节点
  nav prev <id>                            前驱节点`,
  plan: `kn-cli plan — 路线规划
  plan generate [--ids <id1,id2,...>]      生成候选计划
  plan list | get <id> | select <id>       查看 / 选中计划
  plan recommend                           推荐计划
  plan mode get|waypoint <m>|weight <m>    模式设置
  plan replan                              重新规划`,
  browse: `kn-cli browse — 浏览操作
  browse start [--plan <id>] [--sequence <ids>]
  browse status | cards                    进度 / 当前卡片
  browse next | prev | waypoint            翻卡 / 下一站`,
  search: `kn-cli search — 搜索
  search query <text> [--mode keyword|vector]
  search mode get|set <keyword|vector>
  search results | select <cardId> | bind-nodes`,
  tree: `kn-cli tree — 树形管理
  tree list | children <id> | path <id>
  tree select|expand|toggle <id>
  tree search <query>`,
  yaml: `kn-cli yaml — YAML 导入导出
  yaml export [--file <path>]              导出（无 --file 时输出到 stdout）
  yaml preview <file>                      预览导入变更
  yaml import <file>                       导入（upsert 合并）
  yaml validate <file>                     校验文件合法性`,
  view: `kn-cli view — 视图切换
  view get
  view set <search|nav|plan|browse|tree>`,
}

/** kn-cli help — 帮助 */
export const run: CommandModule['run'] = async (_api, args) => {
  const topic = args[0]
  if (topic && GROUP_HELP[topic]) {
    console.log(GROUP_HELP[topic])
    return
  }
  console.log(GENERAL_HELP)
}

export { GROUP_HELP }
