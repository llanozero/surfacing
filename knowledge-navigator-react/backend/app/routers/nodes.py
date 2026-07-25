"""导航节点 CRUD 与出向连接管理（/api/nodes）。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..domain import cascade_delete_node, compose_weights, priority_to_weight
from ..store import store

router = APIRouter(prefix="/api/nodes", tags=["nodes"])


class BindCardBody(BaseModel):
    card_id: str


class NextRefBody(BaseModel):
    target_id: str
    preset_priority: int | None = None
    browse_priority: int | None = None
    connection_type: str | None = None


def _require_node(node_id: str) -> dict[str, Any]:
    node = store.get_node(node_id)
    if node is None:
        raise HTTPException(status_code=404, detail=f"节点 {node_id} 不存在")
    return node


def _next_items(node: dict[str, Any]) -> list[dict[str, Any]]:
    """NextNodeItem[]：{ node, ref }，ref 为合成权重后的 WeightedRef。"""
    items = []
    for ref in compose_weights(node):
        target = store.get_node(ref["target_id"])
        if target is not None:
            items.append({"node": target, "ref": ref})
    return items


@router.get("")
def list_nodes(q: str | None = None) -> list[dict[str, Any]]:
    if not q:
        return store.nodes
    query = q.lower()
    return [
        n for n in store.nodes
        if query in str(n.get("id", "")).lower()
        or query in str(n.get("label", "")).lower()
        or query in str(n.get("description", "")).lower()
    ]


@router.post("", status_code=201)
def create_node() -> dict[str, Any]:
    # id 自动生成：node-custom-N（递增且不与现有冲突）
    n = 1
    while store.get_node(f"node-custom-{n}") is not None:
        n += 1
    node = {
        "id": f"node-custom-{n}",
        "label": "新建节点",
        "description": "",
        "bound_cards": [],
        "next_nodes": [],
    }
    store.nodes.append(node)
    store.save()
    return node


@router.get("/{node_id}")
def get_node(node_id: str) -> dict[str, Any]:
    return _require_node(node_id)


@router.put("/{node_id}")
def update_node(node_id: str, fields: dict[str, Any]) -> dict[str, Any]:
    node = _require_node(node_id)
    for k, v in fields.items():
        if k != "id":
            node[k] = v
    store.save()
    return node


@router.delete("/{node_id}")
def delete_node(node_id: str) -> dict[str, Any]:
    _require_node(node_id)
    store.delete_node(node_id)
    cascade_delete_node(store.cards, store.nodes, node_id)
    store.save()
    return {"ok": True}


@router.post("/{node_id}/bind-card")
def bind_card(node_id: str, body: BindCardBody) -> dict[str, Any]:
    node = _require_node(node_id)
    if store.get_card(body.card_id) is None:
        raise HTTPException(status_code=404, detail=f"卡片 {body.card_id} 不存在")
    bound = node.setdefault("bound_cards", [])
    if body.card_id not in bound:
        bound.append(body.card_id)
    # 双向同步：卡片侧 bound_nodes
    card = store.get_card(body.card_id)
    card_bound = card.setdefault("bound_nodes", [])
    if node_id not in card_bound:
        card_bound.append(node_id)
    store.save()
    return {"ok": True, "bound_cards": bound}


@router.delete("/{node_id}/bind-card/{card_id:path}")
def unbind_card(node_id: str, card_id: str) -> dict[str, Any]:
    node = _require_node(node_id)
    node["bound_cards"] = [c for c in (node.get("bound_cards") or []) if c != card_id]
    card = store.get_card(card_id)
    if card is not None and card.get("bound_nodes"):
        card["bound_nodes"] = [x for x in card["bound_nodes"] if x != node_id]
    store.save()
    return {"ok": True, "bound_cards": node["bound_cards"]}


@router.get("/{node_id}/next")
def get_next(node_id: str) -> list[dict[str, Any]]:
    return _next_items(_require_node(node_id))


@router.post("/{node_id}/next", status_code=201)
def add_next(node_id: str, body: NextRefBody) -> dict[str, Any]:
    node = _require_node(node_id)
    if store.get_node(body.target_id) is None:
        raise HTTPException(status_code=404, detail=f"目标节点 {body.target_id} 不存在")
    if node_id == body.target_id:
        raise HTTPException(status_code=400, detail="不允许建立自环连接")
    refs = node.setdefault("next_nodes", [])
    if any(r.get("target_id") == body.target_id for r in refs):
        raise HTTPException(status_code=409, detail="连接已存在")
    refs.append({
        "target_id": body.target_id,
        "preset_weight": priority_to_weight(body.preset_priority or 1),
        "browse_weight": priority_to_weight(body.browse_priority) if body.browse_priority is not None else 0,
        "connection_type": body.connection_type or "user_added",
    })
    store.save()
    return {"ok": True, "next_nodes": refs}


@router.put("/{node_id}/next/{target_id}")
def update_next(node_id: str, target_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    node = _require_node(node_id)
    refs = node.get("next_nodes") or []
    ref = next((r for r in refs if r.get("target_id") == target_id), None)
    if ref is None:
        raise HTTPException(status_code=404, detail=f"连接 {node_id} → {target_id} 不存在")
    if updates.get("preset_priority") is not None:
        ref["preset_weight"] = priority_to_weight(int(updates["preset_priority"]))
    if updates.get("browse_priority") is not None:
        ref["browse_weight"] = priority_to_weight(int(updates["browse_priority"]))
    if updates.get("preset_weight") is not None:
        ref["preset_weight"] = float(updates["preset_weight"])
    if updates.get("browse_weight") is not None:
        ref["browse_weight"] = float(updates["browse_weight"])
    if updates.get("connection_type") is not None:
        ref["connection_type"] = updates["connection_type"]
    store.save()
    return {"ok": True, "ref": ref}


@router.delete("/{node_id}/next/{target_id}")
def remove_next(node_id: str, target_id: str) -> dict[str, Any]:
    node = _require_node(node_id)
    refs = node.get("next_nodes") or []
    kept = [r for r in refs if r.get("target_id") != target_id]
    if len(kept) == len(refs):
        raise HTTPException(status_code=404, detail=f"连接 {node_id} → {target_id} 不存在")
    node["next_nodes"] = kept
    store.save()
    return {"ok": True}


@router.get("/{node_id}/prev")
def get_prev(node_id: str) -> list[dict[str, Any]]:
    _require_node(node_id)
    items = []
    for n in store.nodes:
        for ref in compose_weights(n):
            if ref["target_id"] == node_id:
                items.append({"node": n, "ref": ref})
                break
    return items


@router.get("/{node_id}/browse-history")
def get_browse_history(node_id: str) -> list[dict[str, Any]]:
    return _require_node(node_id).get("browse_history") or []
