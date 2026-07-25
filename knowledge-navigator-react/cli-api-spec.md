# Knowledge Navigator — CLI & API 规范

## 版本

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| 1.0 | 2026-07-25 | — | 初始规范：为所有功能建立 CLI 和 API 接口定义 |

---

## 一、概述

### 1.1 目标

为 **Knowledge Navigator** 的所有功能提供两套程序化接口：

- **CLI（`kn-cli`）**：命令行工具，支持在终端中直接操作认知卡片、导航节点、路线规划、YAML 导入导出等全部功能
- **API（`KnowledgeNavigatorAPI`）**：JavaScript/TypeScript 程序化接口，供其他模块、脚本或服务集成调用

### 1.2 设计原则

- **功能全覆盖**：CLI 和 API 覆盖所有现有 Store、Utils、Data 层的操作
- **CLI = API 的 shell 映射**：每条 CLI 命令对应一个 API 方法，CLI 是 API 的终端封装
- **输出可解析**：CLI 默认输出格式化为易读文本，支持 `--json` 标志输出 JSON 供程序消费
- **无状态**：所有命令操作当前内存中的数据源，不维护持久化连接
- **错误可处理**：所有操作返回结构化结果 `{ ok: boolean, data?: T, error?: string }`

---

## 二、API 设计

### 2.1 全局入口

