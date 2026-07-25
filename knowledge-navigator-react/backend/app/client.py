"""Knowledge Navigator 后端 Python API 客户端。

覆盖全部十组端点（backend-architecture.md §4.2），供 CLI 与第三方脚本复用：

    from app.client import BackendClient
    client = BackendClient()                      # 默认 http://localhost:8171
    client.health()                               # {'status': 'ok', ...}
    client.list_cards()                           # 认知卡片列表

错误处理：非 2xx 响应抛出 BackendError（含 status 与后端 detail）。
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

import requests

DEFAULT_BASE_URL = "http://localhost:8171"


class BackendError(RuntimeError):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(f"HTTP {status}: {message}")
        self.status = status
        self.message = message


def _enc(value: str) -> str:
    """路径参数编码：卡片 id 含斜杠（root/1/2），需 %2F 编码。"""
    return quote(value, safe="")


class BackendClient:
    def __init__(self, base_url: str = DEFAULT_BASE_URL, timeout: float = 15.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    # ---------- 底层 ----------

    def _request(self, method: str, path: str, body: Any = None) -> Any:
        url = f"{self.base_url}{path}"
        try:
            res = requests.request(method, url, json=body, timeout=self.timeout)
        except requests.RequestException as e:
            raise BackendError(-1, f"无法连接后端 {self.base_url}: {e}") from e
        if res.status_code >= 400:
            try:
                detail = res.json().get("detail", res.text)
            except ValueError:
                detail = res.text
            raise BackendError(res.status_code, str(detail))
        if not res.content:
            return None
        return res.json()

    def _get(self, path: str) -> Any:
        return self._request("GET", path)

    def _post(self, path: str, body: Any = None) -> Any:
        return self._request("POST", path, body)

    def _put(self, path: str, body: Any = None) -> Any:
        return self._request("PUT", path, body)

    def _delete(self, path: str) -> Any:
        return self._request("DELETE", path)

    # ---------- 健康 ----------

    def health(self) -> dict:
        return self._get("/api/health")

    # ---------- 认知卡片 ----------

    def list_cards(self) -> list[dict]:
        return self._get("/api/cards")

    def create_card(self, parent_id: str | None = None) -> dict:
        return self._post("/api/cards", {"parent_id": parent_id})

    def get_card(self, card_id: str) -> dict:
        return self._get(f"/api/cards/{_enc(card_id)}")

    def update_card(self, card_id: str, **fields: Any) -> dict:
        return self._put(f"/api/cards/{_enc(card_id)}", fields)

    def delete_card(self, card_id: str) -> dict:
        return self._delete(f"/api/cards/{_enc(card_id)}")

    def get_card_children(self, card_id: str) -> list[dict]:
        return self._get(f"/api/cards/{_enc(card_id)}/children")

    def get_corpus(self, card_id: str) -> list[str]:
        return self._get(f"/api/cards/{_enc(card_id)}/corpus")

    def add_corpus(self, card_id: str, text: str) -> dict:
        return self._post(f"/api/cards/{_enc(card_id)}/corpus", {"text": text})

    def update_corpus(self, card_id: str, index: int, text: str) -> dict:
        return self._put(f"/api/cards/{_enc(card_id)}/corpus/{index}", {"text": text})

    def remove_corpus(self, card_id: str, index: int) -> dict:
        return self._delete(f"/api/cards/{_enc(card_id)}/corpus/{index}")

    # ---------- 导航节点 ----------

    def list_nodes(self, query: str | None = None) -> list[dict]:
        return self._get(f"/api/nodes?q={_enc(query)}" if query else "/api/nodes")

    def create_node(self) -> dict:
        return self._post("/api/nodes", {})

    def get_node(self, node_id: str) -> dict:
        return self._get(f"/api/nodes/{_enc(node_id)}")

    def update_node(self, node_id: str, **fields: Any) -> dict:
        return self._put(f"/api/nodes/{_enc(node_id)}", fields)

    def delete_node(self, node_id: str) -> dict:
        return self._delete(f"/api/nodes/{_enc(node_id)}")

    def bind_card(self, node_id: str, card_id: str) -> dict:
        return self._post(f"/api/nodes/{_enc(node_id)}/bind-card", {"card_id": card_id})

    def unbind_card(self, node_id: str, card_id: str) -> dict:
        return self._delete(f"/api/nodes/{_enc(node_id)}/bind-card/{_enc(card_id)}")

    def get_next_nodes(self, node_id: str) -> list[dict]:
        return self._get(f"/api/nodes/{_enc(node_id)}/next")

    def add_next_node(self, node_id: str, target_id: str,
                      preset_priority: int | None = None,
                      browse_priority: int | None = None,
                      connection_type: str | None = None) -> dict:
        return self._post(f"/api/nodes/{_enc(node_id)}/next", {
            "target_id": target_id,
            "preset_priority": preset_priority,
            "browse_priority": browse_priority,
            "connection_type": connection_type,
        })

    def update_next_node(self, node_id: str, target_id: str, **updates: Any) -> dict:
        return self._put(f"/api/nodes/{_enc(node_id)}/next/{_enc(target_id)}", updates)

    def remove_next_node(self, node_id: str, target_id: str) -> dict:
        return self._delete(f"/api/nodes/{_enc(node_id)}/next/{_enc(target_id)}")

    def get_prev_nodes(self, node_id: str) -> list[dict]:
        return self._get(f"/api/nodes/{_enc(node_id)}/prev")

    def get_browse_history(self, node_id: str) -> list[dict]:
        return self._get(f"/api/nodes/{_enc(node_id)}/browse-history")

    # ---------- 导航图 ----------

    def graph_nodes(self) -> list[dict]:
        return self._get("/api/graph/nodes")

    def graph_edges(self) -> list[dict]:
        return self._get("/api/graph/edges")

    def graph_sync(self) -> dict:
        return self._post("/api/graph/sync")

    # ---------- 路线规划 ----------

    def generate_plans(self, waypoint_ids: list[str] | None = None,
                       waypoint_mode: str = "unordered",
                       weight_mode: str = "mixed") -> list[dict]:
        return self._post("/api/plan/generate", {
            "waypoint_ids": waypoint_ids,
            "waypoint_mode": waypoint_mode,
            "weight_mode": weight_mode,
        })

    def list_plans(self) -> list[dict]:
        return self._get("/api/plan/plans")

    def get_plan(self, plan_id: str) -> dict:
        return self._get(f"/api/plan/plans/{_enc(plan_id)}")

    def select_plan(self, plan_id: str) -> dict:
        return self._post(f"/api/plan/plans/{_enc(plan_id)}/select")

    def replan(self) -> list[dict]:
        return self._post("/api/plan/replan")

    # ---------- 浏览 ----------

    def browse_start(self, plan_id: str | None = None, sequence: list[str] | None = None) -> dict:
        return self._post("/api/browse/start", {"plan_id": plan_id, "sequence": sequence})

    def browse_status(self) -> dict:
        return self._get("/api/browse/status")

    def browse_cards(self) -> list[dict]:
        return self._get("/api/browse/cards")

    def browse_next(self) -> dict:
        return self._post("/api/browse/next")

    def browse_prev(self) -> dict:
        return self._post("/api/browse/prev")

    def browse_next_waypoint(self) -> dict:
        return self._post("/api/browse/waypoint")

    # ---------- 搜索 ----------

    def search(self, query: str, mode: str | None = None) -> list[dict]:
        return self._post("/api/search/query", {"query": query, "mode": mode})

    def vector_match(self, query: str) -> list[dict]:
        return self._post("/api/search/vector-match", {"query": query})

    # ---------- YAML 导入导出 ----------

    def yaml_export(self) -> str:
        return self._get("/api/yaml/export")["yaml"]

    def yaml_validate(self, raw: str) -> dict:
        return self._post("/api/yaml/validate", {"raw": raw})

    def yaml_preview(self, raw: str) -> dict:
        return self._post("/api/yaml/preview", {"raw": raw})

    def yaml_import(self, raw: str) -> dict:
        return self._post("/api/yaml/import", {"raw": raw})

    # ---------- AI 辅助生成 ----------

    def ai_generate(self, kind: str, entity_id: str) -> str:
        """kind: card-title / card-desc / node-label / node-desc"""
        return self._post(f"/api/ai/generate/{kind}", {"id": entity_id})["result"]

    # ---------- 快捷连接 ----------

    def connection_status(self, from_id: str, to_id: str) -> dict:
        return self._get(f"/api/connections/status/{_enc(from_id)}/{_enc(to_id)}")

    def connection_ensure(self, from_id: str, to_id: str) -> dict:
        return self._post("/api/connections/ensure", {"from_id": from_id, "to_id": to_id})

    def connection_update(self, from_id: str, to_id: str, **updates: Any) -> dict:
        return self._put(f"/api/connections/{_enc(from_id)}/{_enc(to_id)}", updates)

    def connection_remove(self, from_id: str, to_id: str) -> dict:
        return self._delete(f"/api/connections/{_enc(from_id)}/{_enc(to_id)}")

    def connections_fill_all(self, waypoint_ids: list[str]) -> dict:
        return self._post("/api/connections/fill-all", {"waypoint_ids": waypoint_ids})

    # ---------- 视图 ----------

    def view_current(self) -> dict:
        return self._get("/api/view/current")

    def view_switch(self, view: str) -> dict:
        return self._post("/api/view/switch", {"view": view})
