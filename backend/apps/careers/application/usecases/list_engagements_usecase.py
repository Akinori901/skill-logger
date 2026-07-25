"""案件一覧取得ユースケース。"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.careers.domain.entities import EngagementEntity
    from apps.careers.domain.repositories import EngagementRepository


class ListEngagementsUseCase:
    def __init__(self, engagement_repository: EngagementRepository) -> None:
        self._repository = engagement_repository

    def execute(self, user_id: int) -> list[EngagementEntity]:
        return self._repository.find_by_user(user_id)