```typescript
// api/index.ts
import type { CognitiveCard, NavNode, RoutePlan, BrowseCard, TreeNodeData } from '../data/types'
import type { MatchMode, MatchedCard } from '../store/searchStore'
import type { NavMode, NextNodeItem } from '../store/navStore'
import type { WaypointMode, WeightMode } from '../store/routePlanner'
import type { ConnectionStatusResult } from '../utils/quickConnectUtils'
import type { ImportPreview, YamlData } from '../utils/yamlIO'
import type { WeightedRef } from '../utils/weightUtils'

export class KnowledgeNavigatorAPI {
  // ============================================================
  // 2.2 认知卡片 (Cognitive Cards)
  // ============================================================

  /** 获取全部认知卡片 */
  getAllCards(): CognitiveCard[]

  /** 按 ID 获取单张卡片 */
  getCard(id: string): CognitiveCard | undefined

  /** 获取子卡片列表 */
  getChildCards(parentId: string): CognitiveCard[]

  /** 新建卡片（自动生成 ID） */
  createCard(parentId?: string): ApiResult<CognitiveCard>

  /** 删除卡片（文件夹类型必须为空） */
  deleteCard(id: string): ApiResult<void>

  /** 更新卡片字段（id 只读） */
  updateCardField(id: string, field: string, value: unknown): ApiResult<void>

  /** 批量更新卡片字段 */
  updateCardFields(id: string, updates: Partial<CognitiveCard>): ApiResult<void>

  /** 添加语料库条目 */
  addCardCorpus(id: string, text: string): ApiResult<void>

  /** 更新语料库条目 */
  updateCardCorpus(id: string, index: number, text: string): ApiResult<void>

  /** 删除语料库条目 */
  removeCardCorpus(id: string, index: number): ApiResult<void>

  /** 添加绑定导航节点 */
  addCardBoundNode(cardId: string, nodeId: string): ApiResult<void>

  /** 移除绑定导航节点 */
  removeCardBoundNode(cardId: string, nodeId: string): ApiResult<void>

  // ============================================================
  // 2.3 导航节点 (Navigation Nodes)
  // ============================================================

  /** 获取全部导航节点 */
  getAllNavNodes(): NavNode[]

  /** 按 ID 获取导航节点 */
  getNavNode(id: string): NavNode | undefined

  /** 按标签搜索导航节点 */
  searchNavNodes(query: string): NavNode[]

  /** 新建导航节点 */
  createNavNode(): ApiResult<NavNode>

  /** 删除导航节点（级联清理引用） */
  deleteNavNode(id: string): ApiResult<void>

  /** 更新导航节点字段（id 只读） */
  updateNavNodeField(id: string, field: string, value: unknown): ApiResult<void>

  /** 添加绑定认知卡片 */
  addNavNodeBoundCard(nodeId: string, cardId: string): ApiResult<void>

  /** 移除绑定认知卡片 */
  removeNavNodeBoundCard(nodeId: string, cardId: string): ApiResult<void>

  // ============================================================
  // 2.4 出向连接 (Next Node Connections)
  // ============================================================

  /** 获取节点所有出向连接 */
  getNextNodes(nodeId: string): NextNodeItem[]

  /** 获取节点所有前驱节点 */
  getPrevNodes(nodeId: string): NavNode[]

  /** 添加出向连接 */
  addNextNodeRef(fromId: string, ref: NextNodeRefInput): ApiResult<void>

  /** 更新出向连接字段 */
  updateNextNodeRef(fromId: string, targetId: string, updates: Partial<NextNodeRefInput>): ApiResult<void>

  /** 删除出向连接 */
  removeNextNodeRef(fromId: string, targetId: string): ApiResult<void>

  /** 查询连接状态 */
  getConnectionStatus(fromId: string, toId: string): ConnectionStatusResult

  /** 一键建立连接（快速连接） */
  ensureQuickConnection(fromId: string, toId: string): boolean

  /** 批量补齐途经点序列中所有缺失连接 */
  fillAllMissingConnections(waypointIds: string[]): number

  // ============================================================
  // 2.5 导航图 (Navigation Graph)
  // ============================================================

  /** 获取全量有向边 */
  getAllEdges(): GraphEdge[]

  /** 设置当前中心节点 */
  setCurrentNode(nodeId: string): void

  /** 切换导航模式 */
  setNavMode(mode: NavMode): void

  /** 添加途经点 */
  addWaypoint(nodeId: string): ApiResult<void>

  /** 移除途经点 */
  removeWaypoint(index: number): void

  /** 清空途经点 */
  clearWaypoints(): void

  /** 获取合成权重排序的后继节点 */
  getWeightedNextNodes(nodeId: string): WeightedRef[]

  /** 从数据源重算图 */
  syncGraphFromSource(): void

  // ============================================================
  // 2.6 路线规划 (Route Planning)
  // ============================================================

  /** 设置途经点排序模式 */
  setWaypointMode(mode: WaypointMode): void

  /** 设置权重模式 */
  setWeightMode(mode: WeightMode): void

  /** 生成候选路线计划 */
  generatePlans(waypointIds?: string[]): ApiResult<RoutePlan[]>

  /** 选中一个计划 */
  selectPlan(planId: string): ApiResult<void>

  /** 获取所有候选计划 */
  getAllPlans(): RoutePlan[]

  /** 获取当前选中的计划 */
  getSelectedPlan(): RoutePlan | undefined

  /** 获取推荐计划 */
  getRecommendedPlan(): RoutePlan | undefined

  /** 重新规划 */
  replan(): void

  // ============================================================
  // 2.7 浏览 (Browse)
  // ============================================================

  /** 从规划序列初始化浏览 */
  initBrowseFromPlan(planId: string): ApiResult<void>

  /** 直接从节点序列初始化浏览 */
  initBrowseFromSequence(nodeIds: string[]): ApiResult<void>

  /** 获取当前浏览卡片 */
  getCurrentBrowseCards(): BrowseCard[]

  /** 获取浏览进度 */
  getBrowseProgress(): { waypointIndex: number; totalWaypoints: number; cardIndex: number; totalCards: number }

  /** 下一张卡片 */
  nextCard(): ApiResult<void>

  /** 上一张卡片 */
  prevCard(): ApiResult<void>

  /** 下一站 */
  nextWaypoint(): ApiResult<void>

  // ============================================================
  // 2.8 搜索 (Search)
  // ============================================================

  /** 设置搜索查询 */
  setSearchQuery(query: string): void

  /** 切换匹配模式 */
  setMatchMode(mode: MatchMode): void

  /** 执行搜索，返回匹配结果 */
  search(query: string, mode?: MatchMode): Promise<MatchedCard[]>

  /** 选中匹配卡片 */
  selectMatchedCard(cardId: string): ApiResult<void>

  /** 获取当前匹配结果 */
  getMatchedCards(): MatchedCard[]

  /** 获取当前选中卡片的绑定导航节点 */
  getBoundNodesForSelectedCard(): NavNode[]

  /** 向量匹配重试 */
  retryVectorMatch(): Promise<void>

  // ============================================================
  // 2.9 树形管理 (Tree Management)
  // ============================================================

  /** 获取树形扁平数据 */
  getTreeFlatData(): TreeNodeData[]

  /** 获取根节点 */
  getRootNodes(): TreeNodeData[]

  /** 获取子节点 */
  getTreeChildren(parentId: string): TreeNodeData[]

  /** 获取节点的完整路径（面包屑） */
  getTreePath(nodeId: string): { path: string; label: string }[]

  /** 展开/折叠节点 */
  toggleTreeNode(nodeId: string): void

  /** 展开所有祖先节点 */
  expandTreeAncestors(nodeId: string): void

  /** 搜索树节点 */
  searchTree(query: string): void

  /** 选中树节点 */
  selectTreeNode(nodeId: string): void

  // ============================================================
  // 2.10 YAML 导入导出
  // ============================================================

  /** 导出全部数据为 YAML 字符串 */
  exportToYAML(): string

  /** 下载 YAML 文件 */
  downloadYAML(filename?: string): void

  /** 解析并验证 YAML 字符串 */
  parseYAML(raw: string): ApiResult<YamlData>

  /** 计算导入预览 */
  computeImportPreview(raw: string): ApiResult<ImportPreview>

  /** 执行导入合并 */
  importYAML(raw: string): ApiResult<ImportPreview>

  // ============================================================
  // 2.11 AI 辅助生成
  // ============================================================

  /** AI 生成卡片标题 */
  generateCardTitle(cardId: string): Promise<ApiResult<string>>

  /** AI 生成卡片描述 */
  generateCardDescription(cardId: string): Promise<ApiResult<string>>

  /** AI 生成导航节点标签 */
  generateNodeLabel(nodeId: string): Promise<ApiResult<string>>

  /** AI 生成导航节点描述 */
  generateNodeDescription(nodeId: string): Promise<ApiResult<string>>

  /** 检查 AI 是否正在生成 */
  isGenerating(): boolean

  // ============================================================
  // 2.12 视图 (View)
  // ============================================================

  /** 切换活动视图 */
  switchView(viewName: ViewName): void

  /** 获取当前活动视图 */
  getActiveView(): ViewName

  /** 获取面板状态 */
  getPanelState(): { node: NavNode | null; position: PanelPosition; hidden: boolean }

  /** 设置面板节点 */
  setPanelNode(nodeId: string | null): void

  /** 设置面板位置 */
  setPanelPosition(position: PanelPosition): void
}

// ============================================================
// 辅助类型
// ============================================================

type ApiResult<T> = { ok: true; data: T } | { ok: false; error: string }

type NextNodeRefInput = {
  target_id: string
  preset_priority?: number
  browse_priority?: number
  connection_type?: 'preset' | 'browse_derived' | 'user_added'
}

type ViewName = 'search' | 'nav' | 'plan' | 'browse' | 'tree'
type PanelPosition = 'collapsed' | 'half' | 'full'

interface GraphEdge {
  source: string
  target: string
  weight: number
}
```

