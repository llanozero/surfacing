"""导航图管理路由（/api/graphs）：多图 CRUD + 跨图解析。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..store import store, Graph

router = APIRouter(prefix="/api/graphs", tags=["graphs"])


# ── 请求体 ──

class CreateGraphBody(BaseModel):
    label: str
    description: str = ""


class ResolveBatchBody(BaseModel):
    refs: list[str]


class DrillPathBody(BaseModel):
    graph_ids: list[str]


# ── 清单 ──

@router.get("")
def list_graphs() -> dict[str, Any]:
    """返回所有图的清单。"""
    return {"graphs": store.graph_list()}


# ── 跨图资源解析（须在 /{graph_id} 之前定义） ──

@router.get("/resolve")
def resolve_graph_ref(ref: str) -> dict[str, Any]:
    """解析跨图引用（如 g2::node-prob），返回目标资源完整数据。"""
    if "::" not in ref:
        raise HTTPException(status_code=400, detail="引用格式错误，需要 graph_id::resource_id")
    graph_id, resource_id = ref.split("::", 1)
    g = store.get_graph(graph_id)
    if not g:
        raise HTTPException(status_code=404, detail=f"目标图 {graph_id} 不存在")

    # 先查节点，再查卡片
    node = g.get_node(resource_id)
    if node:
        return {"type": "node", "data": node, "graph_id": graph_id, "graph_label": g.label}

    card = g.get_card(resource_id)
    if card:
        return {"type": "card", "data": card, "graph_id": graph_id, "graph_label": g.label}

    raise HTTPException(status_code=404, detail=f"资源 {resource_id} 在图 {graph_id} 中不存在")


@router.post("/resolve-batch")
def resolve_batch(body: ResolveBatchBody) -> dict[str, Any]:
    """批量解析跨图引用。"""
    results: list[dict[str, Any]] = []
    for ref in body.refs:
        if "::" not in ref:
            results.append({"ref": ref, "error": "格式错误"})
            continue
        graph_id, resource_id = ref.split("::", 1)
        g = store.get_graph(graph_id)
        if not g:
            results.append({"ref": ref, "error": f"图 {graph_id} 不存在"})
            continue

        node = g.get_node(resource_id)
        if node:
            results.append({"ref": ref, "type": "node", "data": node, "graph_id": graph_id, "graph_label": g.label})
            continue

        card = g.get_card(resource_id)
        if card:
            results.append({"ref": ref, "type": "card", "data": card, "graph_id": graph_id, "graph_label": g.label})
            continue

        results.append({"ref": ref, "error": f"资源 {resource_id} 不存在"})

    return {"results": results}


@router.post("/resolve-drill-path")
def resolve_drill_path(body: DrillPathBody) -> dict[str, Any]:
    """解析钻入路径：返回每个图的 label 信息（用于构建面包屑导航）。"""
    steps: list[dict[str, Any]] = []
    for gid in body.graph_ids:
        g = store.get_graph(gid)
        if g:
            steps.append({"graph_id": gid, "graph_label": g.label, "description": g.description})
        else:
            steps.append({"graph_id": gid, "graph_label": gid, "description": ""})
    return {"steps": steps}


# ── 单图操作 ──

@router.get("/{graph_id}")
def get_graph(graph_id: str) -> dict[str, Any]:
    """获取指定图的完整数据（节点 + 卡片）。"""
    g = store.get_graph(graph_id)
    if not g:
        raise HTTPException(status_code=404, detail=f"图 {graph_id} 不存在")
    return g.to_dict()


@router.get("/{graph_id}/nodes")
def get_graph_nodes(graph_id: str) -> dict[str, Any]:
    """获取指定图的全部节点。"""
    g = store.get_graph(graph_id)
    if not g:
        raise HTTPException(status_code=404, detail=f"图 {graph_id} 不存在")
    return {"nodes": g.nodes}


@router.get("/{graph_id}/cards")
def get_graph_cards(graph_id: str) -> dict[str, Any]:
    """获取指定图的全部卡片。"""
    g = store.get_graph(graph_id)
    if not g:
        raise HTTPException(status_code=404, detail=f"图 {graph_id} 不存在")
    return {"cards": g.cards}


@router.get("/{graph_id}/nodes/{node_id}")
def get_graph_node(graph_id: str, node_id: str) -> dict[str, Any]:
    """获取指定图的单个节点。"""
    g = store.get_graph(graph_id)
    if not g:
        raise HTTPException(status_code=404, detail=f"图 {graph_id} 不存在")
    node = g.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"节点 {node_id} 不存在")
    return node


@router.get("/{graph_id}/edges")
def get_graph_edges(graph_id: str) -> dict[str, Any]:
    """获取指定图的全部边（从 next_nodes 派生）。"""
    g = store.get_graph(graph_id)
    if not g:
        raise HTTPException(status_code=404, detail=f"图 {graph_id} 不存在")
    edges: list[dict[str, Any]] = []
    for node in g.nodes:
        for ref in node.get("next_nodes", []):
            edges.append({
                "source": node["id"],
                "target": ref.get("target_id", ""),
                "weight": ref.get("preset_weight", 1.0),
            })
    return {"edges": edges}


@router.get("/{graph_id}/subgraph-nodes")
def get_subgraph_nodes(graph_id: str) -> dict[str, Any]:
    """返回该图中所有子图节点（sub_graph_id 不为空的节点）。"""
    g = store.get_graph(graph_id)
    if not g:
        raise HTTPException(status_code=404, detail=f"图 {graph_id} 不存在")
    sub = [n for n in g.nodes if n.get("sub_graph_id")]
    return {"nodes": sub}


# ── 图管理 ──

@router.post("")
def create_graph(body: CreateGraphBody) -> dict[str, Any]:
    """新建一个空白图。"""
    gid = store.create_graph(body.label, body.description)
    return {"graph_id": gid, "label": body.label}


@router.delete("/{graph_id}")
def delete_graph(graph_id: str) -> dict[str, Any]:
    """删除指定图（物理删除 YAML 文件，更新 manifest）。"""
    ok = store.delete_graph(graph_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"图 {graph_id} 不存在")
    return {"ok": True}
