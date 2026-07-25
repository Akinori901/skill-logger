"""案件詳細取得ユースケース。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from apps.careers.domain.exceptions import EngagementNotFoundError

if TYPE_CHECKING:
    from apps.careers.domain.entities import EngagementEntity
    from apps.careers.domain.repositories import EngagementRepository


class GetEngagementUseCase:
    def __init__(self, engagement_repository: EngagementRepository) -> None:
        self._repository = engagement_repository

    def execute(self, engagement_id: int, user_id: int) -> EngagementEntity:
        entity = self._repository.find_by_id(engagement_id, user_id)
        if entity is None:
            raise EngagementNotFoundError(f"案件が見つかりません: id={engagement_id}")
        return entity
