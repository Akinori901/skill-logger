"""AI 生成 DTO。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AchievementContext:
    """プロンプトに渡す成果（数字付き）。"""

    category_label: str
    description: str
    metric_text: str = ""  # 例: "40時間 → 20時間（50%改善）"


@dataclass
class EngagementContext:
    """プロンプトに渡す1案件分のコンテキスト。"""

    company_name: str
    industry: str
    company_scale: str  # 例: "従業員300名 / 開発30名"
    period: str
    position: str
    overview: str
    responsibilities: str
    tech_stack: list[str] = field(default_factory=list)
    achievements: list[AchievementContext] = field(default_factory=list)
    engagement_id: int | None = None


@dataclass
class DomainContext:
    """1支援領域の生成コンテキスト。"""

    domain_code: str
    domain_name: str
    engagements: list[EngagementContext] = field(default_factory=list)
