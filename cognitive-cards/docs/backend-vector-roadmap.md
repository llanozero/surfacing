# 认知卡片 · 后端向量化推进路线图

> 参考 AstrBot 向量数据库实现 (`core/db/vec_db/faiss_impl/`) 与知识库检索管道 (`core/knowledge_base/`)，将当前 JSON-in-memory 原型升级为 FAISS + SQLite FTS5 混合检索引擎。

---

## 1. 现状评估

### 1.1 当前架构（v1 原型）

```
server.py (单文件, 715行)
├── DataService       — JSON 文件加载, 内存索引
├── EmergenceEngine  — 三阶段管道 (纯 Python)
│   ├── match_cards()   — Jaccard 2-gram 关键词相似度
│   ├── refine_corpus() — quality_score + keyword_match 加权
│   └── emerge_guidance() — 模板拼接引导词
└── FastAPI routes   — /api/cards, /api/kits, /api/emergence, /api/archive
```

**局限**：
- 关键词匹配粗糙，不支持语义相似度
- 语料库无向量化，无法做语义级细化
- 单文件架构，无法分离关注点
- 无降级方案（LLM 不可用时直接报错）

### 1.2 目标架构（v2）

```
server.py                   — FastAPI 应用入口 + 路由注册
├── app/
│   ├── config.py           — 全局配置（路径、模型、参数）
│   ├── models.py           — Pydantic 模型 + 数据库模型
│   │
│   ├── services/
│   │   ├── embedding.py    — EmbeddingService: 统一调度, 批量/单条, 降级
│   │   ├── card_store.py   — CardStore: 卡片 CRUD, 层级树管理
│   │   ├── corpus_store.py — CorpusStore: 语料入库、索引、查询
│   │   └── kit_service.py  — KitService: 锦囊路径规则引擎
│   │
│   ├── engine/
│   │   ├── matcher.py      — Stage1: 向量语义匹配（替换 Jaccard）
│   │   ├── refiner.py      — Stage2: 混合检索语料细化
│   │   ├── emergence.py    — Stage3: LLM 驱动 / 模板降级引导词
│   │   └── merger.py       — RankFusion: RRF 混合排序
│   │
│   ├── vec_db/             — 向量数据库层 (参考 AstrBot)
│   │   ├── base.py         — BaseVecDB 抽象, Result 结构
│   │   ├── faiss_store.py  — FAISS 索引 + SQLite 文档存储
│   │   ├── doc_storage.py  — DocumentStorage (SQLite + FTS5)
│   │   ├── embed_storage.py— EmbeddingStorage (FAISS 读写)
│   │   └── sql_init.py     — 建表 DDL
│   │
│   └── provider/
│       └── openai_embed.py — OpenAI 兼容 Embedding Provider
│
├── data/
│   ├── cards.json          — 卡片种子数据（不变）
│   ├── corpus.json         — 语料种子数据（会被索引）
│   └── index/              — 向量索引持久化目录
│       ├── cards/
│       │   ├── doc.db      — 卡片文档 SQLite
│       │   └── index.faiss — 卡片向量 FAISS 索引
│       └── corpus/
│           ├── doc.db      — 语料文档 SQLite
│           └── index.faiss — 语料向量 FAISS 索引
│
└── static/
    └── index.html          — 前端 SPA（不变）
```

---

## 2. 核心模块设计

### 2.1 EmbeddingService（`app/services/embedding.py`）

参考 AstrBot 的 `OpenAIEmbeddingProvider` 和 `EmbeddingProvider.get_embeddings_batch()`。