---

## 三、CLI 设计

### 3.1 基本用法

```
kn-cli <command> [subcommand] [options] [arguments]
```

**全局选项**：

| 选项 | 说明 |
|------|------|
| `--json` | 输出 JSON 格式（默认输出易读文本） |
| `--help` | 显示帮助信息 |
| `--version` | 显示版本号 |

**输出格式**：

```
# 文本模式（默认）
✓ 已创建卡片 root/5 (ID: root/5)
  title: "新卡片"
  type: leaf

# JSON 模式 (--json)
{"ok":true,"data":{"id":"root/5","title":"新卡片","type":"leaf"}}
```

---

### 3.2 命令树

```
kn-cli
├── card                         # 认知卡片管理
│   ├── list                     # 列出所有卡片
│   ├── get <id>                 # 查看单张卡片
│   ├── create [--parent <id>]   # 新建卡片
│   ├── delete <id>              # 删除卡片
│   ├── update <id> <field> <value>  # 更新字段
│   ├── corpus                   # 语料库管理
│   │   ├── list <id>            # 列出语料库条目
│   │   ├── add <id> <text>      # 添加语料
│   │   ├── update <id> <index> <text>  # 更新语料
│   │   └── remove <id> <index>  # 删除语料
│   ├── bind                     # 绑定导航节点管理
│   │   ├── list <id>            # 列出绑定的导航节点
│   │   ├── add <cardId> <nodeId> # 绑定节点
│   │   └── remove <cardId> <nodeId> # 解绑节点
│   ├── children <id>            # 列出子卡片
│   └── generate                 # AI 生成
│       ├── title <id>           # 生成标题
│       └── desc <id>            # 生成描述
│
├── node                         # 导航节点管理
│   ├── list [--query <q>]       # 列出节点（可搜索）
│   ├── get <id>                 # 查看单个节点
│   ├── create                   # 新建节点
│   ├── delete <id>              # 删除节点（级联清理）
│   ├── update <id> <field> <value>  # 更新字段
│   ├── bind                     # 绑定卡片管理
│   │   ├── list <id>            # 列出绑定的卡片
│   │   ├── add <nodeId> <cardId> # 绑定卡片
│   │   └── remove <nodeId> <cardId> # 解绑卡片
│   ├── next                     # 出向连接管理
│   │   ├── list <id>            # 列出出向连接
│   │   ├── add <fromId> <toId> [--priority <n>] [--type <t>]  # 添加连接
│   │   ├── update <fromId> <toId> <field> <value>  # 更新连接
│   │   ├── remove <fromId> <toId>  # 删除连接
│   │   └── status <fromId> <toId>  # 查询连接状态
│   ├── prev <id>                # 列出前驱节点
│   └── generate                 # AI 生成
│       ├── label <id>           # 生成标签
│       └── desc <id>            # 生成描述
│
├── nav                          # 导航图操作
│   ├── graph                    # 图操作
│   │   ├── nodes                # 列出所有图节点
│   │   ├── edges                # 列出所有有向边
│   │   └── sync                 # 从数据源重算图
│   ├── current                  # 当前中心节点
│   │   ├── get                  # 查看当前节点
│   │   └── set <id>             # 设置当前节点
│   ├── mode                     # 导航模式
│   │   ├── get                  # 查看当前模式
│   │   └── set <overview|station>  # 切换模式
│   ├── waypoint                 # 途经点管理
│   │   ├── list                 # 列出途经点
│   │   ├── add <id>             # 添加途经点
│   │   ├── remove <index>       # 移除途经点
│   │   ├── clear                # 清空途经点
│   │   └── fill                 # 补齐所有缺失连接
│   ├── next <id>                # 显示按权重排序的后继节点
│   └── prev <id>                # 显示前驱节点
│
├── plan                         # 路线规划
│   ├── generate [--ids <ids>]   # 生成候选计划（逗号分隔 ID）
│   ├── list                     # 列出所有候选计划
│   ├── get <id>                 # 查看计划详情
│   ├── select <id>              # 选中计划
│   ├── recommend                # 查看推荐计划
│   ├── mode                     # 模式设置
│   │   ├── get                  # 查看当前模式
│   │   ├── waypoint <ordered|unordered>  # 设置途经点模式
│   │   └── weight <mixed|user_only>      # 设置权重模式
│   └── replan                   # 重新规划
│
├── browse                       # 浏览操作
│   ├── start                    # 从当前选中计划开始浏览
│   │   [--plan <planId>]        # 指定计划 ID
│   │   [--sequence <ids>]       # 或直接指定节点序列
│   ├── status                   # 查看浏览进度
│   ├── cards                    # 查看当前卡片
│   ├── next                     # 下一张卡片
│   ├── prev                     # 上一张卡片
│   └── waypoint                 # 下一站
│
├── search                       # 搜索
│   ├── query <text>             # 执行搜索
│   │   [--mode keyword|vector]  # 指定匹配模式
│   ├── mode                     # 模式设置
│   │   ├── get                  # 查看当前模式
│   │   └── set <keyword|vector> # 切换模式
│   ├── results                  # 查看当前匹配结果
│   ├── select <cardId>          # 选中匹配卡片
│   └── bind-nodes               # 查看当前选中卡片的绑定节点
│
├── tree                         # 树形管理
│   ├── list                     # 列出树形根节点
│   ├── children <id>            # 列出子节点
│   ├── path <id>                # 查看节点路径（面包屑）
│   ├── select <id>              # 选中节点
│   ├── expand <id>              # 展开节点
│   ├── toggle <id>              # 切换展开/折叠
│   └── search <query>           # 搜索树节点
│
├── yaml                         # YAML 导入导出
│   ├── export [--file <path>]   # 导出到文件（默认下载）
│   ├── preview <file>           # 预览导入变更
│   ├── import <file>            # 导入 YAML 文件
│   └── validate <file>          # 验证 YAML 文件合法性
│
├── view                         # 视图切换
│   ├── get                      # 查看当前视图
│   └── set <search|nav|plan|browse|tree>  # 切换视图
│
└── help [command]               # 查看帮助
```

