"""从 cognitive-cards 项目生成知识导航导入 YAML。

数据源：../cognitive-cards/data/{cards.json, kits.json}
输出：  imports/cognitive-cards-kits.yaml

映射规则（mind-toolbox-import.md §二）：
- 新建一级文件夹卡片 root/7「心智工具箱 · 设计者循环」
- 10 张概念卡片 → root/7/1 ~ root/7/10（corpus = insight / design_directive / product_form）
- 8 个锦囊 → 卡片 root/7/11 ~ root/7/18（corpus = body 段落 + mechanism）
         + 导航节点 node-kit-a ~ node-kit-h（label = "字母 · 名称"）
- 锦囊节点按 next_kits 建立出向连接，权重按顺序 1.0 / 0.9 递减（preset）
- 每个锦囊节点绑定对应的锦囊卡片（browse 时可翻阅）
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
SOURCE_DIR = PROJECT.parent / "cognitive-cards" / "data"
OUT_FILE = PROJECT / "imports" / "cognitive-cards-kits.yaml"

ROOT_ID = "root/7"
KIT_NODE_PREFIX = "node-kit-"


def load(name: str) -> dict:
    with open(SOURCE_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def build_cards(cards_src: list[dict], kits_src: list[dict]) -> list[dict]:
    out: list[dict] = []

    # 一级文件夹
    out.append({
        "id": ROOT_ID,
        "title": "心智工具箱 · 设计者循环",
        "type": "folder",
        "tag": "心智工具",
        "description": "来自 cognitive-cards 项目的 10 张概念卡片与 8 个锦囊（设计者 ↔ 执行者循环）。",
        "corpus": [],
        "bound_nodes": [f"{KIT_NODE_PREFIX}{k['id'].split('_')[1]}" for k in kits_src],
    })

    # 概念卡片
    for i, c in enumerate(cards_src, start=1):
        sections = c.get("sections") or {}
        corpus = [s for s in (sections.get("insight"), sections.get("design_directive"), sections.get("product_form")) if s]
        out.append({
            "id": f"{ROOT_ID}/{i}",
            "title": f"{c.get('number', '')} {c['title']}".strip(),
            "type": "leaf",
            "tag": (c.get("tags") or ["概念"])[0],
            "description": sections.get("insight", ""),
            "corpus": corpus,
            "bound_nodes": [],
            "metadata": {"created_at": (c.get("metadata") or {}).get("created_at")},
        })

    # 锦囊卡片（绑定到对应锦囊节点）
    for j, k in enumerate(kits_src, start=1):
        suffix = k["id"].split("_")[1]  # kit_a → a
        corpus = list(k.get("body") or [])
        if k.get("mechanism"):
            corpus.append(f"机制：{k['mechanism']}")
        out.append({
            "id": f"{ROOT_ID}/{len(cards_src) + j}",
            "title": f"锦囊 {k['letter']} · {k['name']}",
            "type": "leaf",
            "tag": "锦囊",
            "description": k.get("trigger", ""),
            "corpus": corpus,
            "bound_nodes": [f"{KIT_NODE_PREFIX}{suffix}"],
        })

    return out


def build_nodes(kits_src: list[dict], card_count: int) -> list[dict]:
    out: list[dict] = []
    for j, k in enumerate(kits_src, start=1):
        suffix = k["id"].split("_")[1]
        next_nodes = []
        for seq, nxt in enumerate(k.get("next_kits") or []):
            next_nodes.append({
                "target_id": f"{KIT_NODE_PREFIX}{nxt.split('_')[1]}",
                "preset_weight": round(1.0 - seq * 0.1, 2),
                "browse_weight": 0,
                "connection_type": "preset",
            })
        out.append({
            "id": f"{KIT_NODE_PREFIX}{suffix}",
            "label": f"{k['letter']} · {k['name']}",
            "description": k.get("mechanism") or k.get("trigger", ""),
            "bound_cards": [f"{ROOT_ID}/{card_count + j}"],
            "next_nodes": next_nodes,
        })
    return out


def main() -> None:
    cards_src = load("cards.json")["cards"]
    kits_src = load("kits.json")["kits"]

    payload = {
        "cognitive_cards": build_cards(cards_src, kits_src),
        "navigation_nodes": build_nodes(kits_src, len(cards_src)),
    }

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        yaml.safe_dump(payload, f, allow_unicode=True, sort_keys=False)

    edges = sum(len(n["next_nodes"]) for n in payload["navigation_nodes"])
    print(f"已生成 {OUT_FILE}")
    print(f"  认知卡片: {len(payload['cognitive_cards'])}（1 文件夹 + {len(cards_src)} 概念 + {len(kits_src)} 锦囊）")
    print(f"  导航节点: {len(payload['navigation_nodes'])}（{edges} 条出向连接）")


if __name__ == "__main__":
    main()
