# AI 辅助字段生成 — 功能规范

## 版本

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| 1.0 | 2026-07-25 | — | 初始规范：在管理界面中为认知卡片和导航节点增加 AI 快捷生成按钮 |

---

## 一、概述

在认知卡片和导航节点的**编辑面板**中增加 **AI 生成**按钮，利用当前卡片/节点的关联数据（语料库、子卡片、绑定的认知卡片、前驱/后继节点等），智能生成标题、描述等字段内容，减少用户手动输入的负担。

### 1.1 设计原则

- **辅助而非替代**：所有生成内容均为建议，用户可自由编辑修改，覆盖后即生效
- **有据可依**：生成结果基于当前已有的关联数据，不凭空捏造；数据不足时明确提示
- **轻量优先**：优先使用本地 LLM（通过 `/api/ai-generate` 接口），不可用时降级为规则摘要算法
- **可撤销**：生成后用户可通过 Ctrl+Z 或手动编辑回退（当前的自动保存机制天然支持）

### 1.2 数据来源汇总

| 目标字段 | AI 输入来源 |
|----------|-------------|
| 卡片 title | 卡片自身 corpus + 子卡片 title/description |
| 卡片 description | 卡片自身 corpus + 子卡片 title/description |
| 导航节点 label | 绑定的认知卡片 title + description |
| 导航节点 description | 绑定的认知卡片 corpus + 前驱/后继节点的 description |

---

## 二、认知卡片 — AI 生成

### 2.1 触发入口

在 CardEditPanel 的基本字段区域，标题和描述字段右侧增加 AI 生成按钮：

```
┌──────────────────────────────────────────┐
│  id: root/1/1                    (只读)   │
│                                          │
│  title: [监督学习                 ] [✨]  │  ← ✨ 按钮生成 title
│                                          │
│  description:                             │
│  [使用标注数据训练模型...         ] [✨]  │  ← ✨ 按钮生成 description
│                                          │
│  type: [leaf ▼]   tag: [决策分支 ▼]      │
└──────────────────────────────────────────┘
```

每个 ✨ 按钮点击后，生成对应的字段内容。

### 2.2 卡片 title 生成策略

**输入来源**（按优先级排序）：
1. 当前卡片的 `corpus` 列表（各条语料的文本内容）
2. 当前卡片的子卡片的 `title` 和 `description`（仅当卡片 type 为 folder 时可用）

**AI Prompt 模板**：

```
你是一个知识卡片标题生成助手。

根据以下数据，生成一个简洁、准确的卡片标题（10 个字符以内）：

卡片语料库：
{每条语料逐行列出}

子卡片标题与描述：
{每个子卡片的 title + description 逐行列出}

请直接输出标题，不要有任何额外说明。
```

**降级算法**（AI 不可用时）：

```typescript
function generateCardTitle(card: CognitiveCard, children: CognitiveCard[]): string {
  // 1. 尝试从语料库提取最频繁的名词短语
  if (card.corpus.length > 0) {
    const allText = card.corpus.join(' ')
    // 提取第一个句子的前 10 个字作为默认
    const firstSentence = allText.split(/[。！？\n]/)[0]
    if (firstSentence.length <= 10) return firstSentence
    return firstSentence.slice(0, 8) + '…'
  }

  // 2. 无语料时聚合子卡片标题
  if (children.length > 0) {
    const childTitles = children.map(c => c.title)
    // 取子卡片标题中的共同前缀或高频词
    return aggregateTitle(childTitles)
  }

  // 3. 完全无数据
  return '新建卡片'
}
```

### 2.3 卡片 description 生成策略

**输入来源**：
1. 当前卡片的 `corpus` 列表（主要来源）
2. 当前卡片的子卡片的 `description`（补充）

**AI Prompt 模板**：

```
你是一个知识卡片描述生成助手。

根据以下数据，生成一段 1-2 句话的卡片描述（50-100 字），
简洁概述卡片的核心内容：

卡片标题：{title}
卡片语料库：
{每条语料逐行列出}

子卡片描述：
{每个子卡片的 description 逐行列出}

请直接输出描述文本。
```

