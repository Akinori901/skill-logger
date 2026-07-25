"""棚卸しMarkdown出力サービス（外部依存ゼロの純粋関数）。

蓄積した案件エンティティを、ユーザー提示フォーマットの Markdown に整形する。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.careers.domain.entities import EngagementEntity

_CATEGORY_LABELS = {
    "speed": "速度改善",
    "cost": "コスト削減",
    "quality": "品質向上",
    "ops": "運用改善",
    "incident": "障害削減",
    "release": "リリース改善",
    "review": "レビュー体制改善",
}


class MarkdownExportService:
    def render(self, engagements: list[EngagementEntity]) -> str:
        blocks = [self._render_one(e) for e in engagements]
        return "\n\n---\n\n".join(blocks)

    def _render_one(self, e: EngagementEntity) -> str:
        lines: list[str] = []
        industry = f"（{e.industry}）" if e.industry else ""
        lines.append(f"# {e.title}{industry}")
        lines.append("")

        if e.industry:
            lines.append(f"■ 業界\n{e.industry}\n")

        scale = self._company_scale(e)
        if scale:
            lines.append(f"■ 会社規模\n{scale}\n")

        period = self._period(e)
        if period:
            lines.append(f"■ 期間\n{period}\n")

        if e.position:
            lines.append(f"■ ポジション\n{e.position}\n")

        if e.overview:
            lines.append(f"■ プロジェクト概要\n{e.overview}\n")

        if e.responsibilities:
            lines.append(f"■ 担当したこと\n{e.responsibilities}\n")

        if e.tech_stack:
            tech = "\n".join(e.tech_stack)
            lines.append(f"■ 技術\n{tech}\n")

        if e.challenges:
            lines.append(f"■ 苦労したこと・工夫したこと\n{e.challenges}\n")

        if e.achievements:
            lines.append("■ 成果")
            for a in e.achievements:
                label = _CATEGORY_LABELS.get(a.category, a.category)
                metric = self._metric_text(a)
                metric_suffix = f"（{metric}）" if metric else ""
                lines.append(f"・[{label}] {a.description}{metric_suffix}")
            lines.append("")

        if e.urls:
            lines.append("■ 実績URL")
            for u in e.urls:
                label = f"{u.label}: " if u.label else ""
                lines.append(f"・{label}{u.url}")
            lines.append("")

        return "\n".join(lines).rstrip()

    @staticmethod
    def _company_scale(e: EngagementEntity) -> str:
        parts = []
        if e.company_size_employees is not None:
            parts.append(f"従業員：約{e.company_size_employees}名")
        if e.dev_org_size is not None:
            parts.append(f"開発組織：約{e.dev_org_size}名")
        return "\n".join(parts)

    @staticmethod
    def _period(e: EngagementEntity) -> str:
        if not e.period_start:
            return ""
        end = e.period_end or "現在"
        return f"{e.period_start}〜{end}"

    @staticmethod
    def _metric_text(a: object) -> str:
        before = getattr(a, "metric_before", None)
        after = getattr(a, "metric_after", None)
        unit = getattr(a, "metric_unit", "") or ""
        delta = getattr(a, "metric_delta_pct", None)
        if before is None and after is None:
            return ""
        text = ""
        if before is not None and after is not None:
            text = f"{_num(before)}{unit} → {_num(after)}{unit}"
        elif after is not None:
            text = f"{_num(after)}{unit}"
        if delta is not None:
            text = f"{text}（{_num(delta)}%）" if text else f"{_num(delta)}%改善"
        return text


def _num(value: object) -> str:
    """Decimal の末尾ゼロを落として文字列化する。"""
    s = str(value)
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s