```python
class EmbeddingService:
    """嵌入服务：统一管理向量化请求, 支持批量、降级和缓存。"""

    def __init__(self, config: EmbeddingConfig):
        self.client = openai.AsyncOpenAI(
            base_url=config.api_base,   # http://localhost:1234/v1 (LM Studio)
            api_key=config.api_key,     # lm-studio
            timeout=config.timeout,     # 20s
        )
        self.model = config.model       # text-embedding-nomic-embed-text-v1.5
        self.dim = config.dimensions    # 768
        self.batch_size = 16            # 单次请求最多 16 条
        self.max_concurrent = 3         # 并发请求数
        self.max_retries = 3            # 指数退避重试
        self._available = True          # 是否可用（用于降级）
        self._cache: dict[str, list[float]] = {}  # 文本 → 向量缓存

    async def embed(self, text: str) -> list[float]:
        """单条向量化，优先从缓存读取。"""
        if text in self._cache:
            return self._cache[text]
        if not self._available:
            return []  # 降级：返回空向量, 上游用关键词匹配
        try:
            resp = await self.client.embeddings.create(
                input=text, model=self.model,
                dimensions=self.dim if self.dim else NOT_GIVEN,
            )
            vec = resp.data[0].embedding
            self._cache[text] = vec
            return vec
        except Exception:
            self._available = False
            return []

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量向量化，带并发控制、重试和进度回调。"""
        if not self._available:
            return [[]] * len(texts)
        results = [None] * len(texts)
        sem = asyncio.Semaphore(self.max_concurrent)

        async def _batch(start, end):
            async with sem:
                for attempt in range(self.max_retries):
                    try:
                        batch = texts[start:end]
                        resp = await self.client.embeddings.create(
                            input=batch, model=self.model,
                            dimensions=self.dim if self.dim else NOT_GIVEN,
                        )
                        for i, d in enumerate(resp.data):
                            idx = start + d.index
                            results[idx] = d.embedding
                            self._cache[texts[idx]] = d.embedding
                        return
                    except Exception:
                        if attempt == self.max_retries - 1:
                            self._available = False
                        await asyncio.sleep(2 ** attempt)

        tasks = []
        for i in range(0, len(texts), self.batch_size):
            tasks.append(_batch(i, min(i + self.batch_size, len(texts))))
        await asyncio.gather(*tasks)
        return results

    async def health_check(self) -> bool:
        """启动时用空字符串测试连通性, 设置 available 标志。"""
        try:
            await self.embed("health_check")
            self._available = True
            return True
        except Exception:
            self._available = False
            return False
```

**关键点**：
- 缓存层：卡片和语料的标题/正文在启动时批量向量化后永久缓存，避免重复 API 调用
- 降级标志：单次失败后 `self._available = False`，上游自动切换关键词匹配
- 批量与并发：参考 AstrBot 的 `Semaphore(3)` + `batch_size=16` 模式

### 2.2 向量数据库层（`app/vec_db/`）

参考 AstrBot 的 `FaissVecDB` + `DocumentStorage` + `EmbeddingStorage` 三层分离。

#### 2.2.1 `base.py` — 抽象接口

```python
from dataclasses import dataclass

@dataclass
class VecResult:
    doc_id: str          # 文档 UUID
    score: float         # 相似度 [0, 1]
    metadata: dict       # 原始元数据
    text: str            # 原始文本

class BaseVecDB(ABC):
    async def init(self): ...
    async def insert(self, doc_id: str, text: str, metadata: dict, embedding: list[float]): ...
    async def insert_batch(self, items: list[tuple[str, str, dict, list[float]]]): ...
    async def search(self, query_embedding: list[float], top_k: int, metadata_filter: dict | None) -> list[VecResult]: ...
    async def delete(self, doc_ids: list[str]): ...
    async def count(self) -> int: ...
    async def close(self): ...
```

#### 2.2.2 `doc_storage.py` — SQLite + FTS5

参考 AstrBot 的 `document_storage.py`(804行)，精简为本项目所需的最小集。

