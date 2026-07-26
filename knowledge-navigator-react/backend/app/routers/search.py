"""搜索（/api/search）：关键词加权评分 + LM Studio 嵌入向量语义匹配。

- /query：关键词加权子串评分（本地计算，无外部依赖）
- /vector-match：优先调用本机 LM Studio /v1/embeddings（qwen3-embedding）
  做余弦相似度语义匹配；模型不可用 / 超时自动降级为关键词评分
"""

from __future__ import annotations

import json
import math
import urllib.request
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from ..store import store

router = APIRouter(prefix="/api/search", tags=["search"])

LM_EMBED_URL = "http://localhost:1234/v1/embeddings"
# 候选嵌入模型：按序尝试，全部不可用则降级关键词评分
LM_EMBED_MODELS = [
    "text-embedding-qwen3-embedding-0.6b",
    "text-embedding-nomic-embed-text-v1.5",
]
LM_TIMEOUT = 10
# 余弦相似度阈值：低于此值视为语义无关，过滤噪声
SIMILARITY_FLOOR = 0.15
# 语义匹配返回条数上限（嵌入分数分布密集，取头部保证可读性）
VECTOR_TOP_K = 8


class QueryBody(BaseModel):
    query: str
    mode: str | None = None


def _keyword_score(card: dict[str, Any], query: str) -> float:
    """加权子串评分：标题命中权重最高，其次标签 / 描述 / 语料。"""
    q = query.lower()
    if not q:
        return 0.0
    score = 0.0
    title = str(card.get("title", "")).lower()
    tag = str(card.get("tag", "")).lower()
    desc = str(card.get("description", "")).lower()
    corpus = " ".join(card.get("corpus") or []).lower()

    if q in title:
        score += 0.6 if title == q else 0.5
    if q in tag:
        score += 0.2
    if q in desc:
        score += 0.15
    if q in corpus:
        score += 0.1
    # 多词查询：按词拆分补充部分分
    terms = [t for t in q.split() if t]
    if len(terms) > 1:
        hits = sum(1 for t in terms if t in title or t in desc or t in corpus)
        score += 0.1 * (hits / len(terms))
    return min(round(score, 4), 1.0)


def _match(query: str) -> list[dict[str, Any]]:
    results = []
    for card in store.cards:
        score = _keyword_score(card, query)
        if score > 0:
            results.append({"card": card, "score": score})
    results.sort(key=lambda r: r["score"], reverse=True)
    return results


@router.post("/query")
def search_query(body: QueryBody) -> list[dict[str, Any]]:
    return _match(body.query)


# ---------- 向量语义匹配（LM Studio 嵌入） ----------


def _card_text(card: dict[str, Any]) -> str:
    return "\n".join(
        [str(card.get("title", "")), str(card.get("description", "")), *(card.get("corpus") or [])]
    )


def _embed(texts: list[str]) -> list[list[float]] | None:
    """批量调用 LM Studio /v1/embeddings（按候选模型依次尝试）；不可用返回 None。"""
    for model in LM_EMBED_MODELS:
        payload = json.dumps({"model": model, "input": texts}).encode("utf-8")
        req = urllib.request.Request(LM_EMBED_URL, data=payload, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=LM_TIMEOUT) as res:
                data = json.loads(res.read().decode("utf-8"))
            # OpenAI 兼容：按 index 归位，保证与输入顺序一致
            items = sorted(data["data"], key=lambda x: x["index"])
            return [item["embedding"] for item in items]
        except Exception:
            continue
    return None


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _vector(query: str) -> list[dict[str, Any]] | None:
    """语义匹配：query 与全部卡片批量嵌入后按余弦相似度排序。"""
    cards = list(store.cards)
    if not cards:
        return []
    vecs = _embed([query, *[_card_text(c) for c in cards]])
    if vecs is None or len(vecs) != len(cards) + 1:
        return None
    qv, card_vecs = vecs[0], vecs[1:]
    results = []
    for card, cv in zip(cards, card_vecs):
        score = _cosine(qv, cv)
        if score >= SIMILARITY_FLOOR:
            results.append({"card": card, "score": round(score, 4)})
    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:VECTOR_TOP_K]


@router.post("/vector-match")
def vector_match(body: QueryBody) -> list[dict[str, Any]]:
    # 嵌入模型不可用 / 超时 → 降级为关键词评分
    results = _vector(body.query)
    return results if results is not None else _match(body.query)
