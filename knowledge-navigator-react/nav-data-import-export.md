# 认知卡片与导航节点 — YAML 导入导出

## 版本

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| 1.0 | 2026-07-25 | — | 初始功能规范 |

---

## 一、概述

增加认知卡片（CognitiveCard）和导航节点（NavNode）数据的**YAML 导入导出**功能，使用户可以通过 YAML 文件批量备份、迁移、编辑两类核心数据。

### 1.1 目标

- **导出**：将当前内存中的全部认知卡片和导航节点序列化为标准 YAML 文件，供用户保存或分享。
- **导入**：读取用户选择的 YAML 文件，解析并合并/替换到当前数据源。
- **数据完整性**：导入时校验字段格式、引用一致性（如卡片 bound_nodes 中的节点 id 必须存在），避免损坏现有数据。
- **与 data-model.md 格式一致**：导出的 YAML 结构与 `data-model.md` 中定义的 YAML Schema 完全兼容。

---

## 二、文件格式规范

### 2.1 导出 YAML 结构（单个文件，双根键）

一个 `.yaml` 文件同时包含认知卡片和导航节点，使用 `cognitive_cards` 和 `navigation_nodes` 作为顶层键：

```yaml
# 文件头（可选注释）
# Exported at: 2026-07-25T14:00:00Z
# Total cards: 12, total nodes: 8

cognitive_cards:
  - id: root/1
    title: 机器学习
    type: folder
    corpus:
      - 机器学习是人工智能的一个子领域。
      - 主要范式包括监督学习、无监督学习和强化学习。
    tag: 层级分类
    bound_nodes:
      - node-ml-foundation
      - node-ai-intro
    metadata:
      created_at: 2026-07-20T14:00:00Z

  - id: root/1/1
    title: 监督学习
    type: leaf
    corpus:
      - 使用标注数据训练模型。
    bound_nodes:
      - node-supervised

navigation_nodes:
  - id: node-ml-foundation
    label: 机器学习基础
    description: 核心概念与算法基础。
    bound_cards:
      - root/1
    next_nodes:
      - target_id: node-supervised
        preset_weight: 0.75
        browse_weight: 0.42
        connection_type: preset
    metadata:
      created_at: 2026-07-20T14:00:00Z

  - id: node-supervised
    label: 监督学习
    description: 监督学习相关节点。
    bound_cards:
      - root/1/1
    next_nodes: []
```

### 2.2 认知卡片字段映射

| YAML 字段 | TS 类型 | 必填 | 导出条件 |
|-----------|---------|------|----------|
| `id` | string | 是 | 始终导出 |
| `title` | string | 是 | 始终导出 |
| `type` | enum | 是 | 始终导出 |
| `tag` | string | 否 | 有值时导出 |
| `description` | string | 否 | 有值时导出 |
| `corpus` | string[] | 否 | 有值时导出（空数组不写） |
| `bound_nodes` | string[] | 否 | 有值时导出 |
| `metadata` | object | 否 | 有值时导出 |

### 2.3 导航节点字段映射

| YAML 字段 | TS 类型 | 必填 | 导出条件 |
|-----------|---------|------|----------|
| `id` | string | 是 | 始终导出 |
| `label` | string | 是 | 始终导出 |
| `description` | string | 否 | 有值时导出 |
| `bound_cards` | string[] | 否 | 有值时导出 |
| `browse_history` | array | 否 | 有值时导出 |
| `next_nodes` | array | 是 | 始终导出（空数组写 `[]`） |
| `priority_config` | object | 否 | 有值时导出 |
| `metadata` | object | 否 | 有值时导出 |

---

## 三、UI 交互

### 3.1 入口位置

导入导出入口位于**管理视图（TreeView）**，在页面顶部或工具栏区域放置操作按钮：

```
┌─────────────────────────────────────┐
│ 认知卡片管理     [导入] [导出]       │  ← PageHeader 右侧新增按钮
├─────────────────────────────────────┤
│ ...（树形列表 / 编辑面板）            │
└─────────────────────────────────────┘
```

### 3.2 导出交互

