"""浏览（/api/browse）：会话态保存在服务端内存。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..domain import connection_weight
from ..store import store
from .plan import plan_state

router = APIRouter(prefix="/api/browse", tags=["browse"])


class StartBody(BaseModel):
    plan_id: str | None = None
    sequence: list[str] | None = None


class BrowseState:
    def __init__(self) -> None:
        self.node_ids: list[str] = []
        self.waypoint_index = 0
        self.card_index = 0


browse_state = BrowseState()


def _cards_for_waypoint(waypoint: dict[str, Any]) -> list[dict[str, Any]]:
    """browseStore.cardsForWaypoint 的 Python 实现。"""
    related_prev = [
        store.get_node(h["from"]).get("label")
        for h in (waypoint.get("browse_history") or [])
        if h.get("from") and store.get_node(h["from"])
    ]
    related_next = [
        store.get_node(e["target_id"]).get("label")
        for e in (waypoint.get("next_nodes") or [])
        if store.get_node(e.get("target_id", ""))
    ]
    weight = sum(
        connection_weight(waypoint, e.get("target_id", ""), (waypoint.get("priority_config") or {}).get("mode", "mixed"))
        for e in (waypoint.get("next_nodes") or [])
    )
    cards = []
    for cid in waypoint.get("bound_cards") or []:
        c = store.get_card(cid)
        if c is None:
            continue
        corpus = c.get("corpus") or []
        cards.append({
            "title": c.get("title", ""),
            "desc": c.get("description") or (corpus[0] if corpus else ""),
            "tag": c.get("tag") or "",
            "weight": round(weight, 4),
            "cards": len(corpus),
            "corpus": corpus,
            "related": [
                *[{"name": n, "pos": "前置"} for n in related_prev[:1]],
                *[{"name": n, "pos": "后置"} for n in related_next[:2]],
            ],
        })
    return cards


def _current_waypoint() -> dict[str, Any]:
    if not browse_state.node_ids:
        raise HTTPException(status_code=400, detail="尚未开始浏览，请先 POST /api/browse/start")
    nid = browse_state.node_ids[browse_state.waypoint_index]
    node = store.get_node(nid)
    if node is None:
        raise HTTPException(status_code=404, detail=f"节点 {nid} 不存在")
    return node


@router.post("/start")
def start_browse(body: StartBody) -> dict[str, Any]:
    if body.plan_id:
        plan = next((p for p in plan_state.plans if p["id"] == body.plan_id), None)
        if plan is None:
            raise HTTPException(status_code=404, detail=f"计划 {body.plan_id} 不存在")
        browse_state.node_ids = [n["id"] for n in plan["sequence"]]
    elif body.sequence:
        missing = [i for i in body.sequence if store.get_node(i) is None]
        if missing:
            raise HTTPException(status_code=404, detail=f"节点不存在: {', '.join(missing)}")
        browse_state.node_ids = list(body.sequence)
    else:
        raise HTTPException(status_code=400, detail="需要 plan_id 或 sequence")
    browse_state.waypoint_index = 0
    browse_state.card_index = 0
    return {"ok": True, "waypoints": len(browse_state.node_ids)}


@router.get("/status")
def get_status() -> dict[str, int]:
    total_waypoints = len(browse_state.node_ids)
    total_cards = 0
    if total_waypoints:
        total_cards = len(_cards_for_waypoint(_current_waypoint()))
    return {
        "waypointIndex": browse_state.waypoint_index,
        "totalWaypoints": total_waypoints,
        "cardIndex": browse_state.card_index,
        "totalCards": total_cards,
    }


@router.get("/cards")
def get_cards() -> list[dict[str, Any]]:
    if not browse_state.node_ids:
        return []
    return _cards_for_waypoint(_current_waypoint())


@router.post("/next")
def next_card() -> dict[str, Any]:
    total = len(_cards_for_waypoint(_current_waypoint()))
    if total == 0:
        raise HTTPException(status_code=400, detail="当前站点无浏览卡片")
    browse_state.card_index = (browse_state.card_index + 1) % total
    return {"ok": True, "cardIndex": browse_state.card_index}


@router.post("/prev")
def prev_card() -> dict[str, Any]:
    total = len(_cards_for_waypoint(_current_waypoint()))
    if total == 0:
        raise HTTPException(status_code=400, detail="当前站点无浏览卡片")
    browse_state.card_index = (browse_state.card_index - 1) % total
    return {"ok": True, "cardIndex": browse_state.card_index}


@router.post("/waypoint")
def next_waypoint() -> dict[str, Any]:
    if not browse_state.node_ids:
        raise HTTPException(status_code=400, detail="尚未开始浏览")
    browse_state.waypoint_index = (browse_state.waypoint_index + 1) % len(browse_state.node_ids)
    browse_state.card_index = 0
    return {"ok": True, "waypointIndex": browse_state.waypoint_index}


# ── 自由分支浏览 ──


class FreeStartBody(BaseModel):
    node_id: str


def _branch_node_items(node_id: str, direction: str) -> list[dict[str, Any]]:
    """获取节点的前驱/后继分支节点列表。
    
    direction: 'prev' | 'next'
    """
    items: list[dict[str, Any]] = []
    all_nodes = store.nodes

    if direction == "prev":
        for n in all_nodes:
            for e in n.get("next_nodes") or []:
                if e.get("target_id") == node_id:
                    node = store.get_node(n["id"])
                    if node:
                        items.append({
                            "node_id": n["id"],
                            "label": node.get("label", n["id"]),
                            "weight": e.get("preset_weight", 0.5),
                        })
    else:
        node = store.get_node(node_id)
        if node:
            for e in node.get("next_nodes") or []:
                target = store.get_node(e.get("target_id", ""))
                if target:
                    items.append({
                        "node_id": e["target_id"],
                        "label": target.get("label", e["target_id"]),
                        "weight": e.get("preset_weight", 0.5),
                    })

    items.sort(key=lambda x: x["weight"], reverse=True)
    return items


def _free_browse_response(node_id: str) -> dict[str, Any]:
    """构造自由分支浏览的完整响应。"""
    node = store.get_node(node_id)
    if node is None:
        raise HTTPException(status_code=404, detail=f"节点 {node_id} 不存在")
    return {
        "ok": True,
        "current_node_id": node_id,
        "current_node_label": node.get("label", node_id),
        "cards": _cards_for_waypoint(node),
        "prev_nodes": _branch_node_items(node_id, "prev"),
        "next_nodes": _branch_node_items(node_id, "next"),
    }


@router.post("/free/start")
def free_start(body: FreeStartBody) -> dict[str, Any]:
    """以指定节点开始自由分支浏览。"""
    return _free_browse_response(body.node_id)


@router.post("/free/jump/{target_id}")
def free_jump(target_id: str) -> dict[str, Any]:
    """跳转到目标节点，返回新节点的上下文。"""
    return _free_browse_response(target_id)
