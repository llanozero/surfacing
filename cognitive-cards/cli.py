#!/usr/bin/env python3
"""cognitive-cards CLI — 三阶段涌现引擎命令行工具

用法:
  python cli.py run "越准备越焦虑，迟迟无法开始"
  python cli.py match "越准备越焦虑"
  python cli.py refine "越准备越焦虑" --card-id card_05
  python cli.py emerge "越准备越焦虑"
  python cli.py cards list
  python cli.py kits list
  python cli.py health
"""

from __future__ import annotations

import argparse
import json
import sys
import os
import urllib.request
import urllib.error
import urllib.parse

# 强制 stdout 使用 UTF-8，解决 Windows GBK 终端编码问题
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

DEFAULT_SERVER = "http://localhost:8170"
TIMEOUT = 10


def api_get(server: str, path: str) -> dict:
    url = f"{server}{path}"
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(body).get("detail", body)
        except Exception:
            detail = body
        die(f"HTTP {e.code}: {detail}")
    except urllib.error.URLError:
        die(f"无法连接到 {server}\n请先启动服务: python server.py")
    except Exception as e:
        die(f"请求失败: {e}")


def api_post(server: str, path: str, data: dict) -> dict:
    url = f"{server}{path}"
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json; charset=utf-8")
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        resp_body = e.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(resp_body).get("detail", resp_body)
        except Exception:
            detail = resp_body
        die(f"HTTP {e.code}: {detail}")
    except urllib.error.URLError:
        die(f"无法连接到 {server}\n请先启动服务: python server.py")
    except Exception as e:
        die(f"请求失败: {e}")


def die(msg: str):
    print(f"\n  ✗ {msg}\n", file=sys.stderr)
    sys.exit(1)


# ════════════════════════════════════════════════════════
# 输出格式化
# ════════════════════════════════════════════════════════

def format_matched_cards(data: dict) -> str:
    cards = data.get("matched_cards", [])
    state = data.get("user_state_analysis", {})
    if not cards:
        return "  未匹配到卡片"

    lines = [
        "═" * 55,
        "  语义匹配结果",
        "═" * 55,
        "",
    ]
    for i, c in enumerate(cards):
        prefix = "★" if i == 0 else "·"
        lines.append(f"  {prefix} Card {c['number']} \xb7 {c['title']}  "
                     f"\u7f6e\u4fe1\u5ea6 {c['confidence']:.3f}")
        lines.append(f"    {c['reason']}")
        lines.append("")

    if state:
        lines.append(f"  用户状态分析:")
        lines.append(f"    心态: {state.get('dominant_mindset', '-')}")
        lines.append(f"    位置: {state.get('cycle_position', '-')}")
        risks = state.get('risk_signals', [])
        if risks:
            lines.append(f"    风险: {risks}")
        lines.append("")

    return "\n".join(lines)


def format_refined_corpus(data: dict) -> str:
    card_id = data.get("card_id", "-")
    card_title = data.get("card_title", "-")
    style = data.get("user_style_profile", "-")
    entries = data.get("entries", [])

    lines = [
        "═" * 55,
        f"  语料库细化 \xb7 {card_id}\u300c{card_title}\u300d",
        f"  用户风格: {style}",
        "═" * 55,
        "",
    ]
    if not entries:
        lines.append("  (无匹配语料)")
    for e in entries:
        content = e.get("content", "")
        if len(content) > 80:
            content = content[:77] + "..."
        lines.append(f"  [{e.get('final_score', 0):.2f}] \"{content}\"")
        tags = ", ".join(e.get("style_tags", []))
        kws = ", ".join(e.get("match_keywords", []))
        lines.append(f"         风格: {tags}")
        lines.append(f"         关键词: {kws}")
        ann = e.get("annotation", "")
        if ann:
            lines.append(f"         注: {ann}")
        lines.append("")

    return "\n".join(lines)


