"""
领域逻辑：与前端 src/utils 中的算法保持一致。

- priorityToWeight / weightToPriority：quickConnectUtils.ts
- composeWeights：weightUtils.ts（override > preset > browse，同 target 取最小序号）
- derive_parent：treeUtils.ts 层级路径规则（root/1/2 的父级是 root/1）
- graph_edges：由 next_nodes 推导的有向边
"""

from __future__ import annotations

from typing import Any


# ---------- 优先级序号 ↔ 权重 ----------

def priority_to_weight(priority: int) -> float:
    """UI 优先级 #N → preset_weight。#1→1.0 … #10→0.1，#11+ → 0.05"""
    if priority <= 0:
        priority = 1
    if priority >= 11:
        return 0.05
    return round(1.0 - (priority - 1) * 0.1, 2)


def weight_to_priority(weight: float) -> int:
    if weight <= 0.05:
        return 11
    return max(1, round((1.0 - weight) / 0.1) + 1)


# ---------- 树形路径 ----------

def derive_parent(card_id: str) -> str:
    """root/1/2 → root/1；root/1 → root；root → 异常（由调用方避免）"""
    parts = card_id.split("/")
    if len(parts) <= 1:
        raise ValueError(f"非法卡片 id: {card_id}")
    return "/".join(parts[:-1])


def children_of(cards: list[dict[str, Any]], parent_id: str) -> list[dict[str, Any]]:
    out = []
    for c in cards:
        cid = c.get("id", "")
        if cid == parent_id:
            continue
        try:
            if derive_parent(cid) == parent_id:
                out.append(c)
        except ValueError:
            continue
    return out


# ---------- 权重合成 ----------

def compose_weights(node: dict[str, Any]) -> list[dict[str, Any]]:
    """weightUtils.composeWeights 的 Python 实现。"""
    cfg = node.get("priority_config") or {}
    mode = cfg.get("mode", "mixed")
    preset_priority = cfg.get("preset_priority", 0)
    next_nodes = node.get("next_nodes") or []
    browse_priority = cfg.get("browse_priority", len(next_nodes))
    overrides = cfg.get("user_overrides") or []

    result: list[dict[str, Any]] = []
    overridden: set[str] = set()

    for i, o in enumerate(overrides):
        ref = next((n for n in next_nodes if n.get("target_id") == o.get("target_id")), None)
        if ref is None:
            continue
        overridden.add(o["target_id"])
        result.append({**ref, "seq": i, "weight": o.get("override_weight", 0), "source": "override"})

    rest = [n for n in next_nodes if n.get("target_id") not in overridden]

    by_preset = sorted(rest, key=lambda r: r.get("preset_weight", 0), reverse=True)
    for i, ref in enumerate(by_preset):
        result.append({**ref, "seq": preset_priority + i, "weight": ref.get("preset_weight", 0), "source": "preset"})

    if mode == "mixed":
        by_browse = sorted(rest, key=lambda r: r.get("browse_weight", 0), reverse=True)
        for i, ref in enumerate(by_browse):
            result.append({**ref, "seq": browse_priority + i, "weight": ref.get("browse_weight", 0), "source": "browse"})

    best: dict[str, dict[str, Any]] = {}
    for r in result:
        cur = best.get(r["target_id"])
        if cur is None or r["seq"] < cur["seq"]:
            best[r["target_id"]] = r

    return sorted(best.values(), key=lambda r: r["seq"])


def connection_weight(from_node: dict[str, Any], to_id: str, mode: str = "mixed") -> float:
    """routePlanner.getConnectionWeight：mixed 取预设与浏览均值，user_only 仅预设。"""
    ref = next((n for n in (from_node.get("next_nodes") or []) if n.get("target_id") == to_id), None)
    if ref is None:
        return 0.0
    if mode == "user_only":
        return float(ref.get("preset_weight", 0))
    return (float(ref.get("preset_weight", 0)) + float(ref.get("browse_weight", 0))) / 2


# ---------- 导航图 ----------

def graph_edges(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    for n in nodes:
        for ref in n.get("next_nodes") or []:
            w = connection_weight(n, ref.get("target_id", ""), (n.get("priority_config") or {}).get("mode", "mixed"))
            edges.append({"source": n.get("id"), "target": ref.get("target_id"), "weight": round(w, 4)})
    return edges


# ---------- 级联清理 ----------

def cascade_delete_card(cards: list[dict[str, Any]], nodes: list[dict[str, Any]], card_id: str) -> None:
    """删除卡片后清理所有节点 bound_cards 中的引用（原地修改）。"""
    for n in nodes:
        if n.get("bound_cards") and card_id in n["bound_cards"]:
            n["bound_cards"] = [c for c in n["bound_cards"] if c != card_id]


def cascade_delete_node(cards: list[dict[str, Any]], nodes: list[dict[str, Any]], node_id: str) -> None:
    """删除节点后清理出向引用与卡片 bound_nodes（原地修改）。"""
    for n in nodes:
        if n.get("next_nodes"):
            n["next_nodes"] = [r for r in n["next_nodes"] if r.get("target_id") != node_id]
        if n.get("browse_history"):
            n["browse_history"] = [h for h in n["browse_history"] if h.get("from") != node_id]
    for c in cards:
        if c.get("bound_nodes") and node_id in c["bound_nodes"]:
            c["bound_nodes"] = [x for x in c["bound_nodes"] if x != node_id]
