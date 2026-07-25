"""FastAPI 应用入口：CORS、路由挂载、健康检查。"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .store import store
from .routers import ai, browse, cards, connections, graph, nodes, plan, search, view, yaml_io

app = FastAPI(title="Knowledge Navigator Backend", version="0.1.0")

# 本地开发：放开全部来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "knowledge-navigator-backend",
        "version": "0.1.0",
        "cards": len(store.cards),
        "nodes": len(store.nodes),
    }


for r in (cards, nodes, graph, plan, browse, search, yaml_io, ai, connections, view):
    app.include_router(r.router)