def format_emergence(data: dict) -> str:
    kit = data.get("emergent_kit", {})
    path = data.get("predicted_path", [])
    warnings_list = data.get("warnings", [])
    cards = data.get("matched_cards", [])

    lines = [
        "═" * 55,
        "  锦囊路径涌现",
        "═" * 55,
        "",
    ]

    # 匹配卡片摘要
    if cards:
        primary = cards[0]
        lines.append(f"  匹配: Card {primary['number']} \xb7 {primary['title']}")
        lines.append("")

    # 锦囊信息
    kit_name = kit.get("name", "-")
    kit_letter = kit.get("letter", "-")
    guidance = kit.get("guidance", "")
    body_action = kit.get("body_action", "")

    lines.append(f"  \U0001f4e6 锦囊 {kit_letter} \xb7 {kit_name}")
    lines.append("")
    for line in guidance.split("\n"):
        lines.append(f"  {line}")
    lines.append("")
    if body_action:
        lines.append(f"  \U0001f3c3 身体动作: {body_action}")
    lines.append("")

    # 预测路径
    if path:
        lines.append("  " + "\u2500" * 41)
        lines.append("  预测路径:")
        for step in path:
            lines.append(f"    {step['step']}. 锦囊 {step.get('kit_name', '-')}  "
                         f"\u2192 {step.get('action', '-')}")
        lines.append("")

    # 警告
    if warnings_list:
        for w in warnings_list:
            lines.append(f"  \u26a0\ufe0f  {w}")
        lines.append("")

    return "\n".join(lines)


def format_cards_list(cards: list) -> str:
    lines = [
        "═" * 55,
        f"  认知卡片 ({len(cards)} 张)",
        "═" * 55,
        "",
    ]
    for c in cards:
        tags = ", ".join(c.get("tags", [])[:3])
        lines.append(f"  Card {c['number']} \xb7 {c['title']}")
        lines.append(f"    ID: {c['id']}  |  {tags}")
        lines.append("")
    return "\n".join(lines)


def format_card_detail(card: dict) -> str:
    sections = card.get("sections", {})
    lines = [
        "═" * 55,
        f"  Card {card['number']} \xb7 {card['title']}",
        "═" * 55,
        "",
        f"  ID: {card['id']}",
        f"  标签: {', '.join(card.get('tags', []))}",
        f"  关键词: {', '.join(card.get('keywords', []))}",
        "",
    ]
    if sections:
        lines.append(f"  洞察:")
        insight = sections.get("insight", "")
        for line in _wrap(insight, 51):
            lines.append(f"    {line}")
        lines.append("")
        lines.append(f"  设计指令:")
        directive = sections.get("design_directive", "")
        for line in _wrap(directive, 51):
            lines.append(f"    {line}")
        lines.append("")
        lines.append(f"  产品形态:")
        product = sections.get("product_form", "")
        for line in _wrap(product, 51):
            lines.append(f"    {line}")
        lines.append("")

    return "\n".join(lines)


def format_kits_list(kits: list) -> str:
    lines = [
        "═" * 55,
        f"  锦囊 ({len(kits)} 枚)",
        "═" * 55,
        "",
    ]
    for k in kits:
        lines.append(f"  锦囊 {k['letter']} \xb7 {k['name']}")
        lines.append(f"    ID: {k['id']}  |  位置: {k.get('cycle_position', '-')}")
        lines.append(f"    触发: {k.get('trigger', '')[:60]}")
        lines.append("")
    return "\n".join(lines)


def format_kit_detail(kit: dict) -> str:
    lines = [
        "═" * 55,
        f"  锦囊 {kit['letter']} \xb7 {kit['name']}",
        "═" * 55,
        "",
        f"  ID: {kit['id']}",
        f"  位置: {kit.get('cycle_position', '-')}",
        f"  触发: {kit.get('trigger', '')}",
        f"  机制: {kit.get('mechanism', '')}",
        "",
    ]
    for i, paragraph in enumerate(kit.get("body", []), 1):
        lines.append(f"  [{i}]")
        for line in _wrap(paragraph, 51):
            lines.append(f"    {line}")
        lines.append("")

    next_kits = kit.get("next_kits", [])
    if next_kits:
        lines.append(f"  下一锦囊: {', '.join(next_kits)}")
        lines.append("")

    return "\n".join(lines)


def format_corpus_list(entries: list) -> str:
    lines = [
        "═" * 55,
        f"  语料库 ({len(entries)} 条)",
        "═" * 55,
        "",
    ]
    for e in entries:
        content = e.get("content", "")
        if len(content) > 70:
            content = content[:67] + "..."
        lines.append(f"  [{e['id']}] card={e.get('card_id', '-')}")
        lines.append(f"    {content}")
        lines.append(f"    风格: {', '.join(e.get('style_tags', []))}")
        lines.append("")
    return "\n".join(lines)


def _wrap(text: str, width: int) -> list[str]:
    """中文友好换行。"""
    lines = []
    current = ""
    for ch in text:
        if ch == "\n":
            lines.append(current)
            current = ""
        elif len(current) >= width:
            lines.append(current)
            current = ch
        else:
            current += ch
    if current:
        lines.append(current)
    return lines