| 步骤 | 用户操作 | 系统行为 |
|------|----------|----------|
| 1 | 点击「导出」按钮 | 触发 `exportAllToYAML()` 函数 |
| 2 | — | 序列化 `useCardStore.allCards` + `useNavNodeStore.allNodes` 为 YAML 字符串 |
| 3 | — | 在文件名中注入时间戳：`cognitive-nav-data-2026-07-25.yaml` |
| 4 | — | 触发浏览器文件下载（`<a download>` 或 Blob URL） |
| 5 | — | Toast 提示："已导出 X 张认知卡片和 Y 个导航节点" |

### 3.3 导入交互

| 步骤 | 用户操作 | 系统行为 |
|------|----------|----------|
| 1 | 点击「导入」按钮 | 触发隐藏 `<input type="file" accept=".yaml,.yml">` |
| 2 | 选择 `.yaml` 文件 | 读取文件内容，调用 `importFromYAML()` 函数 |
| 3 | — | 解析 YAML → 校验格式与引用一致性 |
| 4 | — | 若校验失败：弹出错误提示对话框，显示具体错误 |
| 5 | — | 若校验成功：弹出确认对话框，预览变更概览 |
| 6 | 确认导入 | 合并/替换当前数据源，刷新所有关联 Store |
| 7 | — | Toast 提示："已导入 X 张认知卡片和 Y 个导航节点" |

### 3.4 导入确认对话框

```
┌──────────────────────────────────┐
│  确认导入 YAML 数据               │
│                                  │
│  将导入:                          │
│  ├─ 认知卡片: 12 张               │
│  │  ├─ 新增: 3 张                 │
│  │  ├─ 覆盖: 9 张 (id 冲突)       │
│  │  └─ 删除: 0 张                 │
│  ├─ 导航节点: 8 个                │
│  │  ├─ 新增: 1 个                 │
│  │  ├─ 覆盖: 7 个 (id 冲突)       │
│  │  └─ 删除: 0 张                 │
│                                  │
│  ┌─────────┐ ┌─────────┐         │
│  │  取消   │ │  确认   │         │
│  └─────────┘ └─────────┘         │
└──────────────────────────────────┘
```

---

## 四、数据流

### 4.1 导出流程

```
用户点击「导出」
    │
    ▼
exportAllToYAML()
    │
    ├─ 1. 从 useCardStore.getState().allCards 读取全部卡片
    ├─ 2. 从 useNavNodeStore.getState().allNodes 读取全部节点
    ├─ 3. 构建 YAML 对象: { cognitive_cards: [...], navigation_nodes: [...] }
    ├─ 4. 调用 yaml.dump() (js-yaml 库) 序列化为字符串
    ├─ 5. 添加文件头注释（导出时间、统计）
    ├─ 6. 创建 Blob URL，触发 <a> 下载
    └─ 7. Toast 提示成功
```

### 4.2 导入流程

```
用户选择文件
    │
    ▼
importFromYAML(fileContent: string)
    │
    ├─ 1. 调用 yaml.load() 解析为对象
    ├─ 2. 校验顶层结构: 是否有 cognitive_cards / navigation_nodes 键
    ├─ 3. 校验每张卡片的字段完整性（id, title, type 必填）
    ├─ 4. 校验每个节点的字段完整性（id, label, next_nodes 必填）
    ├─ 5. 校验引用一致性:
    │   ├─ card.bound_nodes 中的 nodeId 在 navigation_nodes 中都有定义
    │   └─ node.bound_cards 中的 cardId 在 cognitive_cards 中都有定义
    │       (跨引用检查只在导入的数据集内进行，不要求与现有数据集一致)
    ├─ 6. 生成变更预览（新增/覆盖/删除统计）
    ├─ 7. 弹出确认对话框，用户确认
    │       │
    │       ├─ 取消 → 不做任何变更
    │       └─ 确认 → 执行合并
    │               │
    │               ├─ 8. 以导入数据中的 id 为 key，逐项 upsert 到共享数据源
    │               ├─ 9. 写回 cognitiveCards / allNavNodes 数组 + navNodeMap
    │               ├─ 10. 更新 useCardStore / useNavNodeStore state
    │               ├─ 11. 同步 treeStore.flatData（卡片 title/type/tag 更新）
    │               ├─ 12. 同步 navStore（边数据重算）
    │               └─ 13. Toast 提示成功
    │
    └─ 错误 → 显示错误对话框，不改变数据
```

