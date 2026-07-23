# 推荐系统技术参考：从 X 算法架构到语料管线落地

AI 语料管线的 L3（路线连接）和 L4（反馈权重调整）本质上是一个推荐系统——从海量语料中召回候选，打分排序，根据用户行为反馈持续调权。本文梳理 X（Twitter）开源推荐算法架构中可借鉴的设计，以及当前可快速集成的开源方案。

---

## 1. X 推荐算法架构 → 语料管线映射

X 开源的 `twitter/the-algorithm` 仓库揭示了其"为您推荐"时间线的三阶段管线：

```
X 推荐管线                        cognitive-cards 语料管线
════════════                    ════════════════════════════

┌──────────────────┐            ┌──────────────────┐
│ Candidate         │            │ L3 路线与分支     │
│ Generation        │  ──对应──▶ │ 从语料库召回      │
│ (召回)            │            │ 候选语料子集      │
└────────┬─────────┘            └────────┬─────────┘
         │                               │
         ▼                               ▼
┌──────────────────┐            ┌──────────────────┐
│ Ranking           │            │ L2 共鸣匹配       │
│ (排序)            │  ──对应──▶ │ + L4 权重调整     │
│ 预测交互概率×权重  │            │ 共鸣强度×行为权重  │
└────────┬─────────┘            └────────┬─────────┘
         │                               │
         ▼                               ▼
┌──────────────────┐            ┌──────────────────┐
│ Filtering         │            │ 涌现引擎 阶段三   │
│ (过滤/多样性)     │  ──对应──▶ │ 锦囊路径涌现      │
│ 去重, 作者分散    │            │ 去重, 风格变化    │
└──────────────────┘            └──────────────────┘
```

### 1.1 候选召回 → 语料召回

X 的召回分两路：
- **In-Network**（已关注用户）：从用户关系图谱中召回
- **Out-Network**（未关注用户）：从全局内容池中通过 Embedding 相似度召回

对应到 cognitive-cards：

| X 召回方式 | 语料管线对应 |
|-----------|-------------|
| In-Network | 已匹配卡片下的语料（`card_id` 过滤）— 精准但窄 |
| Out-Network | 跨卡片的风格/关键词/向量相似语料 — 宽但可能不精准 |
| 双塔模型（User Tower + Item Tower） | 用户状态向量 × 语料向量 → 余弦相似度 |

### 1.2 排序打分 → 共鸣强度 × 行为权重

X 的排序模型预测用户对每条推文产生各种行为（点赞、转发、评论、停留时长、展开详情）的**概率**，然后加权求和：

```
score = Σ (行为概率 × 行为权重)

其中行为权重由产品目标决定（如：停留时长 > 点赞 > 转发）
```

对应到 cognitive-cards 的 L2+L4 合并打分：

```
final_score = resonance_strength × 0.5       # L2: AI共鸣匹配得分
            + behavior_weight × 0.3          # L4: 该语料历史行为权重
            + style_match × 0.1              # 风格匹配
            + recency_factor × 0.1           # 时间衰减（避免反复推旧语料）

其中 behavior_weight 由 L4 的反馈信号持续更新
```

### 1.3 过滤与多样性 → 锦囊去重与风格轮换

X 的过滤机制：
- **去重**：已显示过的推文短时间内不再出现
- **同一作者限流**：连续展示同一作者不超过 N 条
- **多样性注入**：在排序结果中按比例插入不同话题

对应到 cognitive-cards：

```
过滤规则:
  - 同一条语料在 24h 内不向同一用户重复展示
  - 同一张卡片的语料连续展示不超过 2 条
  - 每轮推荐中注入 1 条不同卡片的语料（多样性）
  - 同一风格的锦囊引导词连续使用不超过 3 次（风格轮换）
```

---

## 2. 快速集成的开源推荐方案

### 2.1 Gorse（推荐微服务，最推荐）

Gorse 是一个独立的 Go 语言推荐服务，提供 RESTful API，自带 AutoML 自动训练。

```
┌──────────────┐   反馈日志    ┌──────────────┐   推荐结果    ┌──────────────┐
│  server.py   │ ──────────▶ │    Gorse     │ ──────────▶ │  server.py   │
│  cognitive-  │  用户行为    │  (独立服务)   │   Top-N      │  语料推荐     │
│  cards       │ ◀────────── │  :8088       │ ◀────────── │              │
└──────────────┘              └──────────────┘              └──────────────┘
```

