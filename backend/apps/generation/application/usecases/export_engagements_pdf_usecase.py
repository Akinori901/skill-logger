"""職務経歴書/スキルシート PDF 出力ユースケース。"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.careers.domain.repositories import EngagementRepository, UserProfileRepository
    from apps.generation.application.services.resume_pdf_service import ResumePdfService


class ExportEngagementsPdfUseCase:
    def __init__(
        self,
        engagement_repository: EngagementRepository,
        resume_pdf_service: ResumePdfService,
        user_profile_repository: UserProfileRepository | None = None,
    ) -> None:
        self._engagement_repo = engagement_repository
        self._pdf = resume_pdf_service
        self._profile_repo = user_profile_repository

    def execute(
        self,
        user_id: int,
        engagement_ids: list[int] | None = None,
        *,
        anonymize: bool = True,
        hide_name: bool = False,
        include_own: bool = False,
    ) -> bytes:
        """PDF バイト列を返す。

        include_own=False（既定）でも自社プロダクトは repo から除外しない。
        除外は案件詳細ゾーンだけの話で、スキル年数は全案件から集計するため、
        絞り込みは PDF サービス側に委ねる（ここで削ると年数まで減ってしまう）。
        """
        engagements = self._engagement_repo.find_by_user(user_id)
        if engagement_ids:
            id_set = set(engagement_ids)
            engagements = [e for e in engagements if e.id in id_set]
        profile = self._profile_repo.find_by_user(user_id) if self._profile_repo is not None else None
        return self._pdf.render_pdf(
            engagements,
            profile,
            anonymize=anonymize,
            hide_name=hide_name,
            include_own=include_own,
        )