```sql
-- SQLite 建表 DDL
CREATE TABLE IF NOT EXISTS documents (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id   TEXT    NOT NULL UNIQUE,   -- UUID
    text     TEXT    NOT NULL,
    metadata TEXT,                       -- JSON: {card_id, corpus_id, type, ...}
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- FTS5 全文索引 (用于稀疏检索)
CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
    text,
    content='documents',
    content_rowid='id',
    tokenize='unicode61'
);
```

核心方法：

```python
class DocumentStorage:
    def __init__(self, db_path: str):
        self.engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
        # 启动时建表

    async def insert(self, doc_id: str, text: str, metadata: dict) -> int:
        """插入一条文档，返回自增 id"""
        ...

    async def insert_batch(self, items) -> list[int]:
        """批量插入, 返回 id 列表"""
        ...

    async def get_by_ids(self, ids: list[int]) -> list[dict]:
        """按自增 id 批量查询文档"""
        ...

    async def search_fts(self, query_tokens: list[str], limit: int) -> list[tuple[int, float]]:
        """FTS5 BM25 全文检索 → [(doc_rowid, bm25_score), ...]"""
        # 构造 MATCH 查询: token1 OR token2 OR ...
        query_str = " OR ".join(query_tokens)
        sql = """
            SELECT rowid, bm25(documents_fts) AS score
            FROM documents_fts
            WHERE documents_fts MATCH ?
            ORDER BY score
            LIMIT ?
        """
        ...

    async def delete_by_doc_id(self, doc_id: str):
        """删除文档及其 FTS5 索引"""
        ...
```

**差异**（vs AstrBot）：
- 去掉 SQLAlchemy + SQLModel 重量依赖，直接用 `aiosqlite` 原生 SQL
- 去掉 group_id/user_id 提取（本项目无多租户需求）
- FTS5 tokenizer 保留 `unicode61`（中文支持已足够）
- Stopwords 从 `hit_stopwords.txt` 初始化时加载，预处理用户查询

#### 2.2.3 `embed_storage.py` — FAISS 索引

参考 AstrBot 的 `embedding_storage.py`(95行)，基本完全复用。

```python
class EmbeddingStorage:
    def __init__(self, index_path: str, dimension: int):
        self.path = index_path
        self.dim = dimension
        if os.path.exists(index_path):
            self.index = faiss.read_index(index_path)
        else:
            self.index = faiss.IndexIDMap(faiss.IndexFlatL2(dimension))

    def insert(self, vectors: np.ndarray, ids: np.ndarray):
        """vectors shape=(n, dim), ids shape=(n,) int64"""
        self.index.add_with_ids(vectors.astype(np.float32), ids.astype(np.int64))
        self._save()

    def search(self, query_vec: list[float], top_k: int) -> tuple[np.ndarray, np.ndarray]:
        """返回 (distances, indices)"""
        q = np.array([query_vec], dtype=np.float32)
        faiss.normalize_L2(q)
        return self.index.search(q, top_k)

    def delete(self, ids: list[int]):
        self.index.remove_ids(np.array(ids, dtype=np.int64))
        self._save()

    def _save(self):
        faiss.write_index(self.index, self.path)

    def count(self) -> int:
        return self.index.ntotal
```

**关键点**：
- FAISS Index 选择 `IndexFlatL2`（精确搜索），因为卡片+语料规模不超过 10万条，无需近似索引
- `IndexIDMap` 包装支持任意 int ID（对应 SQLite 的 rowid），保证删除操作不破坏映射
- `faiss.normalize_L2` → L2 距离转余弦相似度

#### 2.2.4 `faiss_store.py` — FaissVecDB 编排

参考 AstrBot 的 `vec_db.py`(294行)，组合 doc_storage + embed_storage。