# ════════════════════════════════════════════════════════
# 命令处理
# ════════════════════════════════════════════════════════

def cmd_run(args):
    data = api_post(args.server, "/api/emergence", {"text": args.text, "source": "cli"})
    if args.format == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(format_emerge_card_summary(data))
        print(format_emergence(data))


def format_emerge_card_summary(data: dict) -> str:
    """管道完整输出的简短摘要，放在锦囊涌现之前。"""
    matched = data.get("matched_cards", [])
    if not matched:
        return ""
    return format_matched_cards(data)


def cmd_match(args):
    data = api_post(args.server, "/api/emergence/match",
                    {"text": args.text, "source": "cli", "top_k": args.top_k})
    if args.format == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(format_matched_cards(data))


def cmd_refine(args):
    card_id = args.card_id
    if not card_id:
        match_data = api_post(args.server, "/api/emergence/match",
                              {"text": args.text, "source": "cli", "top_k": 1})
        matched = match_data.get("matched_cards", [])
        if not matched:
            die("未匹配到任何卡片，无法进行语料细化")
        card_id = matched[0]["card_id"]

    data = api_post(args.server, "/api/emergence/refine",
                    {"text": args.text, "card_id": card_id, "top_n": args.top_n})
    if args.format == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(format_refined_corpus(data))


def cmd_emerge(args):
    data = api_post(args.server, "/api/emergence", {"text": args.text, "source": "cli"})
    if args.format == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(format_matched_cards(data))
        print(format_emergence(data))


def cmd_cards(args):
    if args.action == "list":
        cards = api_get(args.server, "/api/cards")
        if args.format == "json":
            print(json.dumps(cards, ensure_ascii=False, indent=2))
        else:
            print(format_cards_list(cards))
    elif args.action == "show":
        card_id = _resolve_card_id(args.id_or_number)
        card = api_get(args.server, f"/api/cards/{card_id}")
        if args.format == "json":
            print(json.dumps(card, ensure_ascii=False, indent=2))
        else:
            print(format_card_detail(card))


def cmd_kits(args):
    if args.action == "list":
        kits = api_get(args.server, "/api/kits")
        if args.format == "json":
            print(json.dumps(kits, ensure_ascii=False, indent=2))
        else:
            print(format_kits_list(kits))
    elif args.action == "show":
        kit = api_get(args.server, f"/api/kits/{args.kit_id}")
        if args.format == "json":
            print(json.dumps(kit, ensure_ascii=False, indent=2))
        else:
            print(format_kit_detail(kit))


def cmd_corpus(args):
    query = {}
    if args.card_id:
        query["card_id"] = args.card_id
    path = "/api/corpus"
    if query:
        path += "?" + urllib.parse.urlencode(query)
    entries = api_get(args.server, path)
    if args.format == "json":
        print(json.dumps(entries, ensure_ascii=False, indent=2))
    else:
        print(format_corpus_list(entries))


def cmd_health(args):
    data = api_get(args.server, "/api/health")
    if args.format == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(f"\n  \u2713 {data.get('name', '-')} v{data.get('version', '-')}")
        print(f"    状态: {data.get('status', '-')}\n")


def cmd_archive(args):
    data = api_get(args.server, "/api/archive")
    if args.format == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(format_archive(data))


def format_archive(data: dict) -> str:
    lines = [
        "═" * 55,
        f"  系统架构 \xb7 {data.get('system_name', '-')}",
        "═" * 55,
        "",
    ]
    for layer in data.get("layers", []):
        lines.append(f"  L{layer['layer']}: {layer['name']}")
        lines.append(f"    {', '.join(layer.get('cards', []))}")
        desc = layer.get("description", "")
        for line in _wrap(desc, 49):
            lines.append(f"    {line}")
        lines.append("")

    cycle = data.get("core_cycle", {})
    if cycle:
        lines.append(f"  主循环: {cycle.get('main', '-')}")
        lines.append(f"  旁路:   {cycle.get('side', '-')}")
        lines.append("")

    lines.append(f"  卡片: {data.get('cards_count', 0)} 张")
    lines.append(f"  锦囊: {data.get('kits_count', 0)} 枚")
    lines.append(f"  语料: {data.get('corpus_entries_count', 0)} 条")
    lines.append("")

    return "\n".join(lines)


def _resolve_card_id(id_or_number: str) -> str:
    """支持 'card_05' 或 '05' 两种输入。"""
    if id_or_number.startswith("card_"):
        return id_or_number
    if id_or_number.isdigit():
        return f"card_{int(id_or_number):02d}"
    return id_or_number


