"""AI設定リポジトリ ORM 実装。"""

from __future__ import annotations

from apps.generation.domain.entities import AiConfigEntity
from apps.generation.domain.repositories import AiConfigRepository
from apps.generation.infrastructure.models import AiConfig


class DjangoAiConfigRepository(AiConfigRepository):
    def find_by_user(self, user_id: int) -> AiConfigEntity | None:
        row = AiConfig.objects.filter(user_id=user_id).first()
        return self._to_entity(row) if row is not None else None

    def save(self, entity: AiConfigEntity) -> AiConfigEntity:
        row, _ = AiConfig.objects.update_or_create(
            user_id=entity.user_id,
            defaults={
                "provider": entity.provider,
                "api_key": entity.api_key,
                "model": entity.model,
                "is_enabled": entity.is_enabled,
            },
        )
        return self._to_entity(row)

    @staticmethod
    def _to_entity(row: AiConfig) -> AiConfigEntity:
        return AiConfigEntity(
            id=row.id,
            user_id=row.user_id,
            provider=row.provider,
            api_key=row.api_key,
            model=row.model,
            is_enabled=row.is_enabled,
        )