**集成步骤：**

```bash
# 1. 启动 Gorse
docker run -p 8088:8088 zhenghaoz/gorse-in-one

# 2. 导入数据
# 用户 = 会话 ID
curl -X POST http://localhost:8088/api/user -d '{"user_id": "s_20260723_01"}'

# 物品 = 语料条目
curl -X POST http://localhost:8088/api/item -d '{
  "item_id": "corpus_05_001",
  "labels": ["card_05", "诗意象_温和", "启动", "信任"],
  "comment": "飞轮启动前最安静的时刻..."
}'

# 反馈 = 用户行为信号
curl -X POST http://localhost:8088/api/feedback -d '{
  "feedback_type": "like",
  "user_id": "s_20260723_01",
  "item_id": "corpus_05_001"
}'
# feedback_type: like(共鸣确认), read(展示), skip(跳过)

# 3. 获取推荐
curl http://localhost:8088/api/recommend/s_20260723_01?n=5
```

**优势**：零 ML 代码，Gorse 自动做协同过滤 + 矩阵分解 + 在线学习。适合 cognitive-cards 的 L4 权重调整需求。

---

### 2.2 pgvector（已有 PG 时零额外部署）

如果 cognitive-cards 后期接入 PostgreSQL，直接用 pgvector 做语料的向量相似检索：

```sql
-- 建表
CREATE TABLE corpus_embeddings (
    id TEXT PRIMARY KEY,
    card_id TEXT,
    embedding VECTOR(1536),  -- OpenAI text-embedding-3-small 维度
    content TEXT,
    style_tags TEXT[]
);

-- 相似语料召回（L3 路线连接）
SELECT id, content, 1 - (embedding <=> $user_state_embedding) AS similarity
FROM corpus_embeddings
ORDER BY embedding <=> $user_state_embedding
LIMIT 10;

-- 结合权重的排序（L4）
SELECT c.id, c.content,
       (1 - (c.embedding <=> $user_state_embedding)) * 0.5
       + COALESCE(w.weight, 0.5) * 0.3
       + (CASE WHEN c.style_tags && $user_style THEN 0.2 ELSE 0 END)
       AS final_score
FROM corpus_embeddings c
LEFT JOIN corpus_weights w ON c.id = w.corpus_id
ORDER BY final_score DESC
LIMIT 5;
```

**优势**：与现有数据层合二为一，不需要额外服务。

---

### 2.3 LightFM（Python 轻量级冷启动处理）

cognitive-cards 的语料和用户都是冷启动物体（新语料没反馈、新用户没历史），LightFM 专门解决这个：

```python
from lightfm import LightFM
from lightfm.data import Dataset

# 构建交互矩阵
dataset = Dataset()
dataset.fit(
    users=session_ids,           # 会话ID
    items=corpus_ids,            # 语料ID
    user_features=state_labels,  # 用户状态标签（如"设计者心态_入口受阻"）
    item_features=card_labels,   # 语料标签（如"card_05_诗意象_温和"）
)
interactions, weights = dataset.build_interactions(feedback_pairs)

# 训练（混合协同过滤 + 内容特征）
model = LightFM(loss='warp')  # WARP 适合隐式反馈
model.fit(interactions, user_features=user_features, item_features=item_features)

# 对新用户（无历史）也能推荐——靠 user_features 元数据
scores = model.predict(
    new_user_id,
    all_item_ids,
    user_features=new_user_state_features
)
top_items = all_item_ids[np.argsort(-scores)[:5]]
```

**优势**：天然支持冷启动，几行代码即可。

---

## 3. 选型建议

| 阶段 | 需求 | 推荐方案 | 原因 |
|------|------|----------|------|
| **原型期** | 快速验证 L2+L4 逻辑 | 内置逻辑（当前 server.py） | 无额外依赖，逻辑透明 |
| **语料 < 100 条** | 权重调整 | Python `dict` + 简单评分公式 | 数据量小，不需要专门引擎 |
| **语料 100-1000 条** | 语料召回 + 权重排序 | **pgvector** | 向量检索，单表 SQL 搞定 |
| **语料 > 1000 条 / 多用户** | 完整推荐管线 | **Gorse** 或 **LightFM** | 协同过滤生效，AutoML 省心 |
| **需要实时在线学习** | 用户行为即时影响下次推荐 | **Gorse** | 内置在线学习，无需手动重训 |

