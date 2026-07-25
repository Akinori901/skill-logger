"""申請文生成プロンプト構築サービス（外部依存ゼロの純粋ロジック）。

Expert 申請の各支援領域について、蓄積した案件コンテキストから
「50〜200字・在籍企業名・具体ステップ・定量成果(数字)入り」の
申請文を生成させるためのプロンプトを組み立てる。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.generation.application.dto import DomainContext


class StatementPromptBuilderService:
    def build_system_prompt(self) -> str:
        return (
            "あなたはIT人材紹介の「Expert審査」に通す申請文を書くプロの職務経歴ライターです。\n"
            "与えられた案件データだけを根拠に、マッチング精度を最大化する申請文を書きます。\n"
            "\n"
            "# 制約（厳守）\n"
            "- 出力は1つの支援領域についての申請文を1段落のみ。前置きや見出し・箇条書きは出力しない。\n"
            "- 文字数は50〜200字。\n"
            "- 「どんな企業に → どんなステップで支援し → どんな成果(数字)を出せるか」の順で書く。\n"
            "- 在籍/支援先の企業規模や具体的な数字（成果）を必ず織り込む。"
            "企業名は伏せて『◯◯業のSaaS企業』等の表現でよい。\n"
            "- 提供データにない事実の捏造・誇張は禁止。数字は提供された成果の範囲でのみ使う。\n"
            "- 体言止めを避け、自然な文章にする。"
        )

    def build_user_prompt(self, context: DomainContext) -> str:
        lines: list[str] = [f"# 支援領域: {context.domain_name}", ""]
        if not context.engagements:
            lines.append("（この領域に紐づく案件データはありません。一般的な表現で簡潔に書いてください）")
        for i, eng in enumerate(context.engagements, start=1):
            lines.append(f"## 案件{i}")
            if eng.company_name:
                lines.append(f"- 企業: {eng.company_name}（{eng.industry}）")
            elif eng.industry:
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
            lines.append("")
        lines.append(
            f"上記を根拠に、「{context.domain_name}」で発揮できるバリューを50〜200字の申請文で1つ書いてください。"
        )
        return "\n".join(lines)
