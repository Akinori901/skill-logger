"""案件削除ユースケース。"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.careers.domain.repositories import EngagementRepository


class DeleteEngagementUseCase:
    def __init__(self, engagement_repository: EngagementRepository) -> None:
        self._repository = engagement_repository

    def execute(self, engagement_id: int, user_id: int) -> None:
        self._repository.delete(engagement_id, user_id)