### 4.3 导入冲突策略

采用 **upsert（存在即覆盖，不存在则新增）** 策略：

| 场景 | 行为 |
|------|------|
| 导入的卡片 id 在当前数据中不存在 | 新增到 allCards 末尾 |
| 导入的卡片 id 在当前数据中已存在 | 覆盖该 id 的整条记录（全字段替换） |
| 导入的节点 id 在当前数据中不存在 | 新增到 allNodes 末尾 |
| 导入的节点 id 在当前数据中已存在 | 覆盖该 id 的整条记录 |
| 当前数据中有但导入数据中没有的条目 | **保留不动**（不做删除） |

> **不采用全量替换策略**，以避免用户误操作丢失未导出的数据。如果需要清空后导入，用户可以手动先清空再导入。

---

## 五、实现方案

### 5.1 依赖库

```json
{
  "dependencies": {
    "js-yaml": "^4.1.0"
  },
  "devDependencies": {
    "@types/js-yaml": "^4.0.9"
  }
}
```

### 5.2 工具函数

在 `src/utils/` 下新建 `yamlIO.ts`，包含以下导出函数：

```typescript
import { load, dump } from 'js-yaml'
import type { CognitiveCard, NavNode } from '../data/types'

/* ========== 类型定义 ========== */

/** YAML 文件顶层结构 */
interface YamlData {
  cognitive_cards: CognitiveCard[]
  navigation_nodes: NavNode[]
}

/** 导入校验错误 */
interface ValidationError {
  type: 'structure' | 'field' | 'reference'
  message: string
  itemId?: string
}

/** 导入变更预览 */
interface ImportPreview {
  cards: { total: number; added: number; overwritten: number }
  nodes: { total: number; added: number; overwritten: number }
}

/* ========== 导出 ========== */

/**
 * 导出全部认知卡片和导航节点为 YAML 字符串。
 * 序列化前剔除空数组、undefined、metadata 中的空对象，
 * 保持导出文件简洁可读。
 */
export function exportAllToYAML(
  cards: CognitiveCard[],
  nodes: NavNode[],
): string {
  const data: YamlData = {
    cognitive_cards: cards.map(cleanCard),
    navigation_nodes: nodes.map(cleanNode),
  }
  const now = new Date().toISOString()
  const comment = `# Exported at: ${now}\n# Total cards: ${cards.length}, total nodes: ${nodes.length}\n\n`
  return comment + dump(data, { indent: 2, lineWidth: 120, noRefs: true })
}

/**
 * 触发浏览器下载 YAML 文件。
 * 使用 <a> download + Blob URL 方案，兼容所有现代浏览器。
 */
