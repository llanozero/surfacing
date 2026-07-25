"""搜索（/api/search）：关键词加权评分；向量模式当前复用关键词结果（降级）。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from ..store import store

router = APIRouter(prefix="/api/search", tags=["search"])


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
    # mode=vector 时降级为关键词匹配（LM Studio 嵌入接入前）
    return _match(body.query)


@router.post("/vector-match")
def vector_match(body: QueryBody) -> list[dict[str, Any]]:
    return _match(body.query)