```python
class FaissVecDB(BaseVecDB):
    def __init__(self, doc_path: str, index_path: str, dim: int):
        self.docs = DocumentStorage(doc_path)
        self.embeddings = EmbeddingStorage(index_path, dim)

    async def init(self):
        await self.docs._ensure_tables()

    async def insert_batch(self, items: list[tuple[str, str, dict, list[float]]]):
        doc_items = []  # (doc_id, text, metadata_json)
        vectors = []
        for doc_id, text, meta, vec in items:
            doc_items.append((doc_id, text, json.dumps(meta)))
            vectors.append(vec)
        row_ids = await self.docs.insert_batch(doc_items)
        self.embeddings.insert(np.array(vectors), np.array(row_ids, dtype=np.int64))

    async def search(self, query_vec: list[float], top_k: int,
                     metadata_filter: dict = None) -> list[VecResult]:
        distances, indices = self.embeddings.search(query_vec, top_k * 2)
        ids = [int(i) for i in indices[0] if i >= 0]
        if not ids:
            return []
        docs = await self.docs.get_by_ids(ids)
        results = []
        for i, doc in enumerate(docs):
            score = 1.0 - (distances[0][i] / 2.0)  # L2 → 余弦相似度
            results.append(VecResult(
                doc_id=doc["doc_id"],
                score=round(score, 4),
                metadata=json.loads(doc["metadata"]),
                text=doc["text"],
            ))
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]
```

### 2.3 RankFusion（`app/engine/merger.py`）

参考 AstrBot 的 `retrieval/rank_fusion.py`(142行)，RRF `k=60`。

```python
class RankFusion:
    def __init__(self, k: int = 60):
        self.k = k

    def fuse(
        self,
        dense_results: list[VecResult],   # 稠密检索结果
        sparse_results: list[VecResult],  # 稀疏检索结果
        top_k: int = 20,
    ) -> list[VecResult]:
        """Reciprocal Rank Fusion 混合排序"""
        # 构建 rank 映射: {doc_id: position}
        dense_ranks = {r.doc_id: i + 1 for i, r in enumerate(dense_results)}
        sparse_ranks = {r.doc_id: i + 1 for i, r in enumerate(sparse_results)}

        all_ids = set(dense_ranks) | set(sparse_ranks)
        scored = {}
        for doc_id in all_ids:
            rrf = 0.0
            if doc_id in dense_ranks:
                rrf += 1.0 / (self.k + dense_ranks[doc_id])
            if doc_id in sparse_ranks:
                rrf += 1.0 / (self.k + sparse_ranks[doc_id])
            # 取存在于任一结果集中的原始记录
            for r in dense_results + sparse_results:
                if r.doc_id == doc_id:
                    scored[doc_id] = (rrf, r)
                    break

        ranked = sorted(scored.values(), key=lambda x: x[0], reverse=True)
        return [r for _, r in ranked[:top_k]]
```

### 2.4 涌现引擎重写（`app/engine/`）

#### 2.4.1 `matcher.py` — Stage1 语义匹配（替换 Jaccard）

**当前**：2-gram Jaccard 关键词相似度  
**升级后**：向量相似度 + 状态检测 + LLM 排序（可选）

```
用户输入
    │
    ├──→ EmbeddingService.embed(user_text)  → query_vec
    │
    ├──→ FaissVecDB.search(query_vec, top_k=5)  → 稠密检索 TOP-5 卡片
    │     (卡片 keywords + sections 文本的向量已在启动时索引)
    │
    ├──→ DocumentStorage.search_fts(tokenize(user_text), limit=5)  → 稀疏检索 TOP-5
    │
    ├──→ RankFusion.fuse(dense, sparse, top_k=3)  → TOP-3 融合卡片
    │
    └──→ (可选) LLM 排序 + 匹配理由生成
          → 降级: 直接返回 Top-3 融合结果 + 预设理由
```

**卡片向量化策略**：
- 对每张卡片的 `{title} | {keywords} | {sections.insight}` 拼接后向量化
- 启动时批量嵌入，存入 `data/index/cards/` 的 FAISS 索引
- 语料条目同理，存入 `data/index/corpus/` 的独立 FAISS 索引

