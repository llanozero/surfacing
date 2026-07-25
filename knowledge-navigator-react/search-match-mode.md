# 搜索匹配模式 — 功能规范

## 版本

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| 1.0 | 2026-07-25 | — | 初始规范：新增"关键词匹配"与"向量模型匹配"双模式搜索 |

---

## 一、概述

### 1.1 目标

在现有 **搜索视图（SearchView）** 中增加匹配模式切换功能，用户可在以下两种模式间切换：

1. **关键词匹配**（当前已有） — 在认知卡片的 `title` / `description` / `corpus` 字段中做子串模糊匹配，计算简单评分
2. **向量模型匹配**（新增） — 将用户查询和认知卡片的 `corpus` 字段分别编码为向量，通过余弦相似度计算语义匹配度

两种模式共享同一个搜索入口和结果列表 UI，仅在匹配算法和结果排序上分叉。

### 1.2 对比

| 维度 | 关键词匹配 | 向量模型匹配 |
|------|-----------|-------------|
| 匹配依据 | 文本子串包含关系 | 语义相似度（向量距离） |
| 计算方式 | 前端本地字符串匹配 | 调用后端向量模型 API |
| 响应速度 | 即时（毫秒级） | 依赖网络请求（百毫秒~秒级） |
| 适用场景 | 用户知道确切术语名称 | 用户用自然语言描述概念，模糊搜索 |
| 对 corpus 的利用 | 仅做子串判断 | 利用 corpus 语义内容做相似度计算 |
| 冷启动 | 无依赖 | 需向量模型服务可用 |

---

## 二、UI 交互

### 2.1 模式切换控件

在搜索框上方或搜索框所在行增加模式切换器（ModeToggle），两个模式互斥，当前激活模式高亮显示。

```
┌────────────────────────────────────────────┐
│  ○ 关键词匹配    ● 向量模型匹配            │  ← 模式切换器
├────────────────────────────────────────────┤
│  🔍 输入关键词或自然语言描述...            │  ← SearchBar (不变)
├────────────────────────────────────────────┤
│  匹配的认知卡片 (3)                         │
│  ┌──────────────────────────────────────┐  │
│  │ 📄 监督学习                    92%  │  │
│  │ 使用标注数据训练模型...               │  │
│  ├──────────────────────────────────────┤  │
│  │ 📄 无监督学习                  78%  │  │
│  │ 从未标注数据中发现...                 │  │
│  └──────────────────────────────────────┘  │
└────────────────────────────────────────────┘
```

#### 交互行为

| ID | 功能 | 触发方式 | 预期行为 |
|----|------|----------|----------|
| MM-01 | 切换匹配模式 | 点击模式标签 | 重新执行当前 query 的匹配，清空选中状态，切换标注 |
| MM-02 | 关键词模式 | 选中模式 | 沿用当前 `matchCards` 逻辑，300ms debounce 后执行 |
| MM-03 | 向量模式 | 选中模式 | 调用向量匹配函数，执行结果异步显示，添加 loading 态 |

### 2.2 关键细节

- **向量模式下搜索框 placeholder**：切换为 `"输入自然语言描述，语义匹配语料库..."`，以提示用户该模式支持自然语言输入。
- **匹配度显示**：两种模式均显示 0-100% 匹配度，但颜色/标注可微调以区分模式：
  - 关键词模式：使用现有百分比显示
  - 向量模式：百分比前加 `~` 前缀（如 `~92%`），表示近似语义匹配
- **向量模式加载态**：接口请求期间，结果区域显示加载指示器（skeleton 或 spinner），防止用户重复操作。
- **空结果**：向量模式也显示 `"未找到匹配的认知卡片"`，若接口调用失败则显示错误提示 + 重试按钮。

---

## 三、数据流

### 3.1 匹配模式状态

在 `searchStore` 中新增 `matchMode` 字段：

```typescript
type MatchMode = 'keyword' | 'vector'

interface SearchStore {
  // 已有字段
  query: string
  matchedCards: MatchedCard[]
  selectedCardId: string | null
  boundNodes: NavNode[]
  selectedNodeId: string | null

  // 新增字段
  matchMode: MatchMode          // 当前匹配模式
  isVectorLoading: boolean      // 向量模式加载态
  vectorError: string | null    // 向量模式错误信息

  // 新增方法
  setMatchMode: (mode: MatchMode) => void
}
```

### 3.2 两种匹配路径