**降级算法**：

```typescript
function generateCardDescription(card: CognitiveCard, children: CognitiveCard[]): string {
  const sources: string[] = []

  // 1. 从语料库拼接前两条语料各取第一句
  for (const text of card.corpus.slice(0, 2)) {
    const firstSentence = text.split(/[。！？\n]/)[0]
    if (firstSentence) sources.push(firstSentence)
  }

  // 2. 语料不足时补充子卡片描述
  if (sources.length < 2) {
    for (const child of children.slice(0, 3)) {
      if (child.description) sources.push(child.description)
    }
  }

  if (sources.length === 0) return `${card.title}相关知识点。`
  return sources.join('；') + '。'
}
```

### 2.4 交互流程

```
用户点击 title 旁的 ✨ 按钮
    │
    ▼
显示加载态：按钮变为旋转动画
    │
    ├─ 尝试调用 POST /api/ai-generate { type: 'card-title', cardId, ... }
    │       │
    │       ├─ 成功 → 将返回的文本填入 title 输入框
    │       │           → 触发自动保存（onChange → updateField）
    │       │           → Toast: "已生成标题"
    │       │
    │       └─ 失败（超时/无后端）
    │               │
    │               └─ 执行轻量降级算法 → 填入 title → Toast: "已生成标题（轻量模式（lite））"
    │
    └─ 生成完毕，按钮恢复为 ✨
```

### 2.5 特殊情况

| 场景 | 行为 |
|------|------|
| 卡片无语料、无子卡片 | 按钮置灰，hover 提示"缺少生成依据，请先添加语料或子卡片" |
| 生成结果超过字段长度限制 | title 超 10 字自动截断并在末尾加… |
| 生成结果为空串 | 不填充，Toast 提示"生成失败，请重试" |
| 连续快速点击生成 | 每次生成覆盖上一次结果，不做去重 |
| type 为 leaf 但选择了"从子卡片生成" | 按钮置灰（leaf 无子卡片） |

---

## 三、导航节点 — AI 生成

### 3.1 触发入口

在 NodeEditPanel 的基本字段区域，label 和 description 字段右侧增加 AI 生成按钮：

```
┌──────────────────────────────────────────┐
│  id: node-ml-foundation          (只读)   │
│                                          │
│  label: [机器学习基础             ] [✨]  │  ← ✨ 生成 label
│                                          │
│  description:                             │
│  [涵盖监督学习、无监督学习...    ] [✨]  │  ← ✨ 生成 description
│                                          │
│  绑定卡片：root/1 机器学习                 │
│            root/1/1 监督学习              │
│  前驱节点：概率论                          │
│  后继节点：监督学习、无监督学习            │
└──────────────────────────────────────────┘
```

### 3.2 导航节点 label 生成策略

**输入来源**（按优先级合并）：
1. 绑定的认知卡片的 `title` 列表（主要来源）
2. 绑定的认知卡片的 `description`（补充语义）

**AI Prompt 模板**：

```
你是一个导航节点标签生成助手。

根据以下绑定的认知卡片信息，生成一个简洁的导航节点标签名（8 个字以内），
作为知识路径中的一个"站点"名称：

绑定卡片标题：
{每个绑定卡片的 title 逐行列出}

绑定卡片描述：
{每个绑定卡片的 description 逐行列出}

请直接输出标签名。
```

**降级算法**：

```typescript
function generateNodeLabel(node: NavNode, boundCards: CognitiveCard[]): string {
  if (boundCards.length === 0) return node.label // 保持原名

  // 1. 如果只绑定一张卡片，直接使用该卡片的 title
  if (boundCards.length === 1) return boundCards[0].title

  // 2. 多张卡片：取标题中最长的公共子串或首个共同词
  const titles = boundCards.map(c => c.title)
  const common = findLongestCommonPrefix(titles)
  if (common && common.length >= 2) return common

  // 3. 无公共前缀：拼接前两个卡片的标题
  return `${titles[0]}·${titles[1]}`
}
```

### 3.3 导航节点 description 生成策略

