"""職務経歴書の作文生成プロンプト構築サービス（外部依存ゼロの純粋ロジック）。

StatementPromptBuilderService と同構造。案件コンテキスト（事実）から、
職務経歴書に載せる「作文」（職務要約 / 自己PR / 生成AI活用の効果文 / 案件実績文）を
生成させるためのプロンプトを組み立てる。企業名は伏せる（匿名前提）。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.generation.application.dto import EngagementContext

# プロフィール作文の種別
NARRATIVE_KINDS = ("summary", "strengths", "good_at", "ai_effect")

# 案件フィールドの生成種別（industry/overview は下書き用、narrative は実績文）
ENGAGEMENT_FIELD_KINDS = ("industry", "overview", "narrative", "responsibilities", "challenges", "position")

_COMMON_RULES = (
    "# 制約（厳守）\n"
    "- 提供データにない事実の捏造・誇張は禁止。数字は提供された成果の範囲でのみ使う。\n"
    "- 企業名は出さず『◯◯業のSaaS企業』『人材サービス業の受託案件』等、業界＋規模で表現する。\n"
    "- 前置きや見出し・箇条書きは出力しない。本文の文章のみを出力する。\n"
    "- 体言止めを避け、読み手（採用担当・エージェント）に伝わる自然な文章にする。"
)


class ResumePromptBuilderService:
    # --- プロフィール作文（全案件を根拠にする） ---

    def build_profile_system_prompt(self, kind: str) -> str:
        intro = "あなたは職務経歴書を書くプロの職務経歴ライターです。与えられた案件データだけを根拠に書きます。\n\n"
        if kind == "summary":
            return (
                intro
                + _COMMON_RULES
                + "\n- 出力は職務要約を3〜5文の1段落で。強みの技術領域・経験年数感・"
                "直近の傾向（例: AI活用）が伝わるようにする。"
            )
        if kind == "strengths":
            return (
                intro + _COMMON_RULES + "\n- 出力は自己PRの『強み』を2〜4文で。案件横断で一貫する価値を書く。"
            )
        if kind == "good_at":
            return (
                intro + _COMMON_RULES + "\n- 出力は自己PRの『得意業務』を2〜4文で。担当領域・工程の得意さを書く。"
            )
        # ai_effect
        return (
            intro
            + _COMMON_RULES
            + "\n- 出力は生成AIの活用による『効果』を1〜2文で。案件での使い方から得られた成果を書く。"
        )

    def build_profile_user_prompt(self, kind: str, engagements: list[EngagementContext]) -> str:
        lines: list[str] = ["# これまでの案件（事実）", ""]
        lines.extend(self._engagement_lines(engagements))
        asks = {
            "summary": "上記を根拠に、職務要約を3〜5文で書いてください。",
            "strengths": "上記を根拠に、自己PRの『強み』を2〜4文で書いてください。",
            "good_at": "上記を根拠に、自己PRの『得意業務』を2〜4文で書いてください。",
            "ai_effect": "上記のうちAI活用に関わる経験を根拠に、生成AI活用の『効果』を1〜2文で書いてください。",
        }
        lines.append(asks.get(kind, asks["summary"]))
        return "\n".join(lines)

    # --- 案件フィールド（単一案件を根拠にする。industry/overview/narrative） ---

    def build_engagement_system_prompt(self, kind: str = "narrative") -> str:
        base = "あなたは職務経歴書を書くプロの職務経歴ライターです。1案件の事実だけを根拠に書きます。\n\n"
        if kind == "industry":
            # 業界は短い名詞句なので、_COMMON_RULES の「文章のみ」ではなく専用ルールにする
            return (
                base
                + "# 制約（厳守）\n"
                "- 出力は業界名/事業ドメインのみ。10文字程度の簡潔な名詞句で1つだけ返す。\n"
                "- 例: 『人材・労務 SaaS』『保険（損害保険）』『EC・小売』『医療・ヘルスケア』。\n"
                "- 技術スタックや規模から推測できる範囲で。分からなければ『（業界不明）』と返す。\n"
                "- 説明文・前置き・記号・引用符は付けない。"
            )
        if kind == "overview":
            return (
                base
                + _COMMON_RULES
                + "\n- 出力はプロジェクト概要を1〜3文で。何のためのどんなシステムかが伝わるようにする。"
                "\n- 技術スタック・規模・期間から妥当に推測し、企業名は出さない。"
            )
        if kind == "responsibilities":
            return (
                base
                + _COMMON_RULES
                + "\n- 出力はその案件で『担当したこと』を2〜4文で。技術スタック・工程から妥当な担当範囲を書く。"
                "\n- 設計/実装/テスト/レビュー等、具体的な作業内容が伝わるようにする。企業名は出さない。"
            )
        if kind == "challenges":
            return (
                base
                + _COMMON_RULES
                + "\n- 出力はその案件で『苦労したこと・工夫したこと』を1〜3文で。"
                "技術的な難所と、それにどう対処/工夫したかを書く。事実から離れた誇張はしない。企業名は出さない。"
            )
        if kind == "position":
            return (
                base
                + "# 制約（厳守）\n"
                "- 出力は担当ポジション/ロールのみ。簡潔な名詞句で1つだけ返す。\n"
                "- 例: 『Backendエンジニア』『フルスタックエンジニア』『テックリード』『インフラエンジニア』。\n"
                "- 技術スタックから妥当に推測する。説明文・前置き・記号・引用符は付けない。"
            )
        # narrative（実績・取り組み）
        return (
            base
            + _COMMON_RULES
            + "\n- 出力はその案件の『実績・取り組み』を2〜4文の1段落で。"
            "課題→取り組み→成果(あれば数字)の流れで、担当した価値が伝わるようにする。"
        )

    def build_engagement_user_prompt(self, engagement: EngagementContext, kind: str = "narrative") -> str:
        lines = ["# 案件（事実）", ""]
        lines.extend(self._one_engagement_lines(engagement))
        lines.append("")
        asks = {
            "industry": "上記の技術・規模から、この案件の業界/事業ドメインを簡潔な名詞句で1つ推測してください。",
            "overview": "上記を根拠に、この案件のプロジェクト概要を1〜3文で書いてください。",
            "narrative": "上記を根拠に、この案件の『実績・取り組み』を2〜4文で書いてください。",
            "responsibilities": "上記を根拠に、この案件で『担当したこと』を2〜4文で書いてください。",
            "challenges": "上記を根拠に、この案件で『苦労したこと・工夫したこと』を1〜3文で書いてください。",
            "position": "上記の技術・工程から、担当ポジション/ロールを簡潔な名詞句で1つ推測してください。",
        }
        lines.append(asks.get(kind, asks["narrative"]))
        return "\n".join(lines)

    # --- 共通: 案件の行整形（企業名は出さない） ---

    def _engagement_lines(self, engagements: list[EngagementContext]) -> list[str]:
        if not engagements:
            return ["（案件データがありません。一般的な表現で簡潔に書いてください）", ""]
        lines: list[str] = []
        for i, eng in enumerate(engagements, start=1):
            lines.append(f"## 案件{i}")
            lines.extend(self._one_engagement_lines(eng))
            lines.append("")
        return lines

    @staticmethod
    def _one_engagement_lines(eng: EngagementContext) -> list[str]:
        lines: list[str] = []
        # 企業名は出さず業界＋規模で表現する
        if eng.industry:
            lines.append(f"- 業界: {eng.industry}")
        if eng.company_scale:
            lines.append(f"- 規模: {eng.company_scale}")
        if eng.period:
            lines.append(f"- 期間: {eng.period}")
        if eng.position:
            lines.append(f"- ポジション: {eng.position}")
        if eng.overview:
            lines.append(f"- 概要: {eng.overview}")
        if eng.responsibilities:
            lines.append(f"- 担当: {eng.responsibilities}")
        if eng.tech_stack:
            lines.append(f"- 技術: {', '.join(eng.tech_stack)}")
        for ach in eng.achievements:
            metric = f"（{ach.metric_text}）" if ach.metric_text else ""
            lines.append(f"- 成果[{ach.category_label}]: {ach.description}{metric}")
        return lines