---

## 四、CLI 命令详细规范

### 4.1 `kn-cli card`

```
kn-cli card list [--json]
kn-cli card get <id> [--json]
kn-cli card create [--parent <parentId>] [--title <title>] [--type <folder|leaf>] [--json]
kn-cli card delete <id>
kn-cli card update <id> <field> <value>
kn-cli card corpus list <id>
kn-cli card corpus add <id> <text>
kn-cli card corpus update <id> <index> <text>
kn-cli card corpus remove <id> <index>
kn-cli card bind list <id>
kn-cli card bind add <cardId> <nodeId>
kn-cli card bind remove <cardId> <nodeId>
kn-cli card children <id> [--json]
kn-cli card generate title <id>
kn-cli card generate desc <id>

card update 可操作的 field:
  title, description, tag, type (folder/leaf)

示例:
  kn-cli card list --json
  kn-cli card get root/1
  kn-cli card create --parent root/1 --title "新概念" --type leaf
  kn-cli card update root/5 title "机器学习进阶"
  kn-cli card corpus add root/5 "这是关于机器学习的补充语料"
  kn-cli card corpus remove root/5 2
  kn-cli card bind add root/5 node-1
  kn-cli card children root/1
  kn-cli card generate title root/5
```

### 4.2 `kn-cli node`

