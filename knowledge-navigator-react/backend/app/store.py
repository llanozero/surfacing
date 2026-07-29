"""
DataStore：多图内存数据 + YAML 落盘持久化。

- 多图模式：backend/graphs/_manifest.yaml + g*.yaml
- 旧版兼容：data.yaml 存在时自动迁移到 graphs/
- 卡片 / 节点以 dict 存储，字段与前端 TS 类型（src/data/types.ts）一一对应
"""

from __future__ import annotations

import shutil
import threading
from pathlib import Path
from typing import Any

import yaml

BACKEND_DIR = Path(__file__).resolve().parent.parent
GRAPHS_DIR = BACKEND_DIR / "graphs"
MANIFEST_FILE = GRAPHS_DIR / "_manifest.yaml"
LEGACY_DATA_FILE = BACKEND_DIR / "data.yaml"
LEGACY_SEED_FILE = BACKEND_DIR / "seed.yaml"


class Graph:
    """单个导航图的内存表示。"""

    def __init__(self, graph_id: str, label: str = "", description: str = "") -> None:
        self.graph_id = graph_id
        self.label = label
        self.description = description
        self.cards: list[dict[str, Any]] = []
        self.nodes: list[dict[str, Any]] = []

    @classmethod
    def from_yaml(cls, filepath: Path) -> Graph:
        with open(filepath, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        g = cls(
            graph_id=data.get("graph_id", ""),
            label=data.get("graph_label", ""),
            description=data.get("graph_description", ""),
        )
        g.cards = data.get("cognitive_cards") or []
        g.nodes = data.get("navigation_nodes") or []
        return g

    def to_dict(self) -> dict[str, Any]:
        return {
            "graph_id": self.graph_id,
            "graph_label": self.label,
            "graph_description": self.description,
            "cognitive_cards": self.cards,
            "navigation_nodes": self.nodes,
        }

    def save(self, filepath: Path) -> None:
        payload = self.to_dict()
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            yaml.safe_dump(payload, f, allow_unicode=True, sort_keys=False)

    # ---------- 卡片 ----------

    def get_card(self, card_id: str) -> dict[str, Any] | None:
        for c in self.cards:
            if c.get("id") == card_id:
                return c
        return None

    def upsert_card(self, card: dict[str, Any]) -> None:
        for i, c in enumerate(self.cards):
            if c.get("id") == card.get("id"):
                self.cards[i] = card
                return
        self.cards.append(card)

    def delete_card(self, card_id: str) -> bool:
        before = len(self.cards)
        self.cards = [c for c in self.cards if c.get("id") != card_id]
        return len(self.cards) < before

    # ---------- 节点 ----------

    def get_node(self, node_id: str) -> dict[str, Any] | None:
        for n in self.nodes:
            if n.get("id") == node_id:
                return n
        return None

    def get_node_ref(self, node_id: str) -> dict[str, Any] | None:
        """获取节点的引用视图：提取描述性字段，丢弃 next_nodes。"""
        n = self.get_node(node_id)
        if not n:
            return None
        return {
            "id": n.get("id", ""),
            "label": n.get("label", ""),
            "description": n.get("description", ""),
            "bound_cards": n.get("bound_cards", []),
        }

    def upsert_node(self, node: dict[str, Any]) -> None:
        for i, n in enumerate(self.nodes):
            if n.get("id") == node.get("id"):
                self.nodes[i] = node
                return
        self.nodes.append(node)

    def delete_node(self, node_id: str) -> bool:
        before = len(self.nodes)
        self.nodes = [n for n in self.nodes if n.get("id") != node_id]
        return len(self.nodes) < before


class DataStore:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.manifest: dict[str, Any] = {}
        self.graphs: dict[str, Graph] = {}  # graph_id → Graph
        self.load_all()

    # ---------- 加载 ----------

    def load_all(self) -> None:
        with self._lock:
            # 兼容旧版：data.yaml 存在但 graphs/_manifest.yaml 不存在 → 自动迁移
            if not MANIFEST_FILE.exists() and LEGACY_DATA_FILE.exists():
                self._migrate_legacy()

            if MANIFEST_FILE.exists():
                self._load_multi_graph()
            else:
                # 完全没有数据：创建空白 graphs 目录
                GRAPHS_DIR.mkdir(parents=True, exist_ok=True)
                self.manifest = {"graphs": [], "next_graph_number": 1}
                self._save_manifest()

    def _load_multi_graph(self) -> None:
        with open(MANIFEST_FILE, encoding="utf-8") as f:
            self.manifest = yaml.safe_load(f) or {"graphs": [], "next_graph_number": 1}
        self.graphs.clear()
        for g in self.manifest.get("graphs", []):
            gid = g.get("graph_id", "")
            if not gid:
                continue
            filepath = GRAPHS_DIR / g.get("file", f"{gid}.yaml")
            if filepath.exists():
                self.graphs[gid] = Graph.from_yaml(filepath)

    def _migrate_legacy(self) -> None:
        """将 data.yaml 迁移为 g1-ml.yaml + _manifest.yaml"""
        GRAPHS_DIR.mkdir(parents=True, exist_ok=True)
        with open(LEGACY_DATA_FILE, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        g1 = Graph(graph_id="g1", label="机器学习", description="从 data.yaml 自动迁移")
        g1.cards = data.get("cognitive_cards") or []
        g1.nodes = data.get("navigation_nodes") or []
        g1.save(GRAPHS_DIR / "g1-ml.yaml")
        self.graphs["g1"] = g1

        self.manifest = {
            "graphs": [{
                "graph_id": "g1",
                "file": "g1-ml.yaml",
                "label": "机器学习",
                "description": "从 data.yaml 自动迁移",
                "created_at": "2026-07-20T00:00:00Z",
                "node_count": len(g1.nodes),
                "card_count": len(g1.cards),
            }],
            "next_graph_number": 2,
        }
        self._save_manifest()

    def _save_manifest(self) -> None:
        GRAPHS_DIR.mkdir(parents=True, exist_ok=True)
        with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
            yaml.safe_dump(self.manifest, f, allow_unicode=True, sort_keys=False)

    # ---------- 图管理 ----------

    def create_graph(self, label: str, description: str = "") -> str:
        """新建空白图，返回 graph_id"""
        with self._lock:
            num = self.manifest.get("next_graph_number", 1)
            gid = f"g{num}"
            filepath = GRAPHS_DIR / f"{gid}.yaml"
            g = Graph(graph_id=gid, label=label, description=description)
            g.save(filepath)
            self.graphs[gid] = g
            self.manifest.setdefault("graphs", []).append({
                "graph_id": gid,
                "file": f"{gid}.yaml",
                "label": label,
                "description": description,
                "node_count": 0,
                "card_count": 0,
            })
            self.manifest["next_graph_number"] = num + 1
            self._save_manifest()
            return gid

    def delete_graph(self, graph_id: str) -> bool:
        with self._lock:
            g = self.graphs.pop(graph_id, None)
            if not g:
                return False
            # 删除 YAML 文件
            filepath = GRAPHS_DIR / f"{graph_id}.yaml"
            if filepath.exists():
                filepath.unlink()
            # 更新 manifest
            self.manifest["graphs"] = [
                entry for entry in self.manifest.get("graphs", [])
                if entry.get("graph_id") != graph_id
            ]
            self._save_manifest()
            return True

    def get_graph(self, graph_id: str) -> Graph | None:
        return self.graphs.get(graph_id)

    def save_graph(self, graph_id: str) -> bool:
        """将内存中的图数据写回 YAML 文件并更新 manifest 计数"""
        g = self.graphs.get(graph_id)
        if not g:
            return False
        filepath = GRAPHS_DIR / f"{graph_id}.yaml"
        g.save(filepath)
        # 更新 manifest 计数
        for entry in self.manifest.get("graphs", []):
            if entry.get("graph_id") == graph_id:
                entry["node_count"] = len(g.nodes)
                entry["card_count"] = len(g.cards)
                break
        self._save_manifest()
        return True

    def save_all(self) -> int:
        """将所有内存中的图数据写回 YAML 文件，返回保存的图数量。"""
        with self._lock:
            count = 0
            for gid, g in self.graphs.items():
                filepath = GRAPHS_DIR / f"{gid}.yaml"
                g.save(filepath)
                count += 1
            # 同步更新 manifest 计数
            for entry in self.manifest.get("graphs", []):
                gid = entry.get("graph_id", "")
                g = self.graphs.get(gid)
                if g:
                    entry["node_count"] = len(g.nodes)
                    entry["card_count"] = len(g.cards)
            self._save_manifest()
            return count

    # ---------- 聚合查询 ----------

    def all_nodes(self, graph_id: str | None = None) -> list[dict[str, Any]]:
        if graph_id:
            g = self.graphs.get(graph_id)
            return list(g.nodes) if g else []
        result: list[dict[str, Any]] = []
        for g in self.graphs.values():
            result.extend(g.nodes)
        return result

    def all_cards(self, graph_id: str | None = None) -> list[dict[str, Any]]:
        if graph_id:
            g = self.graphs.get(graph_id)
            return list(g.cards) if g else []
        result: list[dict[str, Any]] = []
        for g in self.graphs.values():
            result.extend(g.cards)
        return result

    def get_aggregated_canvas_data(self, selected_graph_ids: list[str]) -> dict[str, Any]:
        """根据勾选的图列表，聚合返回画布所需的节点和边数据。
        
        处理三种节点类型：
        - 普通节点：直接返回
        - 引用节点（ref_graph_id + ref_node_id）：从目标图提取描述字段
        - 子图节点（sub_graph_id + entry_node_id）：保持原样
        """
        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []
        graph_labels: dict[str, str] = {}

        for gid in selected_graph_ids:
            g = self.graphs.get(gid)
            if not g:
                continue
            graph_labels[gid] = g.label

            for node in g.nodes:
                node_id = node.get("id", "")
                
                # 判断节点类型
                ref_graph_id = node.get("ref_graph_id")
                ref_node_id = node.get("ref_node_id")
                
                if ref_graph_id and ref_node_id:
                    # 引用节点：从目标图提取描述字段
                    target_g = self.graphs.get(ref_graph_id)
                    if target_g:
                        ref_data = target_g.get_node_ref(ref_node_id)
                        if ref_data:
                            # 合并：本图 ID + 目标图描述 + 本图连线
                            resolved = {
                                **node,
                                "id": node_id,
                                "label": ref_data["label"],
                                "description": ref_data["description"],
                                "bound_cards": ref_data["bound_cards"],
                                "next_nodes": node.get("next_nodes", []),
                                "_nodeType": "ref",
                                "_sourceGraphId": ref_graph_id,
                                "_sourceGraphLabel": target_g.label,
                                "_sourceNodeId": ref_node_id,
                            }
                            nodes.append(resolved)
                        else:
                            # 降级：保留本节点但标记缺失
                            resolved = {
                                **node,
                                "_nodeType": "ref",
                                "_sourceGraphId": ref_graph_id,
                                "_sourceNodeId": ref_node_id,
                                "_missing": True,
                            }
                            nodes.append(resolved)
                    else:
                        resolved = {
                            **node,
                            "_nodeType": "ref",
                            "_sourceGraphId": ref_graph_id,
                            "_sourceNodeId": ref_node_id,
                            "_missing": True,
                        }
                        nodes.append(resolved)
                else:
                    # 普通节点或子图节点
                    sub_gid = node.get("sub_graph_id")
                    entry_nid = node.get("entry_node_id")
                    if sub_gid and entry_nid:
                        resolved = {
                            **node,
                            "_nodeType": "subgraph",
                            "_sourceGraphId": gid,
                            "_sourceGraphLabel": g.label,
                        }
                    else:
                        resolved = {
                            **node,
                            "_nodeType": "normal",
                            "_sourceGraphId": gid,
                            "_sourceGraphLabel": g.label,
                        }
                    nodes.append(resolved)

                # 收集边（所有节点类型的连线都从本图的 next_nodes 派生）
                for ref in node.get("next_nodes", []):
                    target_id = ref.get("target_id", "")
                    edges.append({
                        "source": node_id,
                        "target": target_id,
                        "weight": ref.get("preset_weight", 1.0),
                    })

        return {
            "nodes": nodes,
            "edges": edges,
            "graph_labels": graph_labels,
            "node_count": len(nodes),
            "edge_count": len(edges),
        }

    def graph_list(self) -> list[dict[str, Any]]:
        return list(self.manifest.get("graphs", []))

    # ---------- 全局兼容（供旧路由使用） ----------

    @property
    def cards(self) -> list[dict[str, Any]]:
        """兼容旧属性：返回所有图的卡片。读可直接用，写请用 graph-specific API。"""
        return self.all_cards()

    @property
    def nodes(self) -> list[dict[str, Any]]:
        """兼容旧属性：返回所有图的节点。"""
        return self.all_nodes()


store = DataStore()
