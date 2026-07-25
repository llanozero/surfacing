"""认知卡片 CRUD（/api/cards）。卡片 id 含斜杠（root/1/2），一律使用 {card_id:path}。

注意：children / corpus 等子路由必须声明在通用 /{card_id:path} 之前，
否则 path 转换器会把子路径吞进 card_id。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..domain import cascade_delete_card, children_of, derive_parent
from ..store import store

router = APIRouter(prefix="/api/cards", tags=["cards"])


class CreateCardBody(BaseModel):
    parent_id: str | None = None


class CorpusBody(BaseModel):
    text: str


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _require_card(card_id: str) -> dict[str, Any]:
    card = store.get_card(card_id)
    if card is None:
        raise HTTPException(status_code=404, detail=f"卡片 {card_id} 不存在")
    return card


@router.get("")
def list_cards() -> list[dict[str, Any]]:
    return store.cards


@router.post("", status_code=201)
def create_card(body: CreateCardBody) -> dict[str, Any]:
    parent = body.parent_id or "root"
    if parent != "root" and store.get_card(parent) is None:
        raise HTTPException(status_code=404, detail=f"父卡片 {parent} 不存在")
    # 同级最大序号 + 1（与前端 cardStore.createCard 一致）
    max_idx = 0
    for c in store.cards:
        cid = c.get("id", "")
        try:
            if derive_parent(cid) != parent:
                continue
        except ValueError:
            continue
        seg = cid.split("/")[-1]
        if seg.isdigit():
            max_idx = max(max_idx, int(seg))
    card = {
        "id": f"{parent}/{max_idx + 1}",
        "title": "新建卡片",
        "type": "leaf",
        "corpus": [],
        "bound_nodes": [],
        "metadata": {"created_at": _now()},
    }
    store.cards.append(card)
    store.save()
    return card


# ---------- 子路由（必须先于通用 /{card_id:path} 声明） ----------

@router.get("/{card_id:path}/children")
def get_children(card_id: str) -> list[dict[str, Any]]:
    _require_card(card_id)
    return children_of(store.cards, card_id)


@router.get("/{card_id:path}/corpus")
def get_corpus(card_id: str) -> list[str]:
    return _require_card(card_id).get("corpus") or []


@router.post("/{card_id:path}/corpus", status_code=201)
def add_corpus(card_id: str, body: CorpusBody) -> dict[str, Any]:
    card = _require_card(card_id)
    card.setdefault("corpus", []).append(body.text)
    store.save()
    return {"ok": True, "corpus": card["corpus"]}


@router.put("/{card_id:path}/corpus/{index}")
def update_corpus(card_id: str, index: int, body: CorpusBody) -> dict[str, Any]:
    card = _require_card(card_id)
    corpus = card.setdefault("corpus", [])
    if index < 0 or index >= len(corpus):
        raise HTTPException(status_code=404, detail=f"语料[{index}] 不存在")
    corpus[index] = body.text
    store.save()
    return {"ok": True, "corpus": corpus}


@router.delete("/{card_id:path}/corpus/{index}")
def remove_corpus(card_id: str, index: int) -> dict[str, Any]:
    card = _require_card(card_id)
    corpus = card.setdefault("corpus", [])
    if index < 0 or index >= len(corpus):
        raise HTTPException(status_code=404, detail=f"语料[{index}] 不存在")
    corpus.pop(index)
    store.save()
    return {"ok": True, "corpus": corpus}


# ---------- 通用单卡片路由（最后声明） ----------

@router.get("/{card_id:path}")
def get_card(card_id: str) -> dict[str, Any]:
    return _require_card(card_id)


@router.put("/{card_id:path}")
def update_card(card_id: str, fields: dict[str, Any]) -> dict[str, Any]:
    card = _require_card(card_id)
    protected = {"id"}
    for k, v in fields.items():
        if k not in protected:
            card[k] = v
    card.setdefault("metadata", {})["updated_at"] = _now()
    store.save()
    return card


@router.delete("/{card_id:path}")
def delete_card(card_id: str) -> dict[str, Any]:
    _require_card(card_id)
    # 文件夹须为空才可删除（与前端 deleteCard 一致）
    if children_of(store.cards, card_id):
        raise HTTPException(status_code=409, detail="文件夹含子卡片，无法删除")
    store.delete_card(card_id)
    cascade_delete_card(store.cards, store.nodes, card_id)
    store.save()
    return {"ok": True}
