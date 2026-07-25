"""案件保存ユースケース（新規作成・更新の両方）。"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.careers.domain.entities import EngagementEntity
    from apps.careers.domain.repositories import EngagementRepository


class SaveEngagementUseCase:
    """案件＋成果＋URL＋領域リンクを一括保存する。

    Repository.save が @transaction.atomic で子テーブルを再構築する。
    """

    def __init__(self, engagement_repository: EngagementRepository) -> None:
        self._repository = engagement_repository

    def execute(self, entity: EngagementEntity) -> EngagementEntity:
        return self._repository.save(entity)
