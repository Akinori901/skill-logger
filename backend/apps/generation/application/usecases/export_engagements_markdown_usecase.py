"""棚卸しMarkdown出力ユースケース。"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.careers.domain.repositories import EngagementRepository
    from apps.generation.application.services.markdown_export_service import MarkdownExportService


class ExportEngagementsMarkdownUseCase:
    def __init__(
        self,
        engagement_repository: EngagementRepository,
        markdown_export_service: MarkdownExportService,
    ) -> None:
        self._engagement_repo = engagement_repository
        self._md = markdown_export_service

    def execute(self, user_id: int, engagement_ids: list[int] | None = None) -> str:
        engagements = self._engagement_repo.find_by_user(user_id)
        if engagement_ids:
            id_set = set(engagement_ids)
            engagements = [e for e in engagements if e.id in id_set]
        return self._md.render(engagements)