**输入来源**：
1. 绑定的认知卡片的 `corpus` 列表（主要来源）
2. 绑定的认知卡片的 `description`（补充）
3. 前驱导航节点的 `description`（上下文补充）
4. 后继导航节点的 `description`（上下文补充）

**AI Prompt 模板**：

```
你是一个导航节点描述生成助手。

根据以下数据，生成一段 1-2 句话的节点描述（50-80 字），
说明该节点在认知导航路径中的定位和核心内容：

节点标签：{label}
绑定的认知卡片语料：
{每个绑定卡片的 corpus 逐卡片列出}
绑定的认知卡片描述：
{每个绑定卡片的 description 逐卡片列出}

前驱节点（上一个站点）：
{前驱节点 label}：{前驱节点 description}

后继节点（可跳转的下一个站点）：
{每个后继节点 label}：{后继节点 description}

请直接输出描述文本。
```

**降级算法**：

```typescript
function generateNodeDescription(
  node: NavNode,
  boundCards: CognitiveCard[],
  prevNodes: NavNode[],
  nextNodes: NavNode[],
): string {
  const parts: string[] = []

  // 1. 从绑定卡片的描述中提取
  const cardDescs = boundCards
    .map(c => c.description)
    .filter(Boolean) as string[]
  if (cardDescs.length > 0) {
    parts.push(cardDescs.slice(0, 2).join('；'))
  }

  // 2. 补充前驱/后继上下文
  if (prevNodes.length > 0) {
    parts.push(`承接${prevNodes[0].label}`)
  }
  if (nextNodes.length > 0) {
    const nextLabels = nextNodes.slice(0, 3).map(n => n.label).join('、')
    parts.push(`可跳转至${nextLabels}`)
  }

  if (parts.length === 0) return node.description || `${node.label}导航节点。`
  return parts.join('。') + '。'
}
```

### 3.4 生成时数据不足的判断

| 生成目标 | 数据是否充足 | 判断条件 |
|----------|-------------|----------|
| 节点 label | 充足 | `bound_cards` 长度 >= 1 |
| 节点 description | 充足 | 任意来源有数据：bound_cards corpus/desc、前驱/后继节点 desc |
| 节点 label/description | 不足 | 无绑定卡片、无任何关联数据 |

数据不足时按钮置灰，hover 提示"缺少生成依据，请先绑定认知卡片"。

---

## 四、后端 API 接口

### 4.1 POST /api/ai-generate

与 `vectorMatchUtils.ts` 中 `/api/vector-match` 使用相同的后端约定，保持一致性。

**请求**：

```json
{
  "type": "card-title" | "card-description" | "node-label" | "node-description",
  "context": {
    "cardId": "root/1/1",
    "title": "监督学习",
    "corpus": [
      "使用标注数据训练模型，学习从输入到输出的映射函数。",
      "常见算法包括线性回归、逻辑回归、SVM、决策树和神经网络。"
    ],
    "childCards": [
      { "title": "线性回归", "description": "..." },
      { "title": "逻辑回归", "description": "..." }
    ],
    "boundCards": [
      { "title": "监督学习", "description": "...", "corpus": ["..."] }
    ],
    "prevNodes": [
      { "label": "机器学习基础", "description": "..." }
    ],
    "nextNodes": [
      { "label": "深度学习", "description": "..." }
    ]
  },
  "prompt": "（可选的完全自定义 prompt，覆盖 type 的默认模板）"
}
```

**成功响应**：

```json
{
  "ok": true,
  "result": "生成的标题文本"
}
```

**失败响应**：

```json
{
  "ok": false,
  "error": "错误描述"
}
```

**超时**：5s（与 vectorMatch 一致），超时则降级为本地算法。

### 4.2 API 调用 Hook

新建 `src/hooks/useAiGenerate.ts`，封装生成逻辑：

