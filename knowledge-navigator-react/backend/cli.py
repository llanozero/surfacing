"""Knowledge Navigator 后端 CLI —— 覆盖后端全部功能组。

用法（需后端已启动：python backend/run.py）：

    python backend/cli.py health
    python backend/cli.py card list [--json]
    python backend/cli.py card get root/1/1
    python backend/cli.py card create --parent root/7 --title 新卡片
    python backend/cli.py card corpus-add root/7/1 "语料文本"
    python backend/cli.py node list --query 机器学习
    python backend/cli.py node next-add node-kit-a node-kit-c --priority 2
    python backend/cli.py plan generate --ids node-kit-a,node-kit-e,node-kit-g
    python backend/cli.py browse start --plan plan-0
    python backend/cli.py search query 机器学习 --mode keyword
    python backend/cli.py yaml export --file out.yaml
    python backend/cli.py yaml import imports/cognitive-cards-kits.yaml
    python backend/cli.py ai card-title root/7/1
    python backend/cli.py conn status node-kit-a node-kit-b
    python backend/cli.py conn fill-all node-kit-a,node-kit-e,node-kit-g
    python backend/cli.py view set plan

全局参数：--url 后端地址（默认 http://localhost:8171，或环境变量 KN_BACKEND_URL）
          --json 输出原始 JSON
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.client import BackendClient, BackendError  # noqa: E402


def out_json(data: object) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def ok(msg: str) -> None:
    print(f"✓ {msg}")


def err(msg: str) -> None:
    print(f"✗ {msg}", file=sys.stderr)


def lines(items: list[str], empty: str = "（无）") -> None:
    if items:
        for s in items:
            print(f"  {s}")
    else:
        print(empty)


def weight_to_priority(weight: float) -> int:
    if weight <= 0.05:
        return 11
    return max(1, round((1.0 - weight) / 0.1) + 1)


def read_file(path: str | None) -> str | None:
    if not path:
        err("缺少文件路径参数")
        return None
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError as e:
        err(f"无法读取文件 {path}: {e}")
        return None


# ============================================================
# 命令组
# ============================================================

def cmd_health(c: BackendClient, a: argparse.Namespace) -> None:
    h = c.health()
    if a.json:
        return out_json(h)
    ok(f"后端正常：{h['cards']} 张卡片 / {h['nodes']} 个节点（v{h['version']}）")


def cmd_card(c: BackendClient, a: argparse.Namespace) -> None:
    sub = a.sub
    if sub == "list":
        cards = c.list_cards()
        if a.json:
            return out_json(cards)
        print(f"共 {len(cards)} 张卡片：")
        return lines([f"{x['id']}  {x['title']}  [{x['type']}]{('  #' + x['tag']) if x.get('tag') else ''}" for x in cards])
    if sub == "get":
        card = c.get_card(a.id)
        if a.json:
            return out_json(card)
        print(f"{card['id']}  {card['title']}  [{card['type']}]")
        if card.get("tag"):
            print(f"  tag: {card['tag']}")
        if card.get("description"):
            print(f"  description: {card['description'][:80]}")
        lines([f"corpus[{i}]: {t[:60]}" for i, t in enumerate(card.get("corpus") or [])], "（暂无语料）")
        if card.get("bound_nodes"):
            print(f"  bound_nodes: {', '.join(card['bound_nodes'])}")
        return
    if sub == "create":
        card = c.create_card(a.parent)
        if a.title:
            card = c.update_card(card["id"], title=a.title)
        if a.type:
            card = c.update_card(card["id"], type=a.type)
        if a.json:
            return out_json(card)
        return ok(f"已创建卡片 {card['id']}（{card['title']}）")
    if sub == "update":
        if not a.field or a.value is None:
            return err("用法: card update <id> <field> <value>")
        c.update_card(a.id, **{a.field: a.value})
        return ok(f"已更新 {a.id} 的 {a.field}")
    if sub == "delete":
        c.delete_card(a.id)
        return ok(f"已删除卡片 {a.id}")
    if sub == "children":
        children = c.get_card_children(a.id)
        if a.json:
            return out_json(children)
        return lines([f"{x['id']}  {x['title']}  [{x['type']}]" for x in children], "（无子卡片）")
    if sub == "corpus-list":
        corpus = c.get_corpus(a.id)
        if a.json:
            return out_json(corpus)
        return lines([f"[{i}] {t[:70]}" for i, t in enumerate(corpus)], "（暂无语料）")
    if sub == "corpus-add":
        c.add_corpus(a.id, " ".join(a.text))
        return ok(f"已为 {a.id} 添加语料")
    if sub == "corpus-update":
        c.update_corpus(a.id, a.index, " ".join(a.text))
        return ok(f"已更新 {a.id} 的语料[{a.index}]")
    if sub == "corpus-remove":
        c.remove_corpus(a.id, a.index)
        return ok(f"已删除 {a.id} 的语料[{a.index}]")
    err(f"未知子命令: card {sub}")


def cmd_node(c: BackendClient, a: argparse.Namespace) -> None:
    sub = a.sub
    if sub == "list":
        nodes = c.list_nodes(a.query)
        if a.json:
            return out_json(nodes)
        print(f"共 {len(nodes)} 个节点：")
        return lines([f"{n['id']}  {n['label']}  ({len(n.get('next_nodes') or [])} 出口)" for n in nodes])
    if sub == "get":
        node = c.get_node(a.id)
        if a.json:
            return out_json(node)
        print(f"{node['id']}  {node['label']}")
        if node.get("description"):
            print(f"  description: {node['description'][:80]}")
        if node.get("bound_cards"):
            print(f"  bound_cards: {', '.join(node['bound_cards'])}")
        return lines(
            [f"→ {r['target_id']}  #{weight_to_priority(r.get('preset_weight', 0))}  [{r.get('connection_type')}]" for r in node.get("next_nodes") or []],
            "（无出向连接）",
        )
    if sub == "create":
        node = c.create_node()
        if a.label:
            node = c.update_node(node["id"], label=a.label)
        if a.json:
            return out_json(node)
        return ok(f"已创建节点 {node['id']}（{node['label']}）")
    if sub == "update":
        if not a.field or a.value is None:
            return err("用法: node update <id> <field> <value>")
        c.update_node(a.id, **{a.field: a.value})
        return ok(f"已更新 {a.id} 的 {a.field}")
    if sub == "delete":
        c.delete_node(a.id)
        return ok(f"已删除节点 {a.id}（引用已级联清理）")
    if sub == "bind":
        r = c.bind_card(a.id, a.card_id)
        return ok(f"已绑定 {a.id} → {a.card_id}（共 {len(r['bound_cards'])} 张）")
    if sub == "unbind":
        c.unbind_card(a.id, a.card_id)
        return ok(f"已解绑 {a.id} → {a.card_id}")
    if sub == "next":
        items = c.get_next_nodes(a.id)
        if a.json:
            return out_json(items)
        return lines(
            [f"→ {x['node']['id']}  {x['node']['label']}  seq={x['ref']['seq']}  w={x['ref']['weight']:.2f}  [{x['ref']['source']}]" for x in items],
            "（无出向连接）",
        )
    if sub == "next-add":
        c.add_next_node(a.id, a.target, preset_priority=a.priority, connection_type=a.type)
        return ok(f"已添加连接 {a.id} → {a.target}")
    if sub == "next-update":
        updates: dict = {}
        if a.priority is not None:
            updates["preset_priority"] = a.priority
        if a.type:
            updates["connection_type"] = a.type
        if not updates:
            return err("用法: node next-update <id> <target> [--priority n] [--type t]")
        c.update_next_node(a.id, a.target, **updates)
        return ok(f"已更新连接 {a.id} → {a.target}")
    if sub == "next-remove":
        c.remove_next_node(a.id, a.target)
        return ok(f"已删除连接 {a.id} → {a.target}")
    if sub == "prev":
        items = c.get_prev_nodes(a.id)
        if a.json:
            return out_json(items)
        return lines([f"{x['node']['id']}  {x['node']['label']}" for x in items], "（无前驱节点）")
    if sub == "history":
        hist = c.get_browse_history(a.id)
        if a.json:
            return out_json(hist)
        return lines([f"from {h['from']}  ×{h['count']}  {h.get('last_at', '')}" for h in hist], "（无浏览历史）")
    err(f"未知子命令: node {sub}")


def cmd_graph(c: BackendClient, a: argparse.Namespace) -> None:
    if a.sub == "nodes":
        nodes = c.graph_nodes()
        if a.json:
            return out_json(nodes)
        return lines([f"{n['id']}  {n['label']}" for n in nodes])
    if a.sub == "edges":
        edges = c.graph_edges()
        if a.json:
            return out_json(edges)
        print(f"共 {len(edges)} 条有向边：")
        return lines([f"{e['source']} → {e['target']}  w={e['weight']}" for e in edges])
    if a.sub == "sync":
        r = c.graph_sync()
        return ok(f"已重算图：{r['nodes']} 节点 / {r['edges']} 边")
    err(f"未知子命令: graph {a.sub}")


def _plan_line(p: dict) -> str:
    seq = " → ".join(n["label"] for n in p["sequence"])
    return f"{p['id']}  {p['label']}  总权重 {p['totalWeight']:.2f}{'  [推荐]' if p.get('isRecommended') else ''}  {seq}"


def cmd_plan(c: BackendClient, a: argparse.Namespace) -> None:
    if a.sub == "generate":
        ids = [s.strip() for s in a.ids.split(",") if s.strip()] if a.ids else None
        plans = c.generate_plans(ids, waypoint_mode=a.waypoint_mode, weight_mode=a.weight_mode)
        if a.json:
            return out_json(plans)
        ok(f"已生成 {len(plans)} 个候选计划：")
        return lines([_plan_line(p) for p in plans])
    if a.sub == "list":
        plans = c.list_plans()
        if a.json:
            return out_json(plans)
        return lines([_plan_line(p) for p in plans], "（尚无候选计划，请先 plan generate）")
    if a.sub == "get":
        plan = c.get_plan(a.id)
        if a.json:
            return out_json(plan)
        print(_plan_line(plan))
        print(f"  算法: {plan['algorithm']}")
        return lines([f"{i + 1}. {n['id']}  {n['label']}" for i, n in enumerate(plan["sequence"])])
    if a.sub == "select":
        c.select_plan(a.id)
        return ok(f"已选中计划 {a.id}")
    if a.sub == "replan":
        plans = c.replan()
        if a.json:
            return out_json(plans)
        return ok(f"已重新规划，共 {len(plans)} 个候选计划")
    err(f"未知子命令: plan {a.sub}")


def cmd_browse(c: BackendClient, a: argparse.Namespace) -> None:
    if a.sub == "start":
        ids = [s.strip() for s in a.sequence.split(",") if s.strip()] if a.sequence else None
        r = c.browse_start(plan_id=a.plan, sequence=ids)
        return ok(f"已开始浏览（{r['waypoints']} 站）")
    if a.sub == "status":
        s = c.browse_status()
        if a.json:
            return out_json(s)
        print(f"  站点: {s['waypointIndex'] + 1} / {s['totalWaypoints']}")
        print(f"  卡片: {s['cardIndex'] + 1} / {s['totalCards']}")
        return
    if a.sub == "cards":
        cards = c.browse_cards()
        if a.json:
            return out_json(cards)
        return lines([f"[{i}] {x['title']}{('  #' + x['tag']) if x.get('tag') else ''}  {x['desc'][:40]}" for i, x in enumerate(cards)], "（无浏览卡片，请先 browse start）")
    if a.sub == "next":
        c.browse_next()
        return ok("已切换到下一张卡片")
    if a.sub == "prev":
        c.browse_prev()
        return ok("已切换到上一张卡片")
    if a.sub == "waypoint":
        c.browse_next_waypoint()
        return ok("已切换到下一站")
    err(f"未知子命令: browse {a.sub}")


def cmd_search(c: BackendClient, a: argparse.Namespace) -> None:
    if a.sub == "query":
        results = c.search(" ".join(a.text), mode=a.mode)
        if a.json:
            return out_json(results)
        if not results:
            print("无匹配结果")
            return
        print(f"共 {len(results)} 条匹配：")
        return lines([f"{m['card']['id']}  {m['card']['title']}  score={m['score']:.2f}" for m in results])
    if a.sub == "vector":
        results = c.vector_match(" ".join(a.text))
        if a.json:
            return out_json(results)
        return lines([f"{m['card']['id']}  {m['card']['title']}  score={m['score']:.2f}" for m in results], "无匹配结果")
    err(f"未知子命令: search {a.sub}")


def cmd_yaml(c: BackendClient, a: argparse.Namespace) -> None:
    if a.sub == "export":
        raw = c.yaml_export()
        if a.file:
            Path(a.file).write_text(raw, encoding="utf-8")
            return ok(f"已导出 → {a.file}")
        print(raw)
        return
    raw = read_file(a.file)
    if raw is None:
        return
    if a.sub == "validate":
        data = c.yaml_validate(raw)
        return ok(f"YAML 合法：{len(data['cognitive_cards'])} 张卡片，{len(data['navigation_nodes'])} 个节点")
    if a.sub == "preview":
        p = c.yaml_preview(raw)
        if a.json:
            return out_json(p)
        print("导入预览：")
        print(f"  认知卡片: 共 {p['cards']['total']} 张（新增 {p['cards']['added']}，覆盖 {p['cards']['overwritten']}）")
        print(f"  导航节点: 共 {p['nodes']['total']} 个（新增 {p['nodes']['added']}，覆盖 {p['nodes']['overwritten']}）")
        return
    if a.sub == "import":
        p = c.yaml_import(raw)
        ok(f"已导入 {p['cards']['total']} 张认知卡片和 {p['nodes']['total']} 个导航节点")
        print(f"  卡片: 新增 {p['cards']['added']}，覆盖 {p['cards']['overwritten']}")
        print(f"  节点: 新增 {p['nodes']['added']}，覆盖 {p['nodes']['overwritten']}")
        return
    err(f"未知子命令: yaml {a.sub}")


def cmd_ai(c: BackendClient, a: argparse.Namespace) -> None:
    result = c.ai_generate(a.sub, a.id)
    if a.json:
        return out_json({"ok": True, "data": result})
    ok(f"生成结果：{result}")


def cmd_conn(c: BackendClient, a: argparse.Namespace) -> None:
    if a.sub == "status":
        r = c.connection_status(a.from_id, a.to_id)
        if a.json:
            return out_json(r)
        if r["status"] == "connected":
            ref = r["ref"]
            return print(f"✓ 已连接 · 优先级 #{weight_to_priority(ref.get('preset_weight', 0))} · {ref.get('connection_type')}")
        if r["status"] == "missing":
            return print("✚ 缺失连接（可新建）")
        return print("⚠ 节点不可用")
    if a.sub == "ensure":
        r = c.connection_ensure(a.from_id, a.to_id)
        return ok("已建立连接" if r.get("created") else "连接已存在")
    if a.sub == "update":
        updates: dict = {}
        if a.priority is not None:
            updates["preset_priority"] = a.priority
        if a.type:
            updates["connection_type"] = a.type
        if not updates:
            return err("用法: conn update <from> <to> [--priority n] [--type t]")
        c.connection_update(a.from_id, a.to_id, **updates)
        return ok(f"已更新连接 {a.from_id} → {a.to_id}")
    if a.sub == "remove":
        c.connection_remove(a.from_id, a.to_id)
        return ok(f"已删除连接 {a.from_id} → {a.to_id}")
    if a.sub == "fill-all":
        ids = [s.strip() for s in a.ids.split(",") if s.strip()]
        r = c.connections_fill_all(ids)
        return ok(f"已建立 {r['count']} 条跳转连接" if r["count"] else "所有相邻途经点均已连接")
    err(f"未知子命令: conn {a.sub}")


def cmd_view(c: BackendClient, a: argparse.Namespace) -> None:
    if a.sub == "get":
        print(c.view_current()["view"])
        return
    if a.sub == "set":
        r = c.view_switch(a.name)
        return ok(f"已切换到 {r['view']} 视图")
    err(f"未知子命令: view {a.sub}")


# ============================================================
# 参数解析
# ============================================================

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="kn-backend-cli", description="Knowledge Navigator 后端 CLI")
    p.add_argument("--url", default=os.environ.get("KN_BACKEND_URL", "http://localhost:8171"), help="后端地址")
    p.add_argument("--json", action="store_true", help="输出原始 JSON")
    p.add_argument("group", choices=["health", "card", "node", "graph", "plan", "browse", "search", "yaml", "ai", "conn", "view"])
    p.add_argument("sub", nargs="?", default="list")
    p.add_argument("args", nargs="*", help="位置参数（id / target / card_id 等，含义因子命令而异）")
    p.add_argument("--parent")
    p.add_argument("--title")
    p.add_argument("--label")
    p.add_argument("--type")
    p.add_argument("--query")
    p.add_argument("--priority", type=int)
    p.add_argument("--ids")
    p.add_argument("--plan")
    p.add_argument("--sequence")
    p.add_argument("--mode")
    p.add_argument("--waypoint-mode", default="unordered")
    p.add_argument("--weight-mode", default="mixed")
    p.add_argument("--file")
    p.add_argument("--index", type=int, default=0)
    return p


def main() -> int:
    parser = build_parser()
    a = parser.parse_args()

    # 位置参数归一化（不同子命令含义不同，按需取用）
    a.id = a.args[0] if len(a.args) > 0 else None
    a.target = a.args[1] if len(a.args) > 1 else None
    a.card_id = a.args[1] if len(a.args) > 1 else None
    a.from_id = a.args[0] if len(a.args) > 0 else None
    a.to_id = a.args[1] if len(a.args) > 1 else None
    a.field = a.args[1] if len(a.args) > 1 else None
    a.value = a.args[2] if len(a.args) > 2 else None
    a.name = a.args[0] if len(a.args) > 0 else None
    a.text = a.args[1:] if len(a.args) > 1 else []
    # card corpus-add <id> <text...> / search query <text...>
    if a.group == "search":
        a.text = a.args
    if a.group == "conn" and a.sub == "fill-all":
        a.ids = a.args[0] if a.args else a.ids
    # yaml validate/preview/import 的文件路径取位置参数
    if a.group == "yaml" and a.sub in ("validate", "preview", "import") and a.args:
        a.file = a.args[0]

    client = BackendClient(a.url)
    handlers = {
        "health": cmd_health,
        "card": cmd_card,
        "node": cmd_node,
        "graph": cmd_graph,
        "plan": cmd_plan,
        "browse": cmd_browse,
        "search": cmd_search,
        "yaml": cmd_yaml,
        "ai": cmd_ai,
        "conn": cmd_conn,
        "view": cmd_view,
    }
    try:
        handlers[a.group](client, a)
    except BackendError as e:
        err(e.message if e.status < 0 else f"HTTP {e.status}: {e.message}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
