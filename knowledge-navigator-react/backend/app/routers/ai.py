"""AI 辅助生成（/api/ai/generate/*）：LM Studio 代理 + 本地模板降级。"""

from __future__ import annotations

import json
import urllib.request
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..store import store

router = APIRouter(prefix="/api/ai", tags=["ai"])

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
LM_TIMEOUT = 8


class GenerateBody(BaseModel):
    id: str


PROMPTS = {
    "card-title": "为以下认知卡片生成一个简洁的中文标题（不超过15字），只输出标题本身：\n{context}",
    "card-desc": "为以下认知卡片生成一句中文描述（不超过50字），只输出描述本身：\n{context}",
    "node-label": "为以下导航节点生成一个简洁的中文名称（不超过10字），只输出名称本身：\n{context}",
    "node-desc": "为以下导航节点生成一句中文描述（不超过50字），只输出描述本身：\n{context}",
}


def _card_context(card: dict[str, Any]) -> str:
    parts = [f"标题: {card.get('title', '')}", f"描述: {card.get('description', '')}"]
    corpus = card.get("corpus") or []
    if corpus:
        parts.append("语料: " + "；".join(corpus[:5]))
    children = [c for c in store.cards if c.get("id", "").startswith(card.get("id", "") + "/")]
    if children:
        parts.append("子卡片: " + "、".join(c.get("title", "") for c in children[:5]))
    return "\n".join(parts)


def _node_context(node: dict[str, Any]) -> str:
    parts = [f"名称: {node.get('label', '')}", f"描述: {node.get('description', '')}"]
    bound = [store.get_card(cid) for cid in (node.get("bound_cards") or [])]
    bound = [c for c in bound if c]
    if bound:
        parts.append("绑定卡片: " + "、".join(c.get("title", "") for c in bound[:5]))
    return "\n".join(parts)


def _lm_generate(prompt: str) -> str | None:
    """调用本机 LM Studio（OpenAI 兼容接口）；不可用返回 None。"""
    payload = json.dumps({
        "model": "local-model",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 120,
    }).encode("utf-8")
    req = urllib.request.Request(LM_STUDIO_URL, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=LM_TIMEOUT) as res:
            data = json.loads(res.read().decode("utf-8"))
        text = data["choices"][0]["message"]["content"].strip()
        # 去掉引号 / 多余换行
        return text.strip('"\'').splitlines()[0].strip() or None
    except Exception:
        return None


def _fallback(endpoint: str, entity: dict[str, Any]) -> str:
    """本地模板降级生成。"""
    if endpoint == "card-title":
        corpus = entity.get("corpus") or []
        return (corpus[0][:12] + "…") if corpus else str(entity.get("title", "未命名卡片"))
    if endpoint == "card-desc":
        corpus = entity.get("corpus") or []
        return corpus[0][:50] if corpus else f"关于「{entity.get('title', '')}」的认知卡片。"
    if endpoint == "node-label":
        return str(entity.get("label", "未命名节点"))
    return str(entity.get("description") or f"导航节点 {entity.get('label', '')}。")


@router.post("/generate/{endpoint}")
def generate(endpoint: str, body: GenerateBody) -> dict[str, str]:
    if endpoint not in PROMPTS:
        raise HTTPException(status_code=404, detail=f"未知生成类型: {endpoint}")

    is_card = endpoint.startswith("card-")
    entity = store.get_card(body.id) if is_card else store.get_node(body.id)
    if entity is None:
        raise HTTPException(status_code=404, detail=f"{'卡片' if is_card else '节点'} {body.id} 不存在")

    context = _card_context(entity) if is_card else _node_context(entity)
    result = _lm_generate(PROMPTS[endpoint].format(context=context))
    if result is None:
        result = _fallback(endpoint, entity)
    return {"result": result}