```typescript
interface UseAiGenerateReturn {
  /** 是否为生成中状态 */
  generating: boolean
  /** 生成卡片标题 */
  generateCardTitle: (card: CognitiveCard, children: CognitiveCard[]) => Promise<string | null>
  /** 生成卡片描述 */
  generateCardDescription: (card: CognitiveCard, children: CognitiveCard[]) => Promise<string | null>
  /** 生成导航节点标签 */
  generateNodeLabel: (node: NavNode, boundCards: CognitiveCard[]) => Promise<string | null>
  /** 生成导航节点描述 */
  generateNodeDescription: (
    node: NavNode,
    boundCards: CognitiveCard[],
    prevNodes: NavNode[],
    nextNodes: NavNode[],
  ) => Promise<string | null>
}
```

内部实现模式：

```
try {
  const res = await fetch('/api/ai-generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ type, context }),
    signal: AbortSignal.timeout(5000),
  })
  const data = await res.json()
  if (data.ok) return data.result
  throw new Error(data.error)
} catch {
  // 降级：执行本地算法
  return fallbackFn(context)
}
```

---

## 五、UI 组件变更

### 5.1 CardEditPanel 变更

在 `CardEditPanel.tsx` 的 title 和 description 字段旁各增加一个 AI 生成按钮：

```tsx
// CardEditPanel.tsx（局部修改）
import { useAiGenerate } from '../../hooks/useAiGenerate'

// ...

const { generating, generateCardTitle, generateCardDescription } = useAiGenerate()
const cardStore = useCardStore()
const treeStore = useTreeStore()

const handleGenTitle = async () => {
  const children = deriveChildren(cardStore.allCards, card.id)
    .map(id => cardStore.allCards.find(c => c.id === id)!)
    .filter(Boolean)
  const result = await generateCardTitle(card, children)
  if (result) {
    cardStore.updateField(card.id, 'title', result)
    toast('已生成标题' + (result.length > 10 ? '（已截断）' : ''))
  }
}

// JSX
<div className={mgrStyles.fieldRow}>
  <span className={mgrStyles.fieldLabel}>标题</span>
  <input ... />
  <button
    className={styles.aiButton}
    onClick={handleGenTitle}
    disabled={generating || (card.corpus.length === 0 && deriveChildren(...).length === 0)}
    title={!hasData ? '缺少生成依据，请先添加语料或子卡片' : ''}
  >
    {generating ? '⏳' : '✨'}
  </button>
</div>
```

### 5.2 NodeEditPanel 变更

在 `NodeEditPanel.tsx` 的 label 和 description 字段旁各增加一个 AI 生成按钮：

```tsx
// NodeEditPanel.tsx（局部修改）
import { useAiGenerate } from '../../hooks/useAiGenerate'

// ...

const { generating, generateNodeLabel, generateNodeDescription } = useAiGenerate()

const handleGenLabel = async () => {
  const boundCards = (node.bound_cards ?? [])
    .map(id => allCards.find(c => c.id === id))
    .filter(Boolean) as CognitiveCard[]
  const result = await generateNodeLabel(node, boundCards)
  if (result) {
    updateField('label', result)
    toast('已生成标签')
  }
}
```

### 5.3 样式

AI 按钮样式：

```css
/* CardEditPanel.module.css / NodeMgr.module.css */
.aiButton {
  background: var(--accent-subtle, #e8f4fd);
  border: 1px solid var(--accent, #4a9eff);
  border-radius: 6px;
  padding: 4px 8px;
  cursor: pointer;
  font-size: 14px;
  line-height: 1;
  transition: all 0.2s;
  flex-shrink: 0;
}
.aiButton:hover:not(:disabled) {
  background: var(--accent, #4a9eff);
  color: #fff;
}
.aiButton:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
```

---

## 六、错误处理与边界情况

| 场景 | 行为 |
|------|------|
| 后端 API 返回 `ok: false` | 降级到轻量算法，Toast 提示"已生成（轻量模式（lite））" |
| 后端 API 超时（5s） | 同降级策略 |
| 轻量降级算法也无法生成 | 按钮恢复可用，不做填充，Toast "生成失败" |
| 用户快速重复点击生成 | 每次独立请求，每次覆盖当前字段内容 |
| 生成中切换选中卡片 | 取消未完成的 fetch（AbortController），按钮恢复 |
| 生成后用户手动编辑 | 与自动保存机制一致，直接覆盖字段值 |
| 数据源在生成过程中变更 | 以当前最新数据为准，生成时 getState() 取最新值 |
| 无后端且无本地算法（初次迭代） | 按钮显示但点击后直接 Toast "AI 生成功能暂不可用" |