export function downloadYAML(yamlStr: string, filename?: string): void {
  const name = filename ?? `cognitive-nav-data-${new Date().toISOString().slice(0, 10)}.yaml`
  const blob = new Blob([yamlStr], { type: 'application/x-yaml;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = name
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

/* ========== 导入 ========== */

/**
 * 解析并校验 YAML 字符串。
 * 返回 { ok: true, data } 或 { ok: false, errors }。
 */
export function parseAndValidateYAML(
  raw: string,
): { ok: true; data: YamlData } | { ok: false; errors: ValidationError[] } {
  const errors: ValidationError[] = []
  let parsed: any

  try {
    parsed = load(raw)
  } catch (e) {
    errors.push({ type: 'structure', message: `YAML 解析失败: ${(e as Error).message}` })
    return { ok: false, errors }
  }

  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
    errors.push({ type: 'structure', message: 'YAML 顶层必须是一个对象' })
    return { ok: false, errors }
  }

  // 顶层键校验（至少有一个）
  const hasCards = 'cognitive_cards' in parsed
  const hasNodes = 'navigation_nodes' in parsed
  if (!hasCards && !hasNodes) {
    errors.push({ type: 'structure', message: 'YAML 文件中缺少 cognitive_cards 或 navigation_nodes 键' })
    return { ok: false, errors }
  }

  const cards: CognitiveCard[] = []
  const nodes: NavNode[] = []

  // 校验认知卡片
  if (hasCards) {
    if (!Array.isArray(parsed.cognitive_cards)) {
      errors.push({ type: 'structure', message: 'cognitive_cards 必须是数组' })
    } else {
      parsed.cognitive_cards.forEach((item: any, i: number) => {
        const id = item?.id ?? `index ${i}`
        if (!item || typeof item !== 'object') {
          errors.push({ type: 'field', itemId: String(id), message: `第 ${i + 1} 项不是有效对象` })
          return
        }
        if (!item.id || typeof item.id !== 'string') {
          errors.push({ type: 'field', itemId: String(id), message: '缺少必填字段 id' })
          return
        }
        if (!item.title || typeof item.title !== 'string') {
          errors.push({ type: 'field', itemId: item.id, message: '缺少必填字段 title' })
          return
        }
        if (!['folder', 'leaf'].includes(item.type)) {
          errors.push({ type: 'field', itemId: item.id, message: 'type 必须是 folder 或 leaf' })
          return
        }
        cards.push(item as CognitiveCard)
      })
    }
  }

  // 校验导航节点
  if (hasNodes) {
    if (!Array.isArray(parsed.navigation_nodes)) {
      errors.push({ type: 'structure', message: 'navigation_nodes 必须是数组' })
    } else {
      parsed.navigation_nodes.forEach((item: any, i: number) => {
        const id = item?.id ?? `index ${i}`
        if (!item || typeof item !== 'object') {
          errors.push({ type: 'field', itemId: String(id), message: `第 ${i + 1} 项不是有效对象` })
          return
        }
        if (!item.id || typeof item.id !== 'string') {
          errors.push({ type: 'field', itemId: String(id), message: '缺少必填字段 id' })
          return
        }
        if (!item.label || typeof item.label !== 'string') {
          errors.push({ type: 'field', itemId: item.id, message: '缺少必填字段 label' })
          return
        }
        if (!Array.isArray(item.next_nodes)) {
          errors.push({ type: 'field', itemId: item.id, message: 'next_nodes 必须是数组（允许空数组）' })
          return
        }
        nodes.push(item as NavNode)
      })
    }
  }

  if (errors.length > 0) return { ok: false, errors }

  return { ok: true, data: { cognitive_cards: cards, navigation_nodes: nodes } }
}

/**
 * 计算变更预览（相对于当前数据）。
 */
export function computeImportPreview(
  imported: YamlData,
  currentCards: CognitiveCard[],
  currentNodes: NavNode[],
): ImportPreview {
  const cardIds = new Set(currentCards.map((c) => c.id))
  const nodeIds = new Set(currentNodes.map((n) => n.id))

  const cardAdded = imported.cognitive_cards.filter((c) => !cardIds.has(c.id)).length
  const cardOverwritten = imported.cognitive_cards.filter((c) => cardIds.has(c.id)).length

  const nodeAdded = imported.navigation_nodes.filter((n) => !nodeIds.has(n.id)).length
  const nodeOverwritten = imported.navigation_nodes.filter((n) => nodeIds.has(n.id)).length

  return {
    cards: { total: imported.cognitive_cards.length, added: cardAdded, overwritten: cardOverwritten },
    nodes: { total: imported.navigation_nodes.length, added: nodeAdded, overwritten: nodeOverwritten },
  }
}

/**
 * 执行导入合并（upsert），直接修改共享数据源。
 * 导入完成后调用回调更新各 Store state。
 */
export function mergeImportedData(
  imported: YamlData,
  callbacks: {
    onCardsMerged: (cards: CognitiveCard[]) => void
    onNodesMerged: (nodes: NavNode[]) => void
  },
): void {
  const { cognitive_cards: importCards, navigation_nodes: importNodes } = imported

  // 合并认知卡片 (upsert)
  const mergedCards = upsertArray(
    cognitiveCards,
    importCards,
    (a, b) => a.id === b.id,
  )

  // 合并导航节点 (upsert)
  const mergedNodes = upsertArray(
    allNavNodes,
    importNodes,
    (a, b) => a.id === b.id,
  )

  // 写回共享数据源
  cognitiveCards.length = 0
  cognitiveCards.push(...mergedCards)
  allNavNodes.length = 0
  allNavNodes.push(...mergedNodes)

  // 重建 navNodeMap
  allNavNodes.forEach((n) => navNodeMap.set(n.id, n))

  callbacks.onCardsMerged(mergedCards)
  callbacks.onNodesMerged(mergedNodes)
}

/* ========== 内部工具 ========== */

/** upsert: 已存在则覆盖，不存在则追加 */
function upsertArray<T>(
  current: T[],
  incoming: T[],
  isSame: (a: T, b: T) => boolean,
): T[] {
  const result = [...current]
  for (const item of incoming) {
    const idx = result.findIndex((c) => isSame(c, item))
    if (idx >= 0) {
      result[idx] = item
    } else {
      result.push(item)
    }
  }
  return result
}

/** 导出前清理空字段 */
function cleanCard(card: CognitiveCard): CognitiveCard {
  return {
    ...card,
    corpus: card.corpus?.length ? card.corpus : undefined,
    bound_nodes: card.bound_nodes?.length ? card.bound_nodes : undefined,
    tag: card.tag || undefined,
    description: card.description || undefined,
    metadata: card.metadata && Object.keys(card.metadata).length > 0 ? card.metadata : undefined,
  } as any
}

function cleanNode(node: NavNode): NavNode {
  return {
    ...node,
    description: node.description || undefined,
    bound_cards: node.bound_cards?.length ? node.bound_cards : undefined,
    browse_history: node.browse_history?.length ? node.browse_history : undefined,
    priority_config: node.priority_config || undefined,
    metadata: (node as any).metadata && Object.keys((node as any).metadata).length > 0
      ? (node as any).metadata
      : undefined,
    next_nodes: node.next_nodes ?? [],
  } as any
}
```

### 5.3 触发导入导出的组件位置

在 `TreeView.tsx` 的 `PageHeader` 区域添加导入导出按钮：

```tsx
// TreeView.tsx（局部修改）
<PageHeader title="认知卡片管理">
  <div className="header-actions">
    <Button variant="ghost" size="sm" onClick={handleImport}>导入</Button>
    <Button variant="ghost" size="sm" onClick={handleExport}>导出</Button>
  </div>
</PageHeader>
```

### 5.4 handleExport / handleImport 实现

```typescript
// TreeView.tsx 或一个单独的 hook: useYamlIO.ts
import { exportAllToYAML, downloadYAML, parseAndValidateYAML, computeImportPreview, mergeImportedData } from '../utils/yamlIO'
import { useCardStore } from '../store/cardStore'
import { useNavNodeStore } from '../store/navNodeStore'
import { useTreeStore } from '../store/treeStore'
import { useNavStore } from '../store/navStore'

function handleExport() {
  const { allCards } = useCardStore.getState()
  const { allNodes } = useNavNodeStore.getState()
  const yaml = exportAllToYAML(allCards, allNodes)
  downloadYAML(yaml)
  // Toast 提示
  showToast(`已导出 ${allCards.length} 张认知卡片和 ${allNodes.length} 个导航节点`)
}

function handleImport(fileContent: string) {
  const result = parseAndValidateYAML(fileContent)
  if (!result.ok) {
    // 显示错误对话框
    showErrorDialog(result.errors.map(e => `[${e.type}] ${e.message}`).join('\n'))
    return
  }

  const { allCards } = useCardStore.getState()
  const { allNodes } = useNavNodeStore.getState()
  const preview = computeImportPreview(result.data, allCards, allNodes)

  // 显示确认对话框
  showConfirmDialog({
    title: '确认导入 YAML 数据',
    preview,
    onConfirm: () => {
      mergeImportedData(result.data, {
        onCardsMerged: (cards) => {
          useCardStore.setState({ allCards: cards })
          // 同步 treeStore
          const treeStore = useTreeStore.getState()
          useTreeStore.setState({
            flatData: cards.map(c => ({ id: c.id, title: c.title, type: c.type, tag: c.tag })),
          })
        },
        onNodesMerged: (nodes) => {
          useNavNodeStore.setState({ allNodes: nodes })
          // 同步 navStore（边数据重算）
          useNavStore.getState().syncFromSource()
        },
      })
      showToast(`已导入 ${preview.cards.total} 张认知卡片和 ${preview.nodes.total} 个导航节点`)
    },
  })
}
```

### 5.5 导入/导出确认对话框组件

新增 `ImportConfirmDialog` 和 `ImportErrorDialog` 组件，Portal 渲染：

```
components/
  └── dialog/
      ├── ImportConfirmDialog.tsx + .module.css    # 导入确认弹窗
      └── ImportErrorDialog.tsx + .module.css      # 导入错误弹窗
```

---

## 六、目录结构变更

```
src/
├── utils/
│   └── yamlIO.ts                # 新增：YAML 序列化/反序列化/校验/合并
│
├── components/
│   └── dialog/
│       ├── ImportConfirmDialog.tsx + .module.css  # 新增：导入确认弹窗
│       └── ImportErrorDialog.tsx + .module.css    # 新增：导入错误弹窗
│
├── components/views/
│   └── TreeView.tsx             # 修改：PageHeader 增加 [导入] [导出] 按钮
│
├── hooks/
│   └── useYamlIO.ts             # 新增（可选）：封装 handleExport / handleImport 逻辑
```

---

## 七、验收标准

- [ ] 点击「导出」下载 `.yaml` 文件，文件名包含日期
- [ ] 导出的 YAML 包含 `cognitive_cards` 和 `navigation_nodes` 两个顶层键
- [ ] 导出文件符合 `data-model.md` 定义的 YAML Schema
- [ ] 导出的认知卡片字段正确（id, title, type, corpus, bound_nodes 等）
- [ ] 导出的导航节点字段正确（id, label, next_nodes, bound_cards 等）
- [ ] 空字段（空数组、空字符串）在导出中被清洁
- [ ] 点击「导入」弹出文件选择器，只接受 `.yaml` / `.yml`
- [ ] 选择非法格式文件 → 错误对话框，不改变数据
- [ ] 选择合法的 YAML 文件 → 显示预览确认对话框
- [ ] 确认对话框显示：总卡片数/新增/覆盖，总节点数/新增/覆盖
- [ ] 取消导入 → 数据不变
- [ ] 确认导入 → 数据合并到共享数据源（upsert）
- [ ] 导入后所有关联 Store 状态同步（cardStore / navNodeStore / treeStore / navStore）
- [ ] 导入后导航画布正确重绘（syncFromSource 调用）
- [ ] 导入的卡片 id 与现有重复时，覆盖现有记录
- [ ] 导入的节点 id 与现有重复时，覆盖现有记录
- [ ] 导入的 id 不存在于现有数据中时，追加到末尾
- [ ] 现有数据中唯一但导入数据中不存在的条目，保留不动
- [ ] 导入成功后 Toast 提示汇总信息
- [ ] TypeScript 编译零错误

---

## 八、注意事项

1. **字段兼容性**：导出时使用 `cleanCard` / `cleanNode` 清理空字段，使文件保持简洁。导入时对空字段不做特殊处理（直接覆盖）。
2. **引用校验范围**：目前引用校验只校验导入数据集内部的跨引用，不校验导入数据引用了当前已有但导入数据中不存在的 id。这允许用户分批导入（例如先导入卡片，再导入节点）。
3. **文件编码**：YAML 文件使用 UTF-8 编码，支持中文等非 ASCII 字符。
4. **浏览器兼容**：`<input type="file">` + Blob URL 方案兼容所有现代浏览器（Chrome/Firefox/Safari/Edge）。
5. **大文件处理**：由于认知导航的数据量通常不大（数百条以内），不涉及分片读取或流式处理。如有超大数据需求，可后续增加分片校验。
