"""快捷连接（/api/connections）：状态查询、确保连接、批量补全。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..domain import priority_to_weight
from ..store import store

router = APIRouter(prefix="/api/connections", tags=["connections"])


class EnsureBody(BaseModel):
    from_id: str
    to_id: str


class FillAllBody(BaseModel):
    waypoint_ids: list[str]


def _find_ref(from_id: str, to_id: str) -> dict | None:
    node = store.get_node(from_id)
    if node is None:
        return None
    return next((r for r in (node.get("next_nodes") or []) if r.get("target_id") == to_id), None)


def _ensure(from_id: str, to_id: str) -> bool:
    """quickConnectUtils.ensureQuickConnection：缺失则以 user_added/#1 建立连接。"""
    from_node = store.get_node(from_id)
    if from_node is None or store.get_node(to_id) is None:
        return False
    if from_id == to_id:
        return False
    refs = from_node.setdefault("next_nodes", [])
    if any(r.get("target_id") == to_id for r in refs):
        return False
    refs.append({
        "target_id": to_id,
        "preset_weight": priority_to_weight(1),
        "browse_weight": 0,
        "connection_type": "user_added",
    })
    return True


@router.get("/status/{from_id}/{to_id}")
def connection_status(from_id: str, to_id: str) -> dict:
    if store.get_node(from_id) is None or store.get_node(to_id) is None:
        return {"status": "unavailable"}
    ref = _find_ref(from_id, to_id)
    if ref is None:
        return {"status": "missing"}
    return {"status": "connected", "ref": ref}


@router.post("/ensure")
def ensure_connection(body: EnsureBody) -> dict:
    created = _ensure(body.from_id, body.to_id)
    if created:
        store.save()
    return {"ok": True, "created": created}


@router.post("/fill-all")
def fill_all(body: FillAllBody) -> dict:
    """fillAllMissingConnections：为相邻途经点对补全缺失连接，返回新建条数。"""
    count = 0
    for i in range(len(body.waypoint_ids) - 1):
        if _ensure(body.waypoint_ids[i], body.waypoint_ids[i + 1]):
            count += 1
    if count:
        store.save()
    return {"count": count}


@router.put("/{from_id}/{to_id}")
def update_connection(from_id: str, to_id: str, updates: dict) -> dict:
    ref = _find_ref(from_id, to_id)
    if ref is None:
        raise HTTPException(status_code=404, detail=f"连接 {from_id} → {to_id} 不存在")
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


@router.delete("/{from_id}/{to_id}")
def remove_connection(from_id: str, to_id: str) -> dict:
    node = store.get_node(from_id)
    if node is None:
        raise HTTPException(status_code=404, detail=f"节点 {from_id} 不存在")
    refs = node.get("next_nodes") or []
    kept = [r for r in refs if r.get("target_id") != to_id]
    if len(kept) == len(refs):
        raise HTTPException(status_code=404, detail=f"连接 {from_id} → {to_id} 不存在")
    node["next_nodes"] = kept
    store.save()
    return {"ok": True}