```
kn-cli node list [--query <q>] [--json]
kn-cli node get <id> [--json]
kn-cli node create [--label <label>] [--json]
kn-cli node delete <id>
kn-cli node update <id> <field> <value>
kn-cli node bind list <id>
kn-cli node bind add <nodeId> <cardId>
kn-cli node bind remove <nodeId> <cardId>
kn-cli node next list <id> [--json]
kn-cli node next add <fromId> <toId> [--priority <n>] [--type <preset|browse_derived|user_added>]
kn-cli node next update <fromId> <toId> <field> <value>
kn-cli node next remove <fromId> <toId>
kn-cli node next status <fromId> <toId> [--json]
kn-cli node prev <id> [--json]
kn-cli node generate label <id>
kn-cli node generate desc <id>

node update 可操作的 field:
  label, description

node next update 可操作的 field:
  preset_priority, browse_priority, connection_type

示例:
  kn-cli node list --query "机器学习"
  kn-cli node get node-1 --json
  kn-cli node create --label "强化学习"
  kn-cli node next add node-1 node-2 --priority 1
  kn-cli node next update node-1 node-2 preset_priority 2
  kn-cli node next status node-1 node-2
  kn-cli node prev node-3
  kn-cli node generate label node-5
```

### 4.3 `kn-cli nav`

```
kn-cli nav graph nodes [--json]
kn-cli nav graph edges [--json]
kn-cli nav graph sync
kn-cli nav current get [--json]
kn-cli nav current set <id>
kn-cli nav mode get
kn-cli nav mode set <overview|station>
kn-cli nav waypoint list [--json]
kn-cli nav waypoint add <id>
kn-cli nav waypoint remove <index>
kn-cli nav waypoint clear
kn-cli nav waypoint fill
kn-cli nav next <id> [--json]
kn-cli nav prev <id> [--json]

示例:
  kn-cli nav graph edges --json
  kn-cli nav current set node-1
  kn-cli nav mode set overview
  kn-cli nav waypoint add node-1
  kn-cli nav waypoint add node-2
  kn-cli nav waypoint fill
  kn-cli nav next node-1
```