# ════════════════════════════════════════════════════════
# 参数解析
# ════════════════════════════════════════════════════════

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cognitive",
        description="cognitive-cards CLI — 三阶段涌现引擎命令行工具",
    )
    parser.add_argument("--server", default=DEFAULT_SERVER,
                        help=f"服务地址 (默认: {DEFAULT_SERVER})")

    sub = parser.add_subparsers(dest="command", help="子命令")

    # run — 完整管道
    p_run = sub.add_parser("run", help="完整三阶段管道")
    p_run.add_argument("text", help="用户输入文本")
    p_run.add_argument("-f", "--format", choices=["pretty", "json"], default="pretty",
                       help="输出格式 (默认: pretty)")

    # match — 阶段一
    p_match = sub.add_parser("match", help="阶段一：语义匹配卡片")
    p_match.add_argument("text", help="用户输入文本")
    p_match.add_argument("-k", "--top-k", type=int, default=3,
                          help="返回匹配数 (默认: 3)")
    p_match.add_argument("-f", "--format", choices=["pretty", "json"], default="pretty")

    # refine — 阶段二
    p_refine = sub.add_parser("refine", help="阶段二：语料库细化")
    p_refine.add_argument("text", help="用户输入文本")
    p_refine.add_argument("--card-id", default=None,
                           help="目标卡片 ID (不指定则自动匹配)")
    p_refine.add_argument("-n", "--top-n", type=int, default=5,
                           help="返回条目数 (默认: 5)")
    p_refine.add_argument("-f", "--format", choices=["pretty", "json"], default="pretty")

    # emerge — 阶段三
    p_emerge = sub.add_parser("emerge", help="阶段三：锦囊路径涌现")
    p_emerge.add_argument("text", help="用户输入文本")
    p_emerge.add_argument("-f", "--format", choices=["pretty", "json"], default="pretty")

    # cards
    p_cards = sub.add_parser("cards", help="认知卡片管理")
    p_cards_sub = p_cards.add_subparsers(dest="action", help="操作")
    p_cards_list = p_cards_sub.add_parser("list", help="列出所有卡片")
    p_cards_list.add_argument("-f", "--format", choices=["pretty", "json"], default="pretty")
    p_cards_show = p_cards_sub.add_parser("show", help="查看卡片详情")
    p_cards_show.add_argument("id_or_number", help="卡片 ID 或编号 (如 card_05 或 05)")
    p_cards_show.add_argument("-f", "--format", choices=["pretty", "json"], default="pretty")

    # kits
    p_kits = sub.add_parser("kits", help="锦囊管理")
    p_kits_sub = p_kits.add_subparsers(dest="action", help="操作")
    p_kits_list = p_kits_sub.add_parser("list", help="列出所有锦囊")
    p_kits_list.add_argument("-f", "--format", choices=["pretty", "json"], default="pretty")
    p_kits_show = p_kits_sub.add_parser("show", help="查看锦囊详情")
    p_kits_show.add_argument("kit_id", help="锦囊 ID (如 kit_b)")
    p_kits_show.add_argument("-f", "--format", choices=["pretty", "json"], default="pretty")

    # corpus
    p_corpus = sub.add_parser("corpus", help="语料库浏览")
    p_corpus_sub = p_corpus.add_subparsers(dest="action", help="操作")
    p_corpus_list = p_corpus_sub.add_parser("list", help="列出语料条目")
    p_corpus_list.add_argument("card_id", nargs="?", default=None,
                                help="按卡片 ID 过滤 (可选)")
    p_corpus_list.add_argument("-f", "--format", choices=["pretty", "json"], default="pretty")

    # health
    p_health = sub.add_parser("health", help="服务健康检查")
    p_health.add_argument("-f", "--format", choices=["pretty", "json"], default="pretty")

    # archive
    p_archive = sub.add_parser("archive", help="系统架构概览")
    p_archive.add_argument("-f", "--format", choices=["pretty", "json"], default="pretty")

    return parser


# ════════════════════════════════════════════════════════
# 入口
# ════════════════════════════════════════════════════════

COMMAND_MAP = {
    "run": cmd_run,
    "match": cmd_match,
    "refine": cmd_refine,
    "emerge": cmd_emerge,
    "cards": cmd_cards,
    "kits": cmd_kits,
    "corpus": cmd_corpus,
    "health": cmd_health,
    "archive": cmd_archive,
}


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    handler = COMMAND_MAP.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
