"""申請文リポジトリ ORM 実装。"""

from __future__ import annotations

from apps.generation.domain.entities import DomainStatementEntity
from apps.generation.domain.repositories import DomainStatementRepository
from apps.generation.infrastructure.models import DomainStatement


class DjangoStatementRepository(DomainStatementRepository):
    def find_by_user(self, user_id: int) -> list[DomainStatementEntity]:
        rows = DomainStatement.objects.filter(user_id=user_id)
        return [self._to_entity(r) for r in rows]

    def save(self, entity: DomainStatementEntity) -> DomainStatementEntity:
        row, _ = DomainStatement.objects.update_or_create(
            user_id=entity.user_id,
            support_domain_id=entity.support_domain_id,
            defaults={
                "priority": entity.priority,
                "body": entity.body,
                "char_count": entity.char_count,
                "source_engagement_ids": entity.source_engagement_ids,
                "ai_model": entity.ai_model,
            },
        )
        return self._to_entity(row)

    @staticmethod
    def _to_entity(row: DomainStatement) -> DomainStatementEntity:
        return DomainStatementEntity(
            id=row.id,
            user_id=row.user_id,
            support_domain_id=row.support_domain_id,
            priority=row.priority,
            body=row.body,
            char_count=row.char_count,
            source_engagement_ids=list(row.source_engagement_ids or []),
            ai_model=row.ai_model,
            generated_at=row.generated_at,
            updated_at=row.updated_at,
        )