```
用户输入 query
       │
       ▼
┌───────────────┐    模式判断    ┌──────────────────┐
│  关键词匹配    │ ←───────────→ │  向量模型匹配     │
│  (前端本地)    │               │  (调用后端 API)   │
└───────┬───────┘               └────────┬─────────┘
        │                                │
        ▼                                ▼
┌──────────────────┐            ┌─────────────────────┐
│ matchCards(query) │            │ vectorMatch(query)  │
│ 遍历 cognitiveCards│            │ 1. 将 query 编码为向量 │
│ 子串匹配 title     │            │ 2. 将每张 card.corpus │
│ description corpus│            │    编码为向量         │
│ 加权评分 0-1      │            │ 3. 计算余弦相似度      │
│ 按 score 降序排列  │            │ 4. 按相似度降序排列    │
└───────┬──────────┘            └──────────┬──────────┘
        │                                │
        └─────────────┬──────────────────┘
                      ▼
           ┌──────────────────┐
           │  matchedCards[]   │
           │  → 渲染到 SearchView │
           └──────────────────┘
```

### 3.3 向量模式接口约定

向量匹配依赖后端 API。约定如下请求/响应格式：

#### 请求

```
POST /api/vector-match
Content-Type: application/json

{
  "query": "使用数据训练模型",
  "corpora": [
    "机器学习是人工智能的一个子领域，使计算机能够从数据中学习和改进。",
    "使用标注数据训练模型，学习从输入到输出的映射函数。",
    "从未标注数据中发现隐藏的模式和结构。"
  ]
}
```

#### 响应

```json
{
  "scores": [
    { "index": 0, "similarity": 0.35 },
    { "index": 1, "similarity": 0.92 },
    { "index": 2, "similarity": 0.78 }
  ]
}
```

说明：
- 请求中的 `corpora` 按传入顺序排列，其中的索引与认知卡片列表的索引一致。
- 实际实现中，`corpora` 传入的应当是所有认知卡片的 `corpus` 字段拼接后的文本列表。
- 响应中 `similarity` 取值 0~1，1 表示语义完全一致。

#### 后端无依赖时的降级策略

若向量模型 API 不可用（后端未部署），可在前端提供一个**模拟向量匹配**实现作为开发/演示用降级：

```typescript
function fallbackVectorMatch(query: string, card: CognitiveCard): number {
  // 降级策略: 将 corpus 分词后计算 query 的词袋重叠率
  const qWords = new Set(query.toLowerCase().split(/[\s,，。、]+/))
  const cWords = card.corpus.flatMap(c => c.toLowerCase().split(/[\s,，。、]+/))
  const cSet = new Set(cWords)
  const intersection = [...qWords].filter(w => w.length > 0 && cSet.has(w))
  return intersection.length / Math.max(qWords.size, 1)
}
```

> 此降级仅为开发阶段占位，生产环境应替换为真实向量模型 API。

---

## 四、接口 / API 设计

### 4.1 searchStore 增量定义

```typescript
// ─── 新增类型 ───

type MatchMode = 'keyword' | 'vector'

interface VectorMatchResult {
  index: number
  similarity: number
}

// ─── searchStore 增量字段与方法 ───

interface SearchStore {
  // ... 现有字段保持不变

  matchMode: MatchMode
  isVectorLoading: boolean
  vectorError: string | null

  setMatchMode: (mode: MatchMode) => void
}

// ─── 向量匹配函数（外部，store 外调用） ───

/** 调用后端向量模型 API 或降级策略，返回每张卡的相似度数组 */
async function vectorMatch(
  query: string,
  cards: CognitiveCard[]
): Promise<MatchedCard[]>
```

### 4.2 setQuery 变更

修改 `setQuery` 方法，在 debounce 回调中根据当前 `matchMode` 选择调用 `matchCards` 或 `vectorMatch`：

```
原有: debounce → matchCards(query) → set matchedCards
变更: debounce → if (mode === 'keyword') matchCards(query)
                 else vectorMatch(query)
               → set matchedCards
```

`vectorMatch` 异步执行：
1. 设置 `isVectorLoading = true`
2. 发送请求到后端
3. 收到响应后计算每张卡的 `score = similarity`，构造 `MatchedCard[]`
4. 按 score 降序排列
5. 设置 `matchedCards`，`isVectorLoading = false`
6. 失败时设置 `vectorError`，清空 `matchedCards`

### 4.3 setMatchMode 行为

1. 更新 `matchMode`
2. 如果当前 `query` 非空，立即以新模式重新执行匹配
3. 清空 `selectedCardId`、`selectedNodeId`、`boundNodes`
4. 清空 `vectorError`

