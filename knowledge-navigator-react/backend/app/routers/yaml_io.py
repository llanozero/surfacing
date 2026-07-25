"""YAML 导入导出（/api/yaml）：导出 / 校验 / 预览 / 合并导入（upsert，不删除现有数据）。"""

from __future__ import annotations

from typing import Any

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..store import store

router = APIRouter(prefix="/api/yaml", tags=["yaml"])


class RawBody(BaseModel):
    raw: str


def _parse(raw: str) -> dict[str, Any]:
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        raise HTTPException(status_code=422, detail=f"YAML 解析失败: {e}")
    if not isinstance(data, dict):
        raise HTTPException(status_code=422, detail="YAML 顶层必须是对象（cognitive_cards / navigation_nodes）")
    cards = data.get("cognitive_cards") or []
    nodes = data.get("navigation_nodes") or []
    if not isinstance(cards, list) or not isinstance(nodes, list):
        raise HTTPException(status_code=422, detail="cognitive_cards / navigation_nodes 必须是数组")
    for c in cards:
        if not isinstance(c, dict) or not c.get("id") or not c.get("title"):
            raise HTTPException(status_code=422, detail=f"卡片缺少必填字段（id/title）: {c}")
    for n in nodes:
        if not isinstance(n, dict) or not n.get("id") or not n.get("label"):
            raise HTTPException(status_code=422, detail=f"节点缺少必填字段（id/label）: {n}")
    return {"cognitive_cards": cards, "navigation_nodes": nodes}


def _preview(data: dict[str, Any]) -> dict[str, Any]:
    existing_cards = {c.get("id") for c in store.cards}
    existing_nodes = {n.get("id") for n in store.nodes}
    cards = data["cognitive_cards"]
    nodes = data["navigation_nodes"]
    return {
        "cards": {
            "total": len(cards),
            "added": sum(1 for c in cards if c.get("id") not in existing_cards),
            "overwritten": sum(1 for c in cards if c.get("id") in existing_cards),
        },
        "nodes": {
            "total": len(nodes),
            "added": sum(1 for n in nodes if n.get("id") not in existing_nodes),
            "overwritten": sum(1 for n in nodes if n.get("id") in existing_nodes),
        },
    }


@router.get("/export")
def export_yaml() -> dict[str, str]:
    payload = {
        "cognitive_cards": store.cards,
        "navigation_nodes": store.nodes,
    }
    return {"yaml": yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)}


@router.post("/validate")
def validate_yaml(body: RawBody) -> dict[str, Any]:
    return _parse(body.raw)


@router.post("/preview")
def preview_import(body: RawBody) -> dict[str, Any]:
    return _preview(_parse(body.raw))


@router.post("/import")
def import_yaml(body: RawBody) -> dict[str, Any]:
    data = _parse(body.raw)
    preview = _preview(data)
    for c in data["cognitive_cards"]:
        store.upsert_card(c)
    for n in data["navigation_nodes"]:
        store.upsert_node(n)
    store.save()
    return preview
