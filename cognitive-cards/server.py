"""认知卡片 · Web 服务原型 — 核心服务器

这是认知卡片系统的完整 web 服务原型，提供：
- 卡片数据的 REST API（CRUD）
- 锦囊数据 API
- 涌现引擎：用户输入 → 卡片匹配 → 语料细化 → 锦囊路径生成
- 静态前端资源托管

启动方式：
    pip install -r requirements.txt
    python server.py
    # 然后访问 http://localhost:8170
"""

from __future__ import annotations

import json
import math
import re
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# ── 配置 ──────────────────────────────────────────────

HOST = "0.0.0.0"
PORT = 8170
DATA_DIR = Path(__file__).parent / "data"
STATIC_DIR = Path(__file__).parent / "static"

# ── FastAPI 应用 ────────────────────────────────────────

app = FastAPI(
    title="认知卡片 · Cognitive Cards API",
    description="既是设计说明书，也是产品本身的认知工具系统 API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ════════════════════════════════════════════════════════
# 数据模型
# ════════════════════════════════════════════════════════

class CardSection(BaseModel):
    insight: str
    design_directive: str
    product_form: str


class CardMetadata(BaseModel):
    created_at: str
    updated_at: str
    version: int
    status: str


class CardSummary(BaseModel):
    id: str
    number: str
    title: str
    slug: str
    tags: list[str]
    keywords: list[str]
    parent_id: Optional[str] = None
    child_ids: list[str] = []
    sibling_order: int = 0


class Card(CardSummary):
    type: str = "cognitive_card"
    sections: CardSection
    metadata: CardMetadata


class KitBodyParagraph(BaseModel):
    text: str


class KitData(BaseModel):
    id: str
    letter: str
    name: str
    trigger: str
    body: list[str]
    mechanism: str
    color: str
    cycle_position: str
    next_kits: list[str]


class CorpusEntry(BaseModel):
    id: str
    card_id: str
    type: str
    source: dict
    content: str
    annotation: str
    style_tags: list[str]
    relation_tags: list[str]
    match_keywords: list[str]
    quality_score: float
    metadata: dict


class EmergenceRequest(BaseModel):
    text: str
    source: str = "chat"


class MatchRequest(BaseModel):
    text: str
    source: str = "cli"
    top_k: int = 3


class RefineRequest(BaseModel):
    text: str
    card_id: str
    top_n: int = 5


class MatchedCard(BaseModel):
    card_id: str
    number: str
    title: str
    confidence: float
    reason: str


class EmergenceKit(BaseModel):
    kit_id: str
    letter: str
    name: str
    guidance: str
    body_action: str


class PathStep(BaseModel):
    step: int
    kit_id: str
    kit_name: str
    action: str


class EmergenceResponse(BaseModel):
    matched_cards: list[MatchedCard]
    emergent_kit: EmergenceKit
    predicted_path: list[PathStep]
    warnings: list[str]
    user_state_analysis: dict


class MatchResponse(BaseModel):
    matched_cards: list[MatchedCard]
    user_state_analysis: dict


class RefinedEntry(BaseModel):
    id: str
    card_id: str
    content: str
    annotation: str
    style_tags: list[str]
    match_keywords: list[str]
    final_score: float


class RefineResponse(BaseModel):
    card_id: str
    card_title: str
    user_style_profile: str
    entries: list[RefinedEntry]


# ════════════════════════════════════════════════════════
# 数据加载服务
# ════════════════════════════════════════════════════════

class DataService:
    """加载并缓存所有 JSON 数据。"""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.cards: list[Card] = []
        self.cards_by_id: dict[str, Card] = {}
        self.corpus_entries: list[CorpusEntry] = []
        self.kits: list[KitData] = []
        self.kits_by_id: dict[str, KitData] = {}
        self.path_rules: dict = {}
        self._load()

    def _load(self):
        self._load_cards()
        self._load_corpus()
        self._load_kits()

    def _load_cards(self):
        path = self.data_dir / "cards.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for c in data.get("cards", []):
                card = Card(**c)
                self.cards.append(card)
                self.cards_by_id[card.id] = card

    def _load_corpus(self):
        path = self.data_dir / "corpus.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for e in data.get("entries", []):
                self.corpus_entries.append(CorpusEntry(**e))

    def _load_kits(self):
        path = self.data_dir / "kits.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for k in data.get("kits", []):
                kit = KitData(**k)
                self.kits.append(kit)
                self.kits_by_id[kit.id] = kit
            self.path_rules = data.get("path_rules", {})

    def get_corpus_for_card(self, card_id: str) -> list[CorpusEntry]:
        return [e for e in self.corpus_entries if e.card_id == card_id]

    def get_all_corpus(self) -> list[CorpusEntry]:
        return self.corpus_entries


data_service = DataService(DATA_DIR)


# ════════════════════════════════════════════════════════
# 涌现引擎
# ════════════════════════════════════════════════════════

class EmergenceEngine:
    """三阶段涌现管道：语义匹配 → 语料细化 → 锦囊生成。"""

    def __init__(self, ds: DataService):
        self.ds = ds

    # ── 阶段一：语义匹配 ──

    def match_cards(self, user_text: str, top_k: int = 3) -> list[MatchedCard]:
        """基于 Jaccard 关键词相似度 + TF 权重匹配卡片。"""
        user_keywords = self._extract_keywords(user_text)

        scored = []
        for card in self.ds.cards:
            score = self._jaccard_similarity(user_keywords, set(card.keywords))
            if score > 0:
                scored.append((card, score))

        scored.sort(key=lambda x: x[1], reverse=True)

        results = []
        for card, score in scored[:top_k]:
            reason = self._generate_match_reason(user_text, card, score)
            results.append(MatchedCard(
                card_id=card.id,
                number=card.number,
                title=card.title,
                confidence=round(score, 3),
                reason=reason,
            ))

        if not results and self.ds.cards:
            first = self.ds.cards[0]
            results.append(MatchedCard(
                card_id=first.id,
                number=first.number,
                title=first.title,
                confidence=0.1,
                reason="输入较短，默认推荐第一张卡片作为起点",
            ))

        return results

    def _extract_keywords(self, text: str) -> set[str]:
        """简单中文关键词提取（生产环境应使用 jieba 分词）。"""
        # 提取2-4字的连续中文字符作为候选词
        clean = re.sub(r'[^\u4e00-\u9fff]', '', text)
        keywords = set()
        for length in [2, 3, 4]:
            for i in range(len(clean) - length + 1):
                keywords.add(clean[i:i + length])
        return keywords

    def _jaccard_similarity(self, set_a: set[str], set_b: set[str]) -> float:
        if not set_a or not set_b:
            return 0.0
        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        return intersection / union if union > 0 else 0.0

    def _generate_match_reason(self, user_text: str, card: Card, score: float) -> str:
        if score > 0.3:
            return f"输入关键词与\"{card.title}\"高度相关"
        elif score > 0.15:
            return f"输入内容与\"{card.title}\"存在一定关联"
        else:
            return f"输入与\"{card.title}\"有微弱关联"

    # ── 阶段二：语料库细化 ──

    def refine_corpus(self, card_id: str, user_text: str, top_n: int = 5) -> list[CorpusEntry]:
        """在匹配卡片的语料库中按关键词精筛。"""
        entries = self.ds.get_corpus_for_card(card_id)
        if not entries:
            return []

        user_keywords = self._extract_keywords(user_text)
        scored = []
        for entry in entries:
            kw_match = len(set(entry.match_keywords) & user_keywords)
            final_score = (
                entry.quality_score * 0.4
                + (kw_match / max(len(entry.match_keywords), 1)) * 0.3
                + (1.0 if any(kw in user_text for kw in entry.match_keywords) else 0.0) * 0.3
            )
            if final_score > 0:
                scored.append((entry, final_score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [e for e, _ in scored[:top_n]]

    # ── 阶段三：锦囊路径涌现 ──

    def emerge_guidance(
        self,
        user_text: str,
        matched_cards: list[MatchedCard],
        refined_corpus: list[CorpusEntry],
    ) -> EmergenceResponse:
        """基于匹配结果和细化语料，生成锦囊引导词和预测路径。"""
        if not matched_cards:
            return self._fallback_response(user_text)

        primary_card = matched_cards[0]
        user_state = self._analyze_user_state(user_text)
        entry_kit = self._select_entry_kit(user_state)

        if not entry_kit:
            entry_kit = self.ds.kits_by_id.get("kit_b")

        kit = entry_kit
        if not kit:
            kit = self.ds.kits_by_id.get("kit_a")

        guidance = self._compose_guidance(user_text, primary_card, kit, refined_corpus)
        body_action = self._extract_body_action(guidance)

        path_rules = self.ds.path_rules
        rule_key = self._select_path_rule(user_state)
        rule = path_rules.get(rule_key, path_rules.get("from_designer_stuck", {}))

        predicted_path = []
        path_kit_ids = rule.get("predicted_path", [kit.id])
        warnings_list = [rule.get("warning", "")] if rule.get("warning") else []
        warnings_list.append("当前阶段禁止提前复盘（kit_h 风险）")
        warnings_list.append("在未经历执行者具身前不要跳到设计者心态")

        for i, kid in enumerate(path_kit_ids, 1):
            pk = self.ds.kits_by_id.get(kid)
            action_map = {
                "kit_b": "正常化感受，用身体感官绕过语义焦虑",
                "kit_c": "允许负向沉沦抵达终点，不干预",
                "kit_d": "回归锚点，重新进入循环",
                "kit_e": "进入执行者心态，信任预设路径",
                "kit_f": "沉浸于处境，让认知自发涌现",
                "kit_g": "从环境级优化角度复盘",
                "kit_a": "确立设计者锚点，规划下一步",
                "kit_h": "停止！回到执行者轨道",
            }
            predicted_path.append(PathStep(
                step=i,
                kit_id=kid,
                kit_name=pk.name if pk else kid,
                action=action_map.get(kid, "继续循环"),
            ))

        return EmergenceResponse(
            matched_cards=matched_cards,
            emergent_kit=EmergenceKit(
                kit_id=kit.id,
                letter=kit.letter,
                name=kit.name,
                guidance=guidance,
                body_action=body_action,
            ),
            predicted_path=predicted_path,
            warnings=warnings_list,
            user_state_analysis=user_state,
        )

    def _analyze_user_state(self, text: str) -> dict:
        """分析用户心态和循环位置。"""
        state = {
            "dominant_mindset": "设计者心态",
            "cycle_position": "在执行者入口处受阻",
            "risk_signals": [],
        }

        # 关键词检测
        if any(w in text for w in ["拖延", "开始", "准备", "焦虑", "设定"]):
            state["dominant_mindset"] = "设计者心态"
            state["cycle_position"] = "在执行者入口处受阻"
            state["risk_signals"] = ["过度准备", "拖延启动"]

        if any(w in text for w in ["迷失", "涣散", "不对", "方向"]):
            state["dominant_mindset"] = "执行者心态"
            state["cycle_position"] = "执行中迷失"
            state["risk_signals"] = ["注意力涣散", "方向感弱化"]

        if any(w in text for w in ["失败", "崩溃", "放弃", "不行", "搞砸"]):
            state["dominant_mindset"] = "执行者心态"
            state["cycle_position"] = "负向沉沦"
            state["risk_signals"] = ["负向信念激活", "身体抽离"]

        if any(w in text for w in ["复盘", "总结", "回顾", "分析", "优化"]):
            state["dominant_mindset"] = "设计者心态"
            state["cycle_position"] = "设计者复盘阶段"
            state["risk_signals"] = ["警惕提前复盘风险"]

        return state

    def _select_entry_kit(self, state: dict) -> Optional[KitData]:
        """根据用户状态选择入口锦囊。"""
        position = state.get("cycle_position", "")
        if "入口处受阻" in position:
            return self.ds.kits_by_id.get("kit_b")
        elif "迷失" in position:
            return self.ds.kits_by_id.get("kit_b")
        elif "负向沉沦" in position:
            return self.ds.kits_by_id.get("kit_c")
        elif "复盘" in position:
            return self.ds.kits_by_id.get("kit_g")
        else:
            return self.ds.kits_by_id.get("kit_a")

    def _select_path_rule(self, state: dict) -> str:
        position = state.get("cycle_position", "")
        if "入口处受阻" in position:
            return "from_designer_stuck"
        elif "迷失" in position:
            return "from_executor_lost"
        elif "负向沉沦" in position:
            return "from_executor_lost"
        elif "复盘" in position:
            return "from_post_reflection"
        else:
            return "from_executor_flow"

    def _compose_guidance(
        self,
        user_text: str,
        card: MatchedCard,
        kit: KitData,
        corpus: list[CorpusEntry],
    ) -> str:
        """基于卡片、锦囊和语料，生成具身引导词。"""
        # 从语料库采样意象
        corpus_imagery = ""
        if corpus:
            top_entry = corpus[0]
            corpus_imagery = top_entry.content

        # 提取用户情绪关键词
        mood_phrases = []
        if "焦虑" in user_text:
            mood_phrases.append("你描述的那种'越准备越焦虑'的感觉，我认得它。")
        if "拖延" in user_text:
            mood_phrases.append("每次设定目标后又停下——那个'等一下，还没准备好'的声音。")
        if "崩溃" in user_text or "失败" in user_text:
            mood_phrases.append("那不是'你又失败了'——那是你在错误的节律上试图推进。")

        if not mood_phrases:
            mood_phrases.append("你说的这种感受，它是一个信号——一个需要被正常化的信号。")

        # 拼接引导词
        parts = [
            mood_phrases[0],
            "",
            f"这不是你准备不够——是你的{self._mindset_name(card.title)}太早入场了。它在没有球的时候就开始调整姿势，结果越调整越僵。",
        ]

        if corpus_imagery:
            parts.append(f"\n{corpus_imagery}")

        # 锦囊body的第二段通常最合适
        if len(kit.body) >= 2:
            parts.append(f"\n{kit.body[1]}")

        # 身体动作指令
        body_actions = [
            "现在，站起来，走三步。不是去做什么事——只是走三步，感受脚底踩到地板的感觉。三步之后，你会发现那个'准备'的声音安静了一些。\n就在那个安静里，开始。",
            "现在，深吸一口气，慢慢地呼出去。在呼气的末尾，感觉身体里有什么东西松开了。那个松开的瞬间，就是你的入口。",
            "现在，把手放在桌面上，感受木头的温度。你的身体还在这个空间里，它没有走丢。它只是在等你注意到它。",
        ]
        import hashlib
        idx = int(hashlib.md5(user_text.encode()).hexdigest(), 16) % len(body_actions)
        parts.append(f"\n{body_actions[idx]}")

        return "\n".join(parts)

    def _mindset_name(self, card_title: str) -> str:
        mapping = {
            "合拍飞轮": "设计者心态（过度准备）",
            "二阶观察者困境": "审视心态",
            "重新定向能量": "理想前置条件执念",
            "直觉即压缩理性": "刻意努力",
            "具身认知": "提取心态",
            "自发命名": "命名冲动",
        }
        return mapping.get(card_title, "设计者心态")

    def _extract_body_action(self, guidance: str) -> str:
        """从引导词中提取身体动作指令。"""
        action_patterns = [
            r'现在，?站起来.*?。',
            r'现在，?深吸一口气.*?。',
            r'现在，?把手放在.*?。',
            r'走三步.*?。',
        ]
        for pattern in action_patterns:
            m = re.search(pattern, guidance)
            if m:
                return m.group(0)
        return "站起来，走三步，感受脚底踩到地板的感觉"

    def _fallback_response(self, user_text: str) -> EmergenceResponse:
        kit = self.ds.kits_by_id.get("kit_a")
        return EmergenceResponse(
            matched_cards=[],
            emergent_kit=EmergenceKit(
                kit_id=kit.id if kit else "kit_a",
                letter=kit.letter if kit else "A",
                name=kit.name if kit else "锚点确立",
                guidance="你说的这些，我听见了。不需要分析，不需要结论。\n\n现在，深吸一口气，慢慢地呼出去。在呼气的末尾，安静地待一会儿。",
                body_action="深吸一口气，慢慢地呼出去",
            ),
            predicted_path=[
                PathStep(step=1, kit_id="kit_a", kit_name="锚点确立", action="确立设计者锚点")
            ],
            warnings=["输入较模糊，建议多描述一些具体感受"],
            user_state_analysis={"dominant_mindset": "未知", "cycle_position": "起点", "risk_signals": []},
        )


engine = EmergenceEngine(data_service)


# ════════════════════════════════════════════════════════
# API 路由
# ════════════════════════════════════════════════════════

@app.get("/api/health")
def health():
    return {"status": "ok", "name": "认知卡片 · Cognitive Cards API", "version": "1.0.0"}


# ── 卡片相关 ──

@app.get("/api/cards", response_model=list[CardSummary])
def list_cards():
    """获取所有卡片摘要。"""
    return data_service.cards


@app.get("/api/cards/{card_id}", response_model=Card)
def get_card(card_id: str):
    """获取单张卡片完整数据。"""
    card = data_service.cards_by_id.get(card_id)
    if not card:
        raise HTTPException(status_code=404, detail=f"卡片 {card_id} 不存在")
    return card


@app.get("/api/cards/{card_id}/children", response_model=list[CardSummary])
def get_card_children(card_id: str):
    """获取某张卡片的子卡片。"""
    card = data_service.cards_by_id.get(card_id)
    if not card:
        raise HTTPException(status_code=404, detail=f"卡片 {card_id} 不存在")
    return [data_service.cards_by_id[cid] for cid in card.child_ids if cid in data_service.cards_by_id]


@app.get("/api/cards/{card_id}/corpus", response_model=list[CorpusEntry])
def get_card_corpus(card_id: str):
    """获取卡片的语料库（含继承，当前版本只返回直接语料）。"""
    card = data_service.cards_by_id.get(card_id)
    if not card:
        raise HTTPException(status_code=404, detail=f"卡片 {card_id} 不存在")
    return data_service.get_corpus_for_card(card_id)


@app.get("/api/cards/hierarchy")
def get_hierarchy():
    """获取卡片层级树。"""
    root_children = [c for c in data_service.cards if c.parent_id is None]
    return {
        "root": [c.id for c in root_children],
        "nodes": {
            c.id: {
                "id": c.id,
                "title": c.title,
                "number": c.number,
                "children": c.child_ids,
                "parent": c.parent_id,
            }
            for c in data_service.cards
        },
    }


# ── 锦囊相关 ──

@app.get("/api/kits", response_model=list[KitData])
def list_kits():
    """获取所有锦囊。"""
    return data_service.kits


@app.get("/api/kits/{kit_id}", response_model=KitData)
def get_kit(kit_id: str):
    """获取单个锦囊。"""
    kit = data_service.kits_by_id.get(kit_id)
    if not kit:
        raise HTTPException(status_code=404, detail=f"锦囊 {kit_id} 不存在")
    return kit


# ── 语料库相关 ──

@app.get("/api/corpus", response_model=list[CorpusEntry])
def list_corpus(card_id: Optional[str] = Query(None, description="按卡片 ID 过滤")):
    """获取语料库，可选按卡片 ID 过滤。"""
    if card_id:
        return data_service.get_corpus_for_card(card_id)
    return data_service.get_all_corpus()


# ── 系统架构 ──

@app.get("/api/archive")
def get_archive():
    """获取系统架构概览。"""
    return {
        "system_name": "认知卡片 · Cognitive Cards",
        "layers": [
            {
                "layer": 1,
                "name": "问题识别与元策略",
                "cards": ["01 - 二阶观察者困境", "02 - 悖论绕过"],
                "description": "承认困境的结构性，确立'绕过而非解决、感官而非语义'的元策略",
            },
            {
                "layer": 2,
                "name": "工具范式与设计原则",
                "cards": ["03 - 环境级工具", "04 - 容器非模具"],
                "description": "确立工具的根本范式：环境级（非指令级）；确立设计的根本原则：容器（非模具）",
            },
            {
                "layer": 3,
                "name": "核心机制",
                "cards": ["05 - 合拍飞轮", "06 - 直觉即压缩理性", "07 - 具身认知", "08 - 自发命名"],
                "description": "飞轮解决启动、直觉解决执行通道、具身解决知识来源、自发命名解决沉淀",
            },
            {
                "layer": 4,
                "name": "转化与起点",
                "cards": ["09 - 信念覆盖机制", "10 - 重新定向能量"],
                "description": "信念覆盖让旧路径褪色、重新定向从任何起点开始",
            },
        ],
        "core_cycle": {
            "main": "设计者锚点 → 执行者具身 → 设计者复盘 → 外沿扩大",
            "side": "迷失 → 沉沦 → 自防御 → 失忆 → 内生回归 → 重新进入",
        },
        "kits_count": len(data_service.kits),
        "cards_count": len(data_service.cards),
        "corpus_entries_count": len(data_service.corpus_entries),
        "path_rules": data_service.path_rules,
    }


# ── 涌现引擎 ──

@app.post("/api/emergence", response_model=EmergenceResponse)
def emerge(request: EmergenceRequest):
    """运行涌现引擎：输入文本 → 匹配卡片 → 细化语料 → 生成锦囊引导词。"""
    text = request.text.strip()
    if len(text) < 3:
        raise HTTPException(status_code=400, detail="输入过短（少于3个字符），请多描述一些感受")

    matched = engine.match_cards(text, top_k=2)
    if matched:
        corpus = engine.refine_corpus(matched[0].card_id, text, top_n=3)
    else:
        corpus = []

    return engine.emerge_guidance(text, matched, corpus)


# ── 阶段拆分 API ──

@app.post("/api/emergence/match", response_model=MatchResponse)
def emerge_match(request: MatchRequest):
    """阶段一：语义匹配。仅运行卡片匹配，不做语料细化和锦囊生成。"""
    text = request.text.strip()
    if len(text) < 3:
        raise HTTPException(status_code=400, detail="输入过短（少于3个字符），请多描述一些感受")

    matched = engine.match_cards(text, top_k=request.top_k)
    user_state = engine._analyze_user_state(text)

    return MatchResponse(
        matched_cards=matched,
        user_state_analysis=user_state,
    )


@app.post("/api/emergence/refine", response_model=RefineResponse)
def emerge_refine(request: RefineRequest):
    """阶段二：语料库细化。在指定卡片的语料库中按关键词和风格精筛。"""
    card = data_service.cards_by_id.get(request.card_id)
    if not card:
        raise HTTPException(status_code=404, detail=f"卡片 {request.card_id} 不存在")

    text = request.text.strip()
    entries = engine.refine_corpus(request.card_id, text, top_n=request.top_n)

    user_keywords = engine._extract_keywords(text)
    style_profile = "叙事_内省" if any(w in text for w in ["感觉", "觉得", "焦虑", "准备"]) else "简洁_直接"

    return RefineResponse(
        card_id=request.card_id,
        card_title=card.title,
        user_style_profile=style_profile,
        entries=[
            RefinedEntry(
                id=e.id,
                card_id=e.card_id,
                content=e.content,
                annotation=e.annotation,
                style_tags=e.style_tags,
                match_keywords=e.match_keywords,
                final_score=round(
                    e.quality_score * 0.4
                    + (len(set(e.match_keywords) & user_keywords) / max(len(e.match_keywords), 1)) * 0.3
                    + (1.0 if any(kw in text for kw in e.match_keywords) else 0.0) * 0.3,
                    2,
                ),
            )
            for e in entries
        ],
    )


# ── 静态文件 ──

@app.get("/")
def root():
    """返回前端页面。"""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "认知卡片 API 服务运行中", "docs": "/docs", "frontend": "static/index.html 未找到"}


if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ════════════════════════════════════════════════════════
# 入口
# ════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    print(f"\n  认知卡片 · Cognitive Cards API")
    print(f"  ════════════════════════════════")
    print(f"  服务地址: http://localhost:{PORT}")
    print(f"  API 文档: http://localhost:{PORT}/docs")
    print(f"  前端页面: http://localhost:{PORT}/\n")
    uvicorn.run("server:app", host=HOST, port=PORT, reload=True)
