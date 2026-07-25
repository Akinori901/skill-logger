"""棚卸し（業務経歴）ドメインエンティティ。

Django ORM / DRF に依存しない純粋なデータ構造（クリーンアーキの domain 層規約）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime
    from decimal import Decimal


# 成果カテゴリ（Expert 申請の成果軸）
ACHIEVEMENT_CATEGORIES = (
    "speed",  # 速度改善
    "cost",  # コスト削減
    "quality",  # 品質向上
    "ops",  # 運用改善
    "incident",  # 障害削減
    "release",  # リリース改善
    "review",  # レビュー体制改善
)


@dataclass
class AchievementEntity:
    """成果（数字付き構造）。

    metric_before/after/unit を持つことで、生成文に定量値を差し込める。
    """

    category: str  # ACHIEVEMENT_CATEGORIES のいずれか
    description: str
    metric_before: Decimal | None = None
    metric_after: Decimal | None = None
    metric_unit: str = ""
    metric_delta_pct: Decimal | None = None
    id: int | None = None


@dataclass
class EngagementUrlEntity:
    """実績URL。"""

    url: str
    label: str = ""
    id: int | None = None


@dataclass
class EngagementDomainLink:
    """案件と支援領域の紐付け（寄与度つき）。"""

    support_domain_id: int
    relevance: int = 3  # 1-5、その領域への寄与度
    id: int | None = None


@dataclass
class EngagementEntity:
    """案件（棚卸しの主エンティティ）。"""

    user_id: int
    title: str
    industry: str = ""
    company_name: str = ""
    company_size_employees: int | None = None
    dev_org_size: int | None = None
    period_start: str = ""  # YYYY-MM
    period_end: str = ""  # YYYY-MM（空=現在）
    position: str = ""
    overview: str = ""
    responsibilities: str = ""
    tech_stack: list[str] = field(default_factory=list)
    challenges: str = ""
    is_public: bool = False  # 匿名化制御（public 出力時に企業名を伏せるか）
    display_order: int = 0
    achievements: list[AchievementEntity] = field(default_factory=list)
    urls: list[EngagementUrlEntity] = field(default_factory=list)
    domain_links: list[EngagementDomainLink] = field(default_factory=list)
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class SupportDomainEntity:
    """支援領域マスタ（Expert 申請の12領域）。"""

    code: str
    name: str
    display_order: int = 0
    id: int | None = None
