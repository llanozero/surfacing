"""路线规划（/api/plan）：routePlanner.ts 的 Python 镜像实现。

- 无序模式：全排列（n ≤ 7）+ 贪心 + 衔接优先 DFS 补充
- 有序模式：子路径拼接（断点插入最优中间节点）
- 计划列表保存在服务端内存（会话态），不写入 YAML
"""

from __future__ import annotations

from itertools import permutations
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..domain import connection_weight
from ..store import store

router = APIRouter(prefix="/api/plan", tags=["plan"])

PLAN_LABELS = ["Plan A", "Plan B", "Plan C", "Plan D", "Plan E", "Plan F"]
PERMUTATION_LIMIT = 7


class GenerateBody(BaseModel):
    waypoint_ids: list[str] | None = None
    waypoint_mode: str = "unordered"
    weight_mode: str = "mixed"


# ---------- 规划器状态（会话态，服务端内存） ----------

class PlanState:
    def __init__(self) -> None:
        self.plans: list[dict[str, Any]] = []
        self.selected_plan_id: str | None = None
        self.source_waypoint_ids: list[str] = []
        self.waypoint_mode: str = "unordered"
        self.weight_mode: str = "mixed"


plan_state = PlanState()


# ---------- 算法（与 routePlanner.ts 一致） ----------

def _seq_weight(seq: list[dict], mode: str) -> float:
    return sum(
        connection_weight(seq[i], seq[i + 1]["id"], mode)
        for i in range(len(seq) - 1)
    )


def _greedy_forward(waypoints: list[dict], mode: str) -> list[dict]:
    remaining = list(waypoints)
    seq = [remaining.pop(0)]
    current = seq[0]
    while remaining:
        best_idx, best_w = -1, 0.0
        for i, w in enumerate(remaining):
            weight = connection_weight(current, w["id"], mode)
            if weight > best_w:
                best_w, best_idx = weight, i
        nxt = remaining.pop(best_idx) if best_idx >= 0 else remaining.pop(0)
        seq.append(nxt)
        current = nxt
    return seq


def _permutation_optimal(waypoints: list[dict], mode: str, top_k: int) -> list[list[dict]]:
    scored = sorted(
        (list(p) for p in permutations(waypoints)),
        key=lambda s: _seq_weight(s, mode),
        reverse=True,
    )
    out, seen = [], set()
    for seq in scored:
        key = ">".join(n["id"] for n in seq)
        if key in seen:
            continue
        seen.add(key)
        out.append(seq)
        if len(out) >= top_k:
            break
    return out


def _connection_priority(waypoints: list[dict], mode: str, top_k: int) -> list[list[dict]]:
    results: list[tuple[list[dict], float]] = []
    if len(waypoints) <= PERMUTATION_LIMIT:
        def dfs(current: dict, visited: list[dict], weight: float) -> None:
            if len(visited) == len(waypoints):
                results.append((list(visited), weight))
                return
            for nxt in waypoints:
                if nxt in visited:
                    continue
                dfs(nxt, visited + [nxt], weight + connection_weight(current, nxt["id"], mode))
        for start in waypoints:
            dfs(start, [start], 0.0)
    else:
        for start in waypoints:
            rest = [w for w in waypoints if w is not start]
            seq = _greedy_forward([start, *rest], mode)
            results.append((seq, _seq_weight(seq, mode)))
    results.sort(key=lambda r: r[1], reverse=True)
    out, seen = [], set()
    for seq, _ in results:
        key = ">".join(n["id"] for n in seq)
        if key in seen:
            continue
        seen.add(key)
        out.append(seq)
        if len(out) >= top_k:
            break
    return out


def _best_intermediate(from_node: dict, to_node: dict, mode: str, exclude: set[str]) -> dict | None:
    best, best_w = None, 0.0
    for ref in from_node.get("next_nodes") or []:
        tid = ref.get("target_id", "")
        if tid in exclude:
            continue
        mid = store.get_node(tid)
        if mid is None:
            continue
        w1 = ref.get("preset_weight", 0) if mode == "user_only" else (ref.get("preset_weight", 0) + ref.get("browse_weight", 0)) / 2
        w2 = connection_weight(mid, to_node["id"], mode)
        if w1 > 0 and w2 > 0 and w1 + w2 > best_w:
            best_w, best = w1 + w2, mid
    return best