#### 2.4.2 `refiner.py` — Stage2 混合检索语料细化

**当前**：纯 keyword_match + quality_score 加权  
**升级后**：语义向量检索 + BM25 关键词检索 → RRF 融合

```
matched_card_id
    │
    ├──→ CorporaVecDB.search(query_vec, top_k=10)
    │      metadata_filter: {card_id: matched_card_id}
    │      → 稠密语义 TOP-10
    │
    ├──→ CorporaDocStorage.search_fts(query_tokens, limit=10)
    │      WHERE json_extract(metadata, '$.card_id') = matched_card_id
    │      → 稀疏关键词 TOP-10
    │
    └──→ RankFusion.fuse(dense, sparse, top_k=5)
           → quality_score × 0.4 + style_match × 0.3 + fusion_score × 0.3
           → TOP-5 细化语料
```

**与 AstrBot 的关键差异**：
- AstrBot 检索的是文档 chunks，本项目检索的是语料条目（精炼片段，非分块文档）
- 语料条目短（200-500字），不需要 chunking，每条直接对应一个向量
- 混合检索的 `metadata_filter` 用于按 `card_id` 过滤（支持语料继承）

#### 2.4.3 `emergence.py` — Stage3 锦囊生成

**当前**：模板拼接（硬编码引导词 + 语料引用）  
**升级后**：LLM 驱动 / 模板降级双路径

```
refined_corpus (TOP-5 语料)
    + kit_definitions (锦囊骨架)
    + user_state_analysis (心态 + 位置 + 风险)
    │
    ├──→ [可用] LLM 调用 (OpenAI 兼容 chat/completions)
    │      system_prompt: 认知引导词生成器 (定义见设计文档 §7.2)
    │      → guidance_text + body_action + style_note
    │
    └──→ [不可用] 模板降级
           → 取 TOP-1 语料内容 + 锦囊 body[1] + 随机身体动作指令
           → guidance_text
```

**LLM 提示词模板**（精简版，完整版见 `涌现引擎.md` §7.2）：

```python
EMERGENCE_SYSTEM_PROMPT = """你是一个认知引导词生成器。

引导词规则：
1. 使用感官意象，不使用抽象概念
2. 必须包含一个身体动作指令
3. 参考语料风格但不要直接复制
4. 引导词长度控制在 150 字以内
5. 不要使用"你应该"、"你需要"等指令性语言

当前用户状态：{user_state}
匹配的认知卡片：{matched_card_title} — {matched_card_insight}
参照的语料风格：{corpus_samples}

请生成 JSON 格式：
{{"guidance_text": "...", "body_action": "..."}}
"""
```

### 2.5 索引初始化与热启动

```python
# app/services/embedding.py

class IndexBootstrap:
    """启动时批量向量化卡片和语料，建立 FAISS 索引。"""

    def __init__(self, embed_svc: EmbeddingService):
        self.embed = embed_svc
        self.card_db = FaissVecDB("data/index/cards/doc.db", "data/index/cards/index.faiss", dim=768)
        self.corpus_db = FaissVecDB("data/index/corpus/doc.db", "data/index/corpus/index.faiss", dim=768)

    async def bootstrap(self, cards: list[Card], corpus: list[CorpusEntry]):
        # 1. 检查索引是否已存在 (avoid re-indexing on restart)
        if await self.card_db.count() == len(cards):
            logger.info("卡片向量索引已存在，跳过")
        else:
            texts = [f"{c.title} | {' '.join(c.keywords)} | {c.sections.insight}" for c in cards]
            vecs = await self.embed.embed_batch(texts)
            items = [(c.id, texts[i], {"type": "card"}, vecs[i]) for i, c in enumerate(cards)]
            await self.card_db.insert_batch(items)

        # 2. 语料索引 (如果不存在)
        if await self.corpus_db.count() == len(corpus):
            logger.info("语料向量索引已存在，跳过")
        else:
            texts = [e.content for e in corpus]
            vecs = await self.embed.embed_batch(texts)
            items = [(e.id, e.content, {"card_id": e.card_id, "type": e.type}, vecs[i])
                     for i, e in enumerate(corpus)]
            await self.corpus_db.insert_batch(items)

    async def reindex_corpus(self, corpus: list[CorpusEntry]):
        """设计模式下添加/编辑语料后，重建语料索引"""
        # 全量重建（语料规模小，重建成本低）
        await self.corpus_db.docs._clear()
        # ... same as bootstrap step 2
```

