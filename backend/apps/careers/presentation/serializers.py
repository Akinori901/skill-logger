"""careers Serializer。

エンティティ ⇔ JSON の変換を担う。入力（write）は DRF Serializer で
バリデーションし、出力（read）はエンティティを dict 化して返す。
"""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.careers.domain.entities import (
    ACHIEVEMENT_CATEGORIES,
    AchievementEntity,
    EngagementDomainLink,
    EngagementEntity,
    EngagementUrlEntity,
)


class AchievementSerializer(serializers.Serializer[dict[str, Any]]):
    id = serializers.IntegerField(required=False, allow_null=True)
    category = serializers.ChoiceField(choices=ACHIEVEMENT_CATEGORIES)
    description = serializers.CharField(max_length=500)
    metric_before = serializers.DecimalField(max_digits=15, decimal_places=2, required=False, allow_null=True)
    metric_after = serializers.DecimalField(max_digits=15, decimal_places=2, required=False, allow_null=True)
    metric_unit = serializers.CharField(max_length=30, required=False, allow_blank=True, default="")
    metric_delta_pct = serializers.DecimalField(max_digits=6, decimal_places=2, required=False, allow_null=True)


class EngagementUrlSerializer(serializers.Serializer[dict[str, Any]]):
    id = serializers.IntegerField(required=False, allow_null=True)
    url = serializers.URLField(max_length=500)
    # `label` は Serializer 基底の表示ラベル属性(str | None)と名前が衝突するため
    # mypy が型不整合を報告する（django-stubs の制約）。API フィールド名は維持する。
    label = serializers.CharField(  # type: ignore[assignment]
        max_length=100, required=False, allow_blank=True, default=""
    )


class EngagementDomainLinkSerializer(serializers.Serializer[dict[str, Any]]):
    id = serializers.IntegerField(required=False, allow_null=True)
    support_domain_id = serializers.IntegerField()
    relevance = serializers.IntegerField(min_value=1, max_value=5, default=3)


class EngagementSerializer(serializers.Serializer[dict[str, Any]]):
    """案件の read/write 共用 Serializer。"""

    id = serializers.IntegerField(required=False, allow_null=True)
    title = serializers.CharField(max_length=200)
    industry = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    company_name = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")
    company_size_employees = serializers.IntegerField(required=False, allow_null=True)
    dev_org_size = serializers.IntegerField(required=False, allow_null=True)
    period_start = serializers.CharField(max_length=7, required=False, allow_blank=True, default="")
    period_end = serializers.CharField(max_length=7, required=False, allow_blank=True, default="")
    position = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    overview = serializers.CharField(required=False, allow_blank=True, default="")
    responsibilities = serializers.CharField(required=False, allow_blank=True, default="")
    tech_stack = serializers.ListField(child=serializers.CharField(max_length=50), required=False, default=list)
    challenges = serializers.CharField(required=False, allow_blank=True, default="")
    is_public = serializers.BooleanField(required=False, default=False)
    display_order = serializers.IntegerField(required=False, default=0)
    achievements = AchievementSerializer(many=True, required=False, default=list)
    urls = EngagementUrlSerializer(many=True, required=False, default=list)
    domain_links = EngagementDomainLinkSerializer(many=True, required=False, default=list)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def to_entity(self, user_id: int) -> EngagementEntity:
        """バリデーション済み data → EngagementEntity。"""
        d = self.validated_data
        return EngagementEntity(
            id=d.get("id"),
            user_id=user_id,
            title=d["title"],
            industry=d.get("industry", ""),
            company_name=d.get("company_name", ""),
            company_size_employees=d.get("company_size_employees"),
            dev_org_size=d.get("dev_org_size"),
            period_start=d.get("period_start", ""),
            period_end=d.get("period_end", ""),
            position=d.get("position", ""),
            overview=d.get("overview", ""),
            responsibilities=d.get("responsibilities", ""),
            tech_stack=list(d.get("tech_stack", [])),
            challenges=d.get("challenges", ""),
            is_public=d.get("is_public", False),
            display_order=d.get("display_order", 0),
            achievements=[
                AchievementEntity(
                    id=a.get("id"),
                    category=a["category"],
                    description=a["description"],
                    metric_before=a.get("metric_before"),
                    metric_after=a.get("metric_after"),
                    metric_unit=a.get("metric_unit", ""),
                    metric_delta_pct=a.get("metric_delta_pct"),
                )
                for a in d.get("achievements", [])
            ],
            urls=[
                EngagementUrlEntity(id=u.get("id"), url=u["url"], label=u.get("label", "")) for u in d.get("urls", [])
            ],
            domain_links=[
                EngagementDomainLink(
                    id=link.get("id"),
                    support_domain_id=link["support_domain_id"],
                    relevance=link.get("relevance", 3),
                )
                for link in d.get("domain_links", [])
            ],
        )

    @staticmethod
    def entity_to_dict(entity: EngagementEntity) -> dict[str, Any]:
        return {
            "id": entity.id,
            "title": entity.title,
            "industry": entity.industry,
            "company_name": entity.company_name,
            "company_size_employees": entity.company_size_employees,
            "dev_org_size": entity.dev_org_size,
            "period_start": entity.period_start,
            "period_end": entity.period_end,
            "position": entity.position,
            "overview": entity.overview,
            "responsibilities": entity.responsibilities,
            "tech_stack": entity.tech_stack,
            "challenges": entity.challenges,
            "is_public": entity.is_public,
            "display_order": entity.display_order,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
            "achievements": [
                {
                    "id": a.id,
                    "category": a.category,
                    "description": a.description,
                    "metric_before": a.metric_before,
                    "metric_after": a.metric_after,
                    "metric_unit": a.metric_unit,
                    "metric_delta_pct": a.metric_delta_pct,
                }
                for a in entity.achievements
            ],
            "urls": [{"id": u.id, "url": u.url, "label": u.label} for u in entity.urls],
            "domain_links": [
                {"id": link.id, "support_domain_id": link.support_domain_id, "relevance": link.relevance}
                for link in entity.domain_links
            ],
        }


class SupportDomainSerializer(serializers.Serializer[dict[str, Any]]):
    id = serializers.IntegerField()
    code = serializers.CharField()
    name = serializers.CharField()
    display_order = serializers.IntegerField()
