"""案件リポジトリ ORM 実装。

案件本体＋子（成果・URL・領域リンク）を一括保存する。子テーブルは
save 時に全削除→再作成する（goals の member_links 再構築パターン）。
"""

from __future__ import annotations

from django.db import transaction

from apps.careers.domain.entities import (
    AchievementEntity,
    EngagementDomainLink,
    EngagementEntity,
    EngagementUrlEntity,
)
from apps.careers.domain.exceptions import EngagementNotFoundError
from apps.careers.domain.repositories import EngagementRepository
from apps.careers.infrastructure.models import (
    Achievement,
    Engagement,
    EngagementDomain,
    EngagementUrl,
)


class DjangoEngagementRepository(EngagementRepository):
    def find_by_user(self, user_id: int) -> list[EngagementEntity]:
        rows = Engagement.objects.filter(user_id=user_id).prefetch_related("achievements", "urls", "domain_links").all()
        # 案件は「終了年月(period_end)の降順 = 新しい順」で返す。
        # period_end は "YYYY-MM" 文字列。空("")は「現在も継続中」なので最新扱いで先頭に置く。
        # PDF/一覧とも本メソッドの取得順をそのまま使うため、並び順はここに一元化する。
        rows = sorted(
            rows,
            key=lambda r: (r.period_end or "9999-99", r.period_start or ""),
            reverse=True,
        )
        return [self._to_entity(row) for row in rows]

    def find_by_id(self, engagement_id: int, user_id: int) -> EngagementEntity | None:
        row = (
            Engagement.objects.filter(id=engagement_id, user_id=user_id)
            .prefetch_related("achievements", "urls", "domain_links")
            .first()
        )
        return self._to_entity(row) if row is not None else None

    def find_by_domain(self, user_id: int, support_domain_id: int) -> list[EngagementEntity]:
        links = (
            EngagementDomain.objects.filter(
                support_domain_id=support_domain_id,
                engagement__user_id=user_id,
            )
            .select_related("engagement")
            .prefetch_related(
                "engagement__achievements",
                "engagement__urls",
                "engagement__domain_links",
            )
            .order_by("-relevance")
        )
        return [self._to_entity(link.engagement) for link in links]

    @transaction.atomic
    def save(self, entity: EngagementEntity) -> EngagementEntity:
        if entity.id is not None:
            row = Engagement.objects.filter(id=entity.id, user_id=entity.user_id).first()
            if row is None:
                raise EngagementNotFoundError(f"案件が見つかりません: id={entity.id}")
        else:
            row = Engagement(user_id=entity.user_id)

        row.title = entity.title
        row.industry = entity.industry
        row.company_name = entity.company_name
        row.company_size_employees = entity.company_size_employees
        row.dev_org_size = entity.dev_org_size
        row.period_start = entity.period_start
        row.period_end = entity.period_end
        row.position = entity.position
        row.overview = entity.overview
        row.responsibilities = entity.responsibilities
        row.tech_stack = entity.tech_stack
        row.challenges = entity.challenges
        row.phases = entity.phases
        row.contract_type = entity.contract_type
        row.tech_categorized = entity.tech_categorized
        row.tech_weights = entity.tech_weights
        row.manual_skills = entity.manual_skills
        row.tech_versions = entity.tech_versions
        row.architecture = entity.architecture
        row.narrative = entity.narrative
        row.is_public = entity.is_public
        row.display_order = entity.display_order
        row.save()

        # 子テーブルを再構築（全削除→再作成）
        row.achievements.all().delete()
        Achievement.objects.bulk_create(
            [
                Achievement(
                    engagement=row,
                    category=a.category,
                    description=a.description,
                    metric_before=a.metric_before,
                    metric_after=a.metric_after,
                    metric_unit=a.metric_unit,
                    metric_delta_pct=a.metric_delta_pct,
                )
                for a in entity.achievements
            ]
        )

        row.urls.all().delete()
        EngagementUrl.objects.bulk_create(
            [EngagementUrl(engagement=row, url=u.url, label=u.label) for u in entity.urls]
        )

        row.domain_links.all().delete()
        EngagementDomain.objects.bulk_create(
            [
                EngagementDomain(
                    engagement=row,
                    support_domain_id=link.support_domain_id,
                    relevance=link.relevance,
                )
                for link in entity.domain_links
            ]
        )

        refreshed = Engagement.objects.prefetch_related("achievements", "urls", "domain_links").get(id=row.id)
        return self._to_entity(refreshed)

    def delete(self, engagement_id: int, user_id: int) -> None:
        Engagement.objects.filter(id=engagement_id, user_id=user_id).delete()

    @staticmethod
    def _to_entity(row: Engagement) -> EngagementEntity:
        return EngagementEntity(
            id=row.id,
            user_id=row.user_id,
            title=row.title,
            industry=row.industry,
            company_name=row.company_name,
            company_size_employees=row.company_size_employees,
            dev_org_size=row.dev_org_size,
            period_start=row.period_start,
            period_end=row.period_end,
            position=row.position,
            overview=row.overview,
            responsibilities=row.responsibilities,
            tech_stack=list(row.tech_stack or []),
            challenges=row.challenges,
            phases=list(row.phases or []),
            contract_type=row.contract_type,
            tech_categorized=dict(row.tech_categorized or {}),
            tech_weights=dict(row.tech_weights or {}),
            manual_skills=dict(row.manual_skills or {}),
            tech_versions=dict(row.tech_versions or {}),
            architecture=dict(row.architecture or {}),
            narrative=row.narrative,
            is_public=row.is_public,
            display_order=row.display_order,
            created_at=row.created_at,
            updated_at=row.updated_at,
            achievements=[
                AchievementEntity(
                    id=a.id,
                    category=a.category,
                    description=a.description,
                    metric_before=a.metric_before,
                    metric_after=a.metric_after,
                    metric_unit=a.metric_unit,
                    metric_delta_pct=a.metric_delta_pct,
                )
                for a in row.achievements.all()
            ],
            urls=[EngagementUrlEntity(id=u.id, url=u.url, label=u.label) for u in row.urls.all()],
            domain_links=[
                EngagementDomainLink(
                    id=link.id,
                    support_domain_id=link.support_domain_id,
                    relevance=link.relevance,
                )
                for link in row.domain_links.all()
            ],
        )