## 3. 依赖变更

### 3.1 requirements.txt

```diff
  fastapi>=0.110.0
  uvicorn[standard]>=0.29.0
  pydantic>=2.6.0
+ openai>=1.30.0
+ faiss-cpu>=1.8.0
+ numpy>=1.26.0
+ aiosqlite>=0.20.0
+ jieba>=0.42.1           # 中文分词（稀疏检索）
+ rank-bm25>=0.2.2        # FTS5 不可用时的降级方案
+ httpx>=0.27.0           # openai 依赖
```

### 3.2 配置文件（新增 `app/config.py`）

```python
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class EmbeddingConfig:
    api_base: str = "http://localhost:1234/v1"   # LM Studio 默认
    api_key: str = "lm-studio"
    model: str = "text-embedding-nomic-embed-text-v1.5"
    dimensions: int = 768
    timeout: int = 20
    batch_size: int = 16
    max_concurrent: int = 3
    max_retries: int = 3

@dataclass
class LLMConfig:
    api_base: str = "http://localhost:1234/v1"
    api_key: str = "lm-studio"
    model: str = "local-model"
    timeout: int = 60
    enabled: bool = True   # False → 始终走模板降级

@dataclass
class VecDBConfig:
    data_dir: Path = Path("data/index")
    # 自动推导: {data_dir}/cards/doc.db, {data_dir}/cards/index.faiss
    # 自动推导: {data_dir}/corpus/doc.db, {data_dir}/corpus/index.faiss

@dataclass
class AppConfig:
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    vec_db: VecDBConfig = field(default_factory=VecDBConfig)

# 可通过环境变量或 .env 文件覆盖:
#   CC_EMBED_API_BASE=http://localhost:11434/v1
#   CC_EMBED_MODEL=nomic-embed-text
#   CC_LLM_ENABLED=false
```

## 4. API 变更

### 4.1 新增端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/admin/reindex` | 重建向量索引（设计模式下添加语料后调用） |
| `GET`  | `/api/status` | 系统状态：embedding 可用性、索引条目数、LLM 连通性 |
| `POST` | `/api/corpus` | 添加语料条目（设计模式） |
| `DELETE` | `/api/corpus/{entry_id}` | 删除语料条目 |
| `PUT`  | `/api/cards/{card_id}` | 更新卡片内容 |

### 4.2 修改端点

| 端点 | 变更 |
|------|------|
| `POST /api/emergence` | 响应增加 `engine_mode` 字段: `"vector"` / `"keyword_fallback"` |
| `POST /api/emergence` | 响应增加 `guidance_mode` 字段: `"llm"` / `"template_fallback"` |

### 4.3 降级行为

```
                     embedding 可用?
                    /              \
                  是                否
                  │                 │
           vector 语义匹配     Jaccard 关键词匹配
           BM25 稀疏检索      Jaccard 关键词匹配
                  │                 │
                RRF 融合        简单加权排序
                  │                 │
              LLM 可用?          LLM 可用?
             /        \         /        \
           是          否      是          否
           │           │       │           │
       LLM 引导词  模板引导词 LLM 引导词 模板引导词
```

## 5. 实施步骤

### Phase 1：基础设施（2-3天）

