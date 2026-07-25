"""
DataStore：内存数据 + YAML 落盘持久化。

- 首次启动：data.yaml 不存在时从 seed.yaml 复制（与前端内置数据完全一致）
- 每次写操作后立即保存，重启不丢失
- 卡片 / 节点以 dict 存储，字段与前端 TS 类型（src/data/types.ts）一一对应
"""

from __future__ import annotations

import shutil
import threading
from pathlib import Path
from typing import Any

import yaml

BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BACKEND_DIR / "data.yaml"
SEED_FILE = BACKEND_DIR / "seed.yaml"


class DataStore:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.cards: list[dict[str, Any]] = []
        self.nodes: list[dict[str, Any]] = []
        self.load()

    # ---------- 持久化 ----------

    def load(self) -> None:
        with self._lock:
            if not DATA_FILE.exists():
                if not SEED_FILE.exists():
                    raise FileNotFoundError(f"种子数据缺失: {SEED_FILE}")
                shutil.copyfile(SEED_FILE, DATA_FILE)
            with open(DATA_FILE, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            self.cards = data.get("cognitive_cards") or []
            self.nodes = data.get("navigation_nodes") or []

    def save(self) -> None:
        with self._lock:
            payload = {
                "cognitive_cards": self.cards,
                "navigation_nodes": self.nodes,
            }
            with open(DATA_FILE, "w", encoding="utf-8") as f:
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


store = DataStore()