### 渐进式接入路径

```
当前（原型）                  近期（数据积累）              远期（规模化）
┌────────────┐   语料超过     ┌────────────┐   用户行为     ┌────────────┐
│ 内置评分逻辑 │  ───────▶   │  pgvector   │  数据够大     │   Gorse     │
│ (server.py) │   50条       │  向量检索    │  ───────▶   │  自动推荐    │
│ 关键词匹配   │              │  + 权重SQL   │  100条+      │  AutoML     │
└────────────┘              └────────────┘              └────────────┘
```

---

## 4. 语料推荐的 X 算法启发点

X 算法架构中可以直接借鉴到 cognitive-cards 的设计决策：

### 4.1 多路召回融合

X 用多路召回（社交图谱 + 兴趣 Embedding + 实时热点）并在最后融合。对应到语料管线：

```
召回路径 1: 已匹配卡片语料（card_id 过滤）       ─┐
召回路径 2: 向量相似语料（跨卡片 Embedding）     ─┤
召回路径 3: 同风格语料（style_tags 匹配）        ─┼──▶ 合并去重 ──▶ 排序
召回路径 4: 高权重语料（L4 feedback 加权）       ─┤
召回路径 5: 探索性语料（随机采样，防信息茧房）    ─┘
```

### 4.2 停留时长的信号价值

X 的排序模型发现**停留时长**是比点赞/转发更可靠的信号。对应到 cognitive-cards：

| 行为 | 信号强度 | 含义 |
|------|----------|------|
| 用户停留阅读 > 10s | ★★★★ | 语料引起了深度共鸣 |
| 用户 < 3s 就跳过 | 负信号 | 语料不匹配或风格不契 |
| 用户做了身体动作 | ★★★★★ | 最强信号——语料驱动了行为改变 |
| 用户返回重复阅读 | ★★★★ | 语料有持续价值 |

### 4.3 探索与利用平衡（Epsilon-Greedy）

X 的排序不是纯贪心（只推预测分数最高的），而是留一定比例给"探索"——推一些用户历史中没接触过但可能感兴趣的。对应到语料管线：

```python
def select_corpus(user_id, candidate_scores, epsilon=0.1):
    if random.random() < epsilon:
        # 探索：随机选一条非 Top 的语料
        return random.choice(candidate_scores[5:])
    else:
        # 利用：选最高分
        return candidate_scores[0]
```

这避免了用户永远只看到同一张卡片、同一种风格的语料。

---

## 5. 权重数据结构设计

```json
{
  "corpus_weights": {
    "corpus_05_001": {
      "global": 0.85,
      "by_cycle_position": {
        "designer_stuck": 0.92,
        "executor_lost": 0.45,
        "executor_flow": 0.30
      },
      "by_user_style": {
        "叙事_内省": 0.88,
        "简洁_直接": 0.60
      },
      "feedback_history": [
        {"session": "s_001", "signal": "resonance_confirm", "delta": 0.09, "at": "2026-07-23T10:30:00Z"},
        {"session": "s_005", "signal": "corpus_skip", "delta": -0.06, "at": "2026-07-23T11:00:00Z"}
      ],
      "last_updated": "2026-07-23T11:00:00Z"
    }
  },
  "route_weights": {
    "route_designer_stuck_v3": {
      "global": 0.72,
      "completion_rate": 0.65,
      "avg_session_duration_ms": 45000,
      "last_updated": "2026-07-23T10:00:00Z"
    }
  }
}
```

权重不是全局一个数，而是三维矩阵：**卡片 × 循环位置 × 用户风格**。同一条语料在"设计者入口受阻"场景下权重可能很高，在"执行者流畅"场景下权重可能很低。

---

*本文档为 AI 语料管线（L2-L4）的技术落地参考。实际集成按"原型内置 → pgvector → Gorse"渐进路线推进。*