### 4.4 `kn-cli plan`

```
kn-cli plan generate [--ids <id1,id2,...>] [--json]
kn-cli plan list [--json]
kn-cli plan get <id> [--json]
kn-cli plan select <id>
kn-cli plan recommend [--json]
kn-cli plan mode get
kn-cli plan mode waypoint <ordered|unordered>
kn-cli plan mode weight <mixed|user_only>
kn-cli plan replan

示例:
  kn-cli plan generate --ids node-1,node-2,node-3
  kn-cli plan list --json
  kn-cli plan select plan-1
  kn-cli plan recommend
  kn-cli plan mode waypoint unordered
  kn-cli plan mode weight user_only
```

### 4.5 `kn-cli browse`

```
kn-cli browse start [--plan <planId>] [--sequence <id1,id2,...>]
kn-cli browse status [--json]
kn-cli browse cards [--json]
kn-cli browse next
kn-cli browse prev
kn-cli browse waypoint

示例:
  kn-cli browse start --plan plan-1
  kn-cli browse start --sequence node-1,node-2,node-3
  kn-cli browse status
  kn-cli browse next
  kn-cli browse waypoint
```

### 4.6 `kn-cli search`

```
kn-cli search query <text> [--mode keyword|vector] [--json]
kn-cli search mode get
kn-cli search mode set <keyword|vector>
kn-cli search results [--json]
kn-cli search select <cardId>
kn-cli search bind-nodes [--json]

示例:
  kn-cli search query "神经网络" --mode vector --json
  kn-cli search mode set vector
  kn-cli search results
  kn-cli search select root/2
  kn-cli search bind-nodes
```

### 4.7 `kn-cli tree`

```
kn-cli tree list [--json]
kn-cli tree children <id> [--json]
kn-cli tree path <id>
kn-cli tree select <id>
kn-cli tree expand <id>
kn-cli tree toggle <id>
kn-cli tree search <query> [--json]

示例:
  kn-cli tree list
  kn-cli tree children root/1
  kn-cli tree path root/1/2
  kn-cli tree expand root/1
  kn-cli tree search "机器"
```

### 4.8 `kn-cli yaml`

```
kn-cli yaml export [--file <path>]
kn-cli yaml preview <file> [--json]
kn-cli yaml import <file>
kn-cli yaml validate <file> [--json]

示例:
  kn-cli yaml export --file ./backup.yaml
  kn-cli yaml preview ./import.yaml
  kn-cli yaml import ./backup.yaml
  kn-cli yaml validate ./data.yaml
```

### 4.9 `kn-cli view`

```
kn-cli view get
kn-cli view set <search|nav|plan|browse|tree>

示例:
  kn-cli view get
  kn-cli view set plan
```

### 4.10 `kn-cli help`

```
kn-cli help
kn-cli help card
kn-cli help node
kn-cli help plan
```

---

## 五、CLI 实现建议

### 5.1 架构

```
src/cli/
├── index.ts              # 入口：解析 argv，分发到各命令处理器
├── commands/
│   ├── card.ts           # card 命令处理器
│   ├── node.ts           # node 命令处理器
│   ├── nav.ts            # nav 命令处理器
│   ├── plan.ts           # plan 命令处理器
│   ├── browse.ts         # browse 命令处理器
│   ├── search.ts         # search 命令处理器
│   ├── tree.ts           # tree 命令处理器
│   ├── yaml.ts           # yaml 命令处理器
│   ├── view.ts           # view 命令处理器
│   └── help.ts           # help 命令处理器
├── formatter.ts          # 输出格式化（文本/JSON）
├── parser.ts             # 参数解析
└── runner.ts             # 命令执行器：串联 API 调用 + 输出
```

### 5.2 参数解析

建议使用 `commander` 或 `yargs` 库进行 CLI 参数解析：