1. **目录重组**：拆 `server.py` → `app/` 子模块，保持当前功能不变
2. **新增配置**：`app/config.py`，支持环境变量覆盖
3. **新增依赖**：`faiss-cpu`, `numpy`, `aiosqlite`, `jieba`, `rank-bm25`, `openai`, `httpx`
4. **实现 `app/vec_db/`**：`base.py` → `doc_storage.py` → `embed_storage.py` → `faiss_store.py`
5. **实现 `app/provider/openai_embed.py`**：`EmbeddingService`，连接本地 LM 验证连通性
6. **实现 `app/engine/merger.py`**：`RankFusion` RRF 混合排序
7. **单元测试**：向量存储读写、FTS5 检索、RRF 融合正确性

### Phase 2：索引与检索（1-2天）

8. **实现 `IndexBootstrap`**：启动时批量嵌入卡片+语料，建立 FAISS 索引
9. **重写 `matcher.py`**：向量语义匹配替换 Jaccard
10. **重写 `refiner.py`**：混合检索替换纯关键词加权
11. **集成降级逻辑**：embedding 不可用时自动回退关键词匹配
12. **测试**：本地 LM Studio / Ollama 环境端到端验证

### Phase 3：LLM 集成（1天）

13. **实现 LLM 客户端**：`app/provider/llm_client.py`，OpenAI 兼容接口
14. **重写 `emergence.py`**：LLM 驱动 + 模板降级双路径
15. **提示词工程**：基于设计文档 §7.2 的匹配器和涌现器提示词精调
16. **测试**：LLM 可用/不可用两种场景的端到端验证

### Phase 4：打磨与文档（1天）

17. **新增 API 端点**：`/api/admin/reindex`, `/api/status`, 语料 CRUD
18. **前端适配**：展示 `engine_mode` 和 `guidance_mode` 状态
19. **文档**：更新 README，补全 API 文档，添加启动指南

## 6. 直接可复用的 AstrBot 模式

以下模式可直接借鉴，无需重新设计：

| 模式 | AstrBot 来源 | 本项目对应 |
|------|-------------|-----------|
| `IndexFlatL2` + `IndexIDMap` | `embedding_storage.py:32` | `app/vec_db/embed_storage.py` |
| `normalize_L2` → cosine | `embedding_storage.py:58` | 同上 |
| L2 distance → score: `1.0 - d/2.0` | `vec_db.py:213` | `app/vec_db/faiss_store.py` |
| async `Semaphore` batch | `provider.py:135` | `app/services/embedding.py` |
| Exponential backoff retry | `provider.py:167` | 同上 |
| RRF `k=60` | `rank_fusion.py:13` | `app/engine/merger.py` |
| FTS5 `bm25()` + `MATCH OR` | `document_storage.py:404` | `app/vec_db/doc_storage.py` |
| `json_extract(metadata, '$.field')` | `document_storage.py:146` | 同上 |
| jieba + stopwords tokenizer | `tokenizer.py:18` | `app/engine/matcher.py` |

## 7. 风险与注意事项

1. **Windows FAISS 安装**：`faiss-cpu` 在 Windows 上可能需要 `pip install faiss-cpu` 而非 `faiss`。如遇到 DLL 问题，备选方案是用 `chromadb`（纯 Python，自管理索引）
2. **嵌入模型选择**：建议使用 `bge-large-zh-v1.5`（1024维，中文最佳）或 `bge-m3`（多语言）。`nomic-embed-text-v1.5` 也支持中文但质量稍低
3. **启动时间**：首次启动需批量嵌入 10 卡片 + ~14 语料，约 2-5 秒（本地 LM）。后续启动直接加载 FAISS 索引，秒级
4. **语料继承**：子卡片语料索引时需 `metadata` 中记录 `{card_id, parent_card_ids}`，检索时 `WHERE json_extract(metadata, '$.card_id') IN (...)`
5. **索引不可变与更新**：添加新语料后需调用 `/api/admin/reindex`。语料规模小（<1000条），全量重建成本低
