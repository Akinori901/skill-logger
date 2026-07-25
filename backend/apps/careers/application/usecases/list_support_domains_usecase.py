"""支援領域マスタ一覧取得ユースケース。"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.careers.domain.entities import SupportDomainEntity
    from apps.careers.domain.repositories import SupportDomainRepository


class ListSupportDomainsUseCase:
    def __init__(self, support_domain_repository: SupportDomainRepository) -> None:
        self._repository = support_domain_repository

    def execute(self) -> list[SupportDomainEntity]:
        return self._repository.list_all()