```typescript
// 示例：使用 yargs
import yargs from 'yargs'
import { hideBin } from 'yargs/helpers'

yargs(hideBin(process.argv))
  .command('card list', '列出所有卡片', (yargs) => {
    return yargs.option('json', { type: 'boolean', desc: 'JSON 输出' })
  }, async (argv) => {
    const api = createAPI()
    const cards = api.getAllCards()
    output(cards, argv.json)
  })
  // ... 其余命令
  .demandCommand(1, '请指定一个命令')
  .strict()
  .parse()
```

### 5.3 API 实例化

```typescript
// cli/runner.ts
import { KnowledgeNavigatorAPI } from '../api'

let _api: KnowledgeNavigatorAPI | null = null

export function createAPI(): KnowledgeNavigatorAPI {
  if (!_api) {
    _api = new KnowledgeNavigatorAPI()
  }
  return _api
}
```

### 5.4 输出格式化

```typescript
// cli/formatter.ts
export function output(data: unknown, jsonMode: boolean): void {
  if (jsonMode) {
    console.log(JSON.stringify(data, null, 2))
    return
  }
  // 文本模式：根据数据类型选择格式化策略
  if (Array.isArray(data)) {
    formatArray(data)
  } else if (typeof data === 'object' && data !== null) {
    formatObject(data as Record<string, unknown>)
  } else {
    console.log(String(data))
  }
}

function formatArray(arr: unknown[]): void {
  for (const item of arr) {
    if (typeof item === 'object' && item !== null) {
      const obj = item as Record<string, unknown>
      const id = obj.id ?? obj.label ?? ''
      console.log(`  ${id}`)
    } else {
      console.log(`  ${item}`)
    }
  }
}

function formatObject(obj: Record<string, unknown>): void {
  for (const [key, value] of Object.entries(obj)) {
    if (Array.isArray(value)) {
      console.log(`  ${key}: [${value.length} items]`)
    } else if (typeof value === 'object' && value !== null) {
      console.log(`  ${key}:`)
      formatObject(value as Record<string, unknown>)
    } else {
      console.log(`  ${key}: ${value}`)
    }
  }
}
```

### 5.5 package.json 入口

```json
{
  "bin": {
    "kn-cli": "./dist/cli/index.js"
  }
}
```

```typescript
// src/cli/index.ts
#!/usr/bin/env node
import { main } from './runner'
main().catch(console.error)
```

---

## 六、API 实现建议

### 6.1 实现方式

`KnowledgeNavigatorAPI` 封装对所有 Zustand Store 和数据源的调用：

```typescript
// api/index.ts
import { cognitiveCards, getCard } from '../data/cards'
import { allNavNodes, getNavNode, navNodeMap, allEdges } from '../data/allNavNodes'
import { useCardStore } from '../store/cardStore'
import { useNavNodeStore } from '../store/navNodeStore'
import { useNavStore } from '../store/navStore'
import { usePlanStore } from '../store/planStore'
import { useBrowseStore } from '../store/browseStore'
import { useSearchStore } from '../store/searchStore'
import { useTreeStore } from '../store/treeStore'
import { useViewStore } from '../store/viewStore'
import { usePanelStore } from '../store/panelStore'
import * as quickConnectUtils from '../utils/quickConnectUtils'
import * as yamlIO from '../utils/yamlIO'
import * as routePlanner from '../utils/routePlanner'
import * as weightUtils from '../utils/weightUtils'
import * as treeUtils from '../utils/treeUtils'

export class KnowledgeNavigatorAPI {
  // 每个方法内部通过 store.getState() 获取最新状态并调用对应 action
  // 或直接操作共享数据源数组

  getAllCards(): CognitiveCard[] {
    return useCardStore.getState().allCards
  }

  getCard(id: string): CognitiveCard | undefined {
    return getCard(id)
  }

  createCard(parentId?: string): ApiResult<CognitiveCard> {
    try {
      const card = useCardStore.getState().createCard(parentId)
      return { ok: true, data: card }
    } catch (e) {
      return { ok: false, error: (e as Error).message }
    }
  }

  // ... 其余方法类似实现
}
```

### 6.2 错误处理

所有 API 方法返回 `ApiResult<T>` 类型，调用方通过 `ok` 字段判断是否成功：