---

## 五、组件变更

### 5.1 新增 ModeToggle 组件

```
search/
  ├── ModeToggle.tsx            ← 新增
  ├── ModeToggle.module.css     ← 新增
  ├── CardMatchItem.tsx          ← 不变
  ├── CardMatchItem.module.css
  ├── BoundNodeItem.tsx
  └── BoundNodeItem.module.css
```

```
<ModeToggle mode={matchMode} onChange={setMatchMode}>
  <Tab active={mode === 'keyword'} value="keyword">
    🔍 关键词匹配
  </Tab>
  <Tab active={mode === 'vector'} value="vector">
    🧠 向量模型匹配
  </Tab>
</ModeToggle>
```

接口：

```typescript
interface ModeToggleProps {
  mode: MatchMode
  onChange: (mode: MatchMode) => void
}
```

### 5.2 SearchView 变更

| 变更项 | 说明 |
|--------|------|
| 插入 ModeToggle | 在 SearchBar 上方或同行插入模式切换器 |
| placeholder 随模式切换 | 关键词: `"搜索认知卡片..."`；向量: `"输入自然语言描述，语义匹配语料库..."` |
| 向量加载态 | 匹配区域显示 spinner / skeleton |
| 错误处理 | 向量匹配失败时显示错误信息 + 重试按钮 |
| 匹配度显示 | 向量模式在百分比前加 `~` 前缀 |

### 5.3 CardMatchItem 变更

- 新增 `matchMode` prop，用于决定是否在百分比前加 `~` 前缀
- 原有的 `Highlight` 高亮在向量模式下可以保留，因为文本片段高亮在语义匹配场景下同样有参考价值

---

## 六、目录结构变更

```
knowledge-navigator-react/src/
  components/
    search/
      ├── ModeToggle.tsx            ← 新增
      ├── ModeToggle.module.css     ← 新增
      ├── CardMatchItem.tsx          ← 微调（matchMode prop）
      ├── CardMatchItem.module.css
      ├── BoundNodeItem.tsx
      └── BoundNodeItem.module.css
  store/
    ├── searchStore.ts             ← 扩展（matchMode / vectorMatch 逻辑）
    └── ...
  utils/
    ├── format.ts
    ├── treeUtils.ts
    ├── weightUtils.ts
    └── vectorMatchUtils.ts        ← 新增：向量匹配工具函数（含 fallback）
```

---

## 七、验收标准

- [ ] 搜索框上方/同行显示"关键词匹配"与"向量模型匹配"两个模式标签
- [ ] 点击模式标签切换匹配模式，重新执行搜索
- [ ] 关键词模式下，300ms debounce 后即时显示匹配结果
- [ ] 向量模式下，显示加载态（spinner / skeleton）
- [ ] 向量模式匹配成功后，结果列表展示匹配度（带 `~` 前缀）
- [ ] 向量模式匹配失败时，显示错误提示 + 重试按钮
- [ ] 切换模式时清空已有选中状态（卡片选中、节点选中）
- [ ] 搜索框 placeholder 跟随模式切换
- [ ] 向量模式 fallback 降级策略可用（后端未部署时）
- [ ] 所有 TypeScript 类型定义正确，编译零错误

---

## 八、与现有功能的兼容性

| 现有功能 | 兼容性 | 说明 |
|----------|--------|------|
| 卡片匹配展示 | ✅ 不变 | 两种模式产出相同的 `MatchedCard[]` 结构 |
| 卡片选中 → 绑定节点查询 | ✅ 不变 | 不依赖匹配算法 |
| 节点选中 → 进入导航 | ✅ 不变 | 不依赖匹配算法 |
| 文本高亮 | ✅ 保留 | 向量模式下仍可高亮文本片段 |
| 空状态 / 无绑定节点 | ✅ 不变 | 沿用现有文案 |
| Tab 切换 / 键盘快捷键 | ✅ 不变 | 不涉及 |
| 后端无向量模型 API | ✅ 降级 | fallbackVectorMatch 提供基础语义匹配 |

---

## 九、后续可扩展方向

1. **混合匹配**：同时执行两种匹配，结果加权合并或分别展示
2. **匹配阈值可调**：用户可拖动滑块调整匹配度下限
3. **向量模型热切换**：支持配置不同的 embedding 模型（如 text2vec、bge、openai 等）
4. **索引缓存**：对 corpus 向量做持久化缓存，减少重复编码请求