---

## 七、目录结构变更

```
src/
├── hooks/
│   └── useAiGenerate.ts             ← 新增：AI 生成 Hook
│
├── utils/
│   └── aiFallback.ts                ← 新增：本地降级算法（摘要/聚合）
│
├── components/tree/
│   └── CardEditPanel.tsx            ← 修改：增加 AI 生成按钮
│
├── components/node-mgr/
│   ├── NodeEditPanel.tsx            ← 修改：增加 AI 生成按钮
│   └── NodeMgr.module.css           ← 修改：增加 .aiButton 样式
│
└── data/
    └── types.ts                     ← 可选：增加 AiGenerateRequest / AiGenerateResponse 类型
```

---

## 八、降级算法文件详述

`src/utils/aiFallback.ts` 包含所有本地降级算法的实现：

| 函数 | 输入 | 输出 |
|------|------|------|
| `fallbackCardTitle(card, children)` | 当前卡片 + 子卡片列表 | 生成的标题字符串 |
| `fallbackCardDescription(card, children)` | 当前卡片 + 子卡片列表 | 生成的描述字符串 |
| `fallbackNodeLabel(node, boundCards)` | 当前节点 + 绑定的卡片列表 | 生成的标签字符串 |
| `fallbackNodeDescription(node, boundCards, prevNodes, nextNodes)` | 当前节点 + 绑定卡片 + 前驱/后继节点 | 生成的描述字符串 |

每个降级函数在输入数据不足时返回 `null`，调用方据此判断是否显示错误提示。

---

## 九、验收标准

- [ ] 认知卡片编辑面板中，title 和 description 字段旁显示 ✨ 按钮
- [ ] 卡片无语料且无子卡片时，✨ 按钮置灰，hover 显示提示
- [ ] 点击卡片 title 的 ✨ 按钮 → 基于语料库生成标题 → 填入输入框 → Toast 提示
- [ ] 卡片 type 为 folder 且无语料但有子卡片时 → 基于子卡片 title/desc 生成
- [ ] 点击卡片 description 的 ✨ 按钮 → 基于语料库生成描述 → 填入文本域
- [ ] 生成过程中按钮显示加载态（不可点击）
- [ ] 后端 API 不可用时降级为本地算法，Toast 标注"轻量模式（lite）"
- [ ] 导航节点编辑面板中，label 和 description 字段旁显示 ✨ 按钮
- [ ] 节点无绑定卡片时，✨ 按钮置灰，hover 显示提示
- [ ] 点击节点 label 的 ✨ 按钮 → 基于绑定卡片 title 生成标签
- [ ] 点击节点 description 的 ✨ 按钮 → 基于绑定卡片语料 + 前驱/后继生成描述
- [ ] 节点 description 生成时使用了前驱/后继节点的上下文
- [ ] 快速重复点击生成 → 每次独立请求，覆盖上一次结果
- [ ] 生成中切换编辑对象 → 取消未完成的请求
- [ ] TypeScript 编译零错误

---

## 十、后续可扩展方向

1. **批量生成**：在树形管理中选中多张卡片/节点，批量生成所有选中项的字段
2. **自定义 Prompt**：在编辑面板中开放 Prompt 编辑入口，用户可自定义生成指令
3. **生成历史**：保留最近的生成记录，支持一键回退到上一次生成结果
4. **多模型切换**：支持选择不同的 LLM 后端（本地 / 云端 / 不同模型）
5. **阈值过滤**：生成的 title/description 与现有内容的相似度低于阈值时，自动丢弃并提示
6. **骨架生成**：对于完全空白的卡片/节点，基于其位置（树层级/导航路径中的位置）推断应属的内容领域并生成初始字段
