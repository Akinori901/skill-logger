"""careers Serializer。

エンティティ ⇔ JSON の変換を担う。入力（write）は DRF Serializer で
バリデーションし、出力（read）はエンティティを dict 化して返す。
"""

from __future__ import annotations

import re
from typing import Any

from rest_framework import serializers

from apps.careers.domain.entities import (
    ACHIEVEMENT_CATEGORIES,
    CONTRACT_TYPES,
    ENGAGEMENT_PHASES,
    TECH_CATEGORIES,
    AchievementEntity,
    EngagementDomainLink,
    EngagementEntity,
    EngagementUrlEntity,
    UserProfileEntity,
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
    # 種別。"repo"=公開リポ（private 案件の public への道）、""=汎用の実績URL。
    kind = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")


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
    client = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")
    agent = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")
    sier = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")
    company_size_employees = serializers.IntegerField(required=False, allow_null=True)
    dev_org_size = serializers.IntegerField(required=False, allow_null=True)
    period_start = serializers.CharField(max_length=7, required=False, allow_blank=True, default="")
    period_end = serializers.CharField(max_length=7, required=False, allow_blank=True, default="")
    position = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    overview = serializers.CharField(required=False, allow_blank=True, default="")
    responsibilities = serializers.CharField(required=False, allow_blank=True, default="")
    tech_stack = serializers.ListField(child=serializers.CharField(max_length=50), required=False, default=list)
    challenges = serializers.CharField(required=False, allow_blank=True, default="")
    phases = serializers.ListField(
        child=serializers.ChoiceField(choices=ENGAGEMENT_PHASES), required=False, default=list
    )
    contract_type = serializers.ChoiceField(
        choices=CONTRACT_TYPES, required=False, allow_blank=True, default=""
    )
    tech_categorized = serializers.DictField(
        child=serializers.ListField(child=serializers.CharField(max_length=50)),
        required=False,
        default=dict,
    )
    narrative = serializers.CharField(required=False, allow_blank=True, default="")
    # 案件レジストリ共通キー（ledger/projects.yaml の key と同一語彙）。空許可。
    project_key = serializers.CharField(max_length=50, required=False, allow_blank=True, default="")
    is_active = serializers.BooleanField(required=False, default=False)
    local_path = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")
    local_paths = serializers.ListField(
        child=serializers.CharField(max_length=500), required=False, default=list
    )
    is_public = serializers.BooleanField(required=False, default=False)
    # 自社/受託の区別。"own"/"client"/""(未分類)。is_public(匿名化制御)とは別概念。
    engagement_type = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")
    display_order = serializers.IntegerField(required=False, default=0)
    achievements = AchievementSerializer(many=True, required=False, default=list)
    urls = EngagementUrlSerializer(many=True, required=False, default=list)
    domain_links = EngagementDomainLinkSerializer(many=True, required=False, default=list)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def validate_tech_categorized(self, value: dict[str, list[str]]) -> dict[str, list[str]]:
        """技術種別のキーは TECH_CATEGORIES のみ許可する。"""
        unknown = set(value) - set(TECH_CATEGORIES)
        if unknown:
            raise serializers.ValidationError(
                f"未知の技術種別です: {', '.join(sorted(unknown))}（許可: {', '.join(TECH_CATEGORIES)}）"
            )
        return value

    def validate_project_key(self, value: str) -> str:
        """案件レジストリキーは ledger/projects.yaml の key 語彙（[a-z0-9_]）に合わせる。空は許可。"""
        if value and not re.fullmatch(r"[a-z0-9_]+", value):
            raise serializers.ValidationError(
                "project_key は英小文字・数字・アンダースコアのみ使用できます（例: my_project）。"
            )
        return value

    def to_entity(self, user_id: int) -> EngagementEntity:
        """バリデーション済み data → EngagementEntity。"""
        d = self.validated_data
        return EngagementEntity(
            id=d.get("id"),
            user_id=user_id,
            title=d["title"],
            industry=d.get("industry", ""),
            company_name=d.get("company_name", ""),
            client=d.get("client", ""),
            agent=d.get("agent", ""),
            sier=d.get("sier", ""),
            company_size_employees=d.get("company_size_employees"),
            dev_org_size=d.get("dev_org_size"),
            period_start=d.get("period_start", ""),
            period_end=d.get("period_end", ""),
            position=d.get("position", ""),
            overview=d.get("overview", ""),
            responsibilities=d.get("responsibilities", ""),
            tech_stack=list(d.get("tech_stack", [])),
            challenges=d.get("challenges", ""),
            phases=list(d.get("phases", [])),
            contract_type=d.get("contract_type", ""),
            tech_categorized={k: list(v) for k, v in d.get("tech_categorized", {}).items()},
            narrative=d.get("narrative", ""),
            project_key=d.get("project_key", ""),
            is_active=d.get("is_active", False),
            local_path=d.get("local_path", ""),
            local_paths=list(d.get("local_paths", [])),
            is_public=d.get("is_public", False),
            engagement_type=d.get("engagement_type", ""),
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
                EngagementUrlEntity(
                    id=u.get("id"), url=u["url"], label=u.get("label", ""), kind=u.get("kind", "")
                )
                for u in d.get("urls", [])
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
            "client": entity.client,
            "agent": entity.agent,
            "sier": entity.sier,
            "company_size_employees": entity.company_size_employees,
            "dev_org_size": entity.dev_org_size,
            "period_start": entity.period_start,
            "period_end": entity.period_end,
            "position": entity.position,
            "overview": entity.overview,
            "responsibilities": entity.responsibilities,
            "tech_stack": entity.tech_stack,
            "challenges": entity.challenges,
            "phases": entity.phases,
            "contract_type": entity.contract_type,
            "tech_categorized": entity.tech_categorized,
            "narrative": entity.narrative,
            "project_key": entity.project_key,
            "is_active": entity.is_active,
            "local_path": entity.local_path,
            "local_paths": entity.local_paths,
            "is_public": entity.is_public,
            "engagement_type": entity.engagement_type,
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
            "urls": [{"id": u.id, "url": u.url, "label": u.label, "kind": u.kind} for u in entity.urls],
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


class AiUsageItemSerializer(serializers.Serializer[dict[str, Any]]):
    """生成AI活用の1項目（ツール/組み込み方/効果）。"""

    tool = serializers.CharField(max_length=100, allow_blank=True, default="")
    how = serializers.CharField(allow_blank=True, default="")
    effect = serializers.CharField(allow_blank=True, default="")


class UserProfileSerializer(serializers.Serializer[dict[str, Any]]):
    """職務経歴書サマリの read/write 共用 Serializer。"""

    display_name = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    age_range = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")
    residence = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    headline = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")
    summary = serializers.CharField(required=False, allow_blank=True, default="")
    strengths = serializers.CharField(required=False, allow_blank=True, default="")
    good_at = serializers.CharField(required=False, allow_blank=True, default="")
    ai_usage = AiUsageItemSerializer(many=True, required=False, default=list)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def to_entity(self, user_id: int) -> UserProfileEntity:
        d = self.validated_data
        return UserProfileEntity(
            user_id=user_id,
            display_name=d.get("display_name", ""),
            age_range=d.get("age_range", ""),
            residence=d.get("residence", ""),
            headline=d.get("headline", ""),
            summary=d.get("summary", ""),
            strengths=d.get("strengths", ""),
            good_at=d.get("good_at", ""),
            ai_usage=[
                {"tool": u.get("tool", ""), "how": u.get("how", ""), "effect": u.get("effect", "")}
                for u in d.get("ai_usage", [])
            ],
        )

    @staticmethod
    def entity_to_dict(entity: UserProfileEntity) -> dict[str, Any]:
        return {
            "display_name": entity.display_name,
            "age_range": entity.age_range,
            "residence": entity.residence,
            "headline": entity.headline,
            "summary": entity.summary,
            "strengths": entity.strengths,
            "good_at": entity.good_at,
            "ai_usage": entity.ai_usage,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
        }
