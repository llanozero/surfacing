"""导航图（/api/graph）：节点、边、重算。"""

from fastapi import APIRouter

from ..domain import graph_edges
from ..store import store

router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.get("/nodes")
def get_graph_nodes() -> list[dict]:
    return store.nodes


@router.get("/edges")
def get_graph_edges() -> list[dict]:
    return graph_edges(store.nodes)


@router.post("/sync")
def sync_graph() -> dict:
    """远程模式下图数据由节点实时推导，无需重算；重新加载落盘数据即可。"""
    store.load()
    return {"ok": True, "nodes": len(store.nodes), "edges": len(graph_edges(store.nodes))}