```typescript
const result = api.deleteCard('root/nonexistent')
if (!result.ok) {
  console.error('删除失败:', result.error)
}
```

### 6.3 异步操作

搜索（向量模式）和 AI 生成是异步方法，返回 `Promise<ApiResult<T>>`：

```typescript
const result = await api.search('神经网络', 'vector')
if (result.ok) {
  console.log('匹配结果:', result.data)
}
```

---

## 七、目录结构

```
src/
├── api/
│   └── index.ts              ← KnowledgeNavigatorAPI 类
│
├── cli/
│   ├── index.ts              ← 入口 (#!/usr/bin/env node)
│   ├── runner.ts             ← 命令执行器
│   ├── parser.ts             ← 参数解析
│   ├── formatter.ts          ← 输出格式化
│   └── commands/
│       ├── card.ts
│       ├── node.ts
│       ├── nav.ts
│       ├── plan.ts
│       ├── browse.ts
│       ├── search.ts
│       ├── tree.ts
│       ├── yaml.ts
│       ├── view.ts
│       └── help.ts
│
└── ... (现有代码结构不变)
```

---

## 八、验收标准

- [ ] `KnowledgeNavigatorAPI` 覆盖所有认知卡片 CRUD 操作
- [ ] `KnowledgeNavigatorAPI` 覆盖所有导航节点 CRUD 操作
- [ ] `KnowledgeNavigatorAPI` 覆盖出向连接的增删改查和快速连接
- [ ] `KnowledgeNavigatorAPI` 覆盖导航图操作（节点/边/模式/途经点）
- [ ] `KnowledgeNavigatorAPI` 覆盖路线规划（生成/选择/模式切换）
- [ ] `KnowledgeNavigatorAPI` 覆盖浏览流程（初始化/翻卡/下一站）
- [ ] `KnowledgeNavigatorAPI` 覆盖搜索（关键词/向量/结果操作）
- [ ] `KnowledgeNavigatorAPI` 覆盖树形管理（展开/搜索/路径）
- [ ] `KnowledgeNavigatorAPI` 覆盖 YAML 导入导出（导出/预览/导入/验证）
- [ ] `KnowledgeNavigatorAPI` 覆盖 AI 辅助生成（标题/描述/标签）
- [ ] `KnowledgeNavigatorAPI` 覆盖视图切换和面板操作
- [ ] CLI 所有命令可正常调用，输出格式正确
- [ ] CLI `--json` 标志输出可被程序解析的 JSON
- [ ] CLI 支持 `--help` 查看命令帮助
- [ ] `kn-cli` 可注册为全局命令（package.json bin）
- [ ] TypeScript 编译零错误

---

## 九、边界情况

| 场景 | 行为 |
|------|------|
| 操作不存在的卡片 ID | 返回 `{ ok: false, error: "卡片 root/999 不存在" }` |
| 操作不存在的节点 ID | 返回 `{ ok: false, error: "节点 node-999 不存在" }` |
| 删除非空文件夹卡片 | 返回 `{ ok: false, error: "文件夹 root/1 不为空，请先删除子卡片" }` |
| 删除有绑定的节点 | 级联清理其他节点引用、卡片绑定、途经点、面板数据 |
| 重复添加已存在的出向连接 | 不覆盖，返回 `{ ok: false, error: "连接已存在" }` |
| 搜索无结果 | 返回空数组 `[]`，CLI 显示 "无匹配结果" |
| 向量匹配 API 超时 | 降级为本地的 fallbackVectorMatch |
| 途经点不足 2 个时生成计划 | 返回 `{ ok: false, error: "途经点至少需要 2 个" }` |
| 未选中计划时开始浏览 | 返回 `{ ok: false, error: "请先选中一个计划" }` |
| 浏览到最后一站/最后一张卡片 | `nextCard`/`nextWaypoint` 返回错误提示 |
| YAML 文件格式错误 | 返回详细错误列表（含行号和字段路径） |
| YAML 导入引用不存在的节点 | 在验证阶段报告引用错误，阻止导入 |
| CLI 输入无效命令 | 显示 "未知命令"，并提示相近命令 |
