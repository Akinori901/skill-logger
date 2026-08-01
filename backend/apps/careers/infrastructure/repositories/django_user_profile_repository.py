"""ユーザープロフィールリポジトリ ORM 実装。"""

from __future__ import annotations

from apps.careers.domain.entities import UserProfileEntity
from apps.careers.domain.repositories import UserProfileRepository
from apps.careers.infrastructure.models import UserProfile


class DjangoUserProfileRepository(UserProfileRepository):
    def find_by_user(self, user_id: int) -> UserProfileEntity | None:
        row = UserProfile.objects.filter(user_id=user_id).first()
        return self._to_entity(row) if row is not None else None

    def save(self, entity: UserProfileEntity) -> UserProfileEntity:
        row, _ = UserProfile.objects.update_or_create(
            user_id=entity.user_id,
            defaults={
                "display_name": entity.display_name,
                "age_range": entity.age_range,
                "residence": entity.residence,
                "headline": entity.headline,
                "summary": entity.summary,
                "strengths": entity.strengths,
                "good_at": entity.good_at,
                "ai_usage": entity.ai_usage,
            },
        )
        return self._to_entity(row)

    @staticmethod
    def _to_entity(row: UserProfile) -> UserProfileEntity:
        return UserProfileEntity(
            id=row.id,
            user_id=row.user_id,
            display_name=row.display_name,
            age_range=row.age_range,
            residence=row.residence,
            headline=row.headline,
            summary=row.summary,
            strengths=row.strengths,
            good_at=row.good_at,
            ai_usage=list(row.ai_usage or []),
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