def _subpath_stitching(waypoints: list[dict], mode: str) -> list[list[dict]]:
    stitched = [waypoints[0]]
    for i in range(len(waypoints) - 1):
        from_n, to_n = waypoints[i], waypoints[i + 1]
        if connection_weight(from_n, to_n["id"], mode) == 0:
            exclude = {w["id"] for w in waypoints}
            mid = _best_intermediate(from_n, to_n, mode, exclude)
            if mid is not None and mid not in stitched:
                stitched.append(mid)
        stitched.append(to_n)
    results = [stitched]
    if [n["id"] for n in stitched] != [n["id"] for n in waypoints]:
        results.append(list(waypoints))
    return results


def generate_plans(waypoints: list[dict], weight_mode: str, waypoint_mode: str) -> list[dict[str, Any]]:
    candidates: list[tuple[list[dict], str]] = []
    if waypoint_mode == "ordered":
        candidates = [(seq, "subpath") for seq in _subpath_stitching(waypoints, weight_mode)]
    else:
        if len(waypoints) <= PERMUTATION_LIMIT:
            candidates = [(seq, "permutation") for seq in _permutation_optimal(waypoints, weight_mode, 2)]
            candidates.append((_greedy_forward(waypoints, weight_mode), "greedy"))
            if len(candidates) < 3:
                candidates += [(seq, "connection") for seq in _connection_priority(waypoints, weight_mode, 3)]
        else:
            candidates = [(_greedy_forward(waypoints, weight_mode), "greedy")]
            candidates += [(seq, "connection") for seq in _connection_priority(waypoints, weight_mode, 2)]

    seen, unique = set(), []
    for seq, algo in candidates:
        key = ">".join(n["id"] for n in seq)
        if key in seen:
            continue
        seen.add(key)
        unique.append((seq, algo))

    any_connection = any(_seq_weight(seq, weight_mode) > 0 for seq, _ in unique)
    final = unique if any_connection else [(list(waypoints), "subpath")]

    scored = sorted(final, key=lambda c: _seq_weight(c[0], weight_mode), reverse=True)
    return [
        {
            "id": f"plan-{i}",
            "label": PLAN_LABELS[i] if i < len(PLAN_LABELS) else f"Plan {i + 1}",
            "sequence": seq,
            "totalWeight": round(_seq_weight(seq, weight_mode), 4),
            "algorithm": algo,
            "isRecommended": i == 0,
        }
        for i, (seq, algo) in enumerate(scored)
    ]


# ---------- 路由 ----------

@router.post("/generate")
def post_generate(body: GenerateBody) -> list[dict[str, Any]]:
    if body.waypoint_ids:
        missing = [i for i in body.waypoint_ids if store.get_node(i) is None]
        if missing:
            raise HTTPException(status_code=404, detail=f"节点不存在: {', '.join(missing)}")
        nodes = [store.get_node(i) for i in body.waypoint_ids]
    else:
        # 未指定：默认取全部有出向连接的前两个节点之外的入口集合 → 使用前 3 个有连接的节点
        connected = [n for n in store.nodes if n.get("next_nodes")]
        nodes = connected[:3]
    if len(nodes) < 2:
        raise HTTPException(status_code=400, detail="途经点至少需要 2 个")

    plan_state.source_waypoint_ids = [n["id"] for n in nodes]
    plan_state.waypoint_mode = body.waypoint_mode
    plan_state.weight_mode = body.weight_mode
    plan_state.plans = generate_plans(nodes, body.weight_mode, body.waypoint_mode)
    plan_state.selected_plan_id = plan_state.plans[0]["id"] if plan_state.plans else None
    return plan_state.plans


@router.get("/plans")
def list_plans() -> list[dict[str, Any]]:
    return plan_state.plans


@router.get("/plans/{plan_id}")
def get_plan(plan_id: str) -> dict[str, Any]:
    plan = next((p for p in plan_state.plans if p["id"] == plan_id), None)
    if plan is None:
        raise HTTPException(status_code=404, detail=f"计划 {plan_id} 不存在")
    return plan


@router.post("/plans/{plan_id}/select")
def select_plan(plan_id: str) -> dict[str, Any]:
    if not any(p["id"] == plan_id for p in plan_state.plans):
        raise HTTPException(status_code=404, detail=f"计划 {plan_id} 不存在")
    plan_state.selected_plan_id = plan_id
    return {"ok": True, "selected": plan_id}


@router.post("/replan")
def replan() -> list[dict[str, Any]]:
    if not plan_state.source_waypoint_ids:
        raise HTTPException(status_code=400, detail="尚无规划上下文，请先 plan generate")
    nodes = [store.get_node(i) for i in plan_state.source_waypoint_ids]
    nodes = [n for n in nodes if n is not None]
    plan_state.plans = generate_plans(nodes, plan_state.weight_mode, plan_state.waypoint_mode)
    return plan_state.plans
