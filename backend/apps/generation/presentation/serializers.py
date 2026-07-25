"""generation Serializer。"""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.generation.domain.entities import AiConfigEntity, DomainStatementEntity


class AiConfigSerializer(serializers.Serializer[dict[str, Any]]):
    provider = serializers.ChoiceField(choices=["gemini", "claude", "openai"], default="gemini")
    api_key = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    model = serializers.CharField(max_length=100, default="gemini-2.5-flash")
    is_enabled = serializers.BooleanField(default=False)

    def to_entity(self, user_id: int) -> AiConfigEntity:
        d = self.validated_data
        return AiConfigEntity(
            user_id=user_id,
            provider=d.get("provider", "gemini"),
            api_key=d.get("api_key", ""),
            model=d.get("model", "gemini-2.5-flash"),
            is_enabled=d.get("is_enabled", False),
        )

    @staticmethod
    def entity_to_dict(entity: AiConfigEntity) -> dict[str, Any]:
        # api_key はマスクして返す（漏洩防止）。設定済みかどうかだけ分かればよい。
        return {
            "provider": entity.provider,
            "model": entity.model,
            "is_enabled": entity.is_enabled,
            "has_api_key": bool(entity.api_key),
        }


class DomainStatementSerializer(serializers.Serializer[dict[str, Any]]):
    id = serializers.IntegerField(required=False, allow_null=True)
    support_domain_id = serializers.IntegerField()
    priority = serializers.IntegerField(default=0)
    body = serializers.CharField(allow_blank=True)
    char_count = serializers.IntegerField(read_only=True)
    source_engagement_ids = serializers.ListField(child=serializers.IntegerField(), required=False, default=list)
    ai_model = serializers.CharField(required=False, allow_blank=True, default="")
    generated_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def to_entity(self, user_id: int) -> DomainStatementEntity:
        d = self.validated_data
        return DomainStatementEntity(
            id=d.get("id"),
            user_id=user_id,
            support_domain_id=d["support_domain_id"],
            priority=d.get("priority", 0),
            body=d["body"],
            char_count=len(d["body"]),
            source_engagement_ids=list(d.get("source_engagement_ids", [])),
            ai_model=d.get("ai_model", ""),
        )

    @staticmethod
    def entity_to_dict(entity: DomainStatementEntity) -> dict[str, Any]:
        return {
            "id": entity.id,
            "support_domain_id": entity.support_domain_id,
            "priority": entity.priority,
            "body": entity.body,
            "char_count": entity.char_count,
            "source_engagement_ids": entity.source_engagement_ids,
            "ai_model": entity.ai_model,
            "generated_at": entity.generated_at,
            "updated_at": entity.updated_at,
        }
