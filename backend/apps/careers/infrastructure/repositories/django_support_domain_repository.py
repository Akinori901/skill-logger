"""支援領域マスタ リポジトリ ORM 実装。"""

from __future__ import annotations

from apps.careers.domain.entities import SupportDomainEntity
from apps.careers.domain.repositories import SupportDomainRepository
from apps.careers.infrastructure.models import SupportDomain


class DjangoSupportDomainRepository(SupportDomainRepository):
    def list_all(self) -> list[SupportDomainEntity]:
        return [self._to_entity(row) for row in SupportDomain.objects.all()]

    def find_by_code(self, code: str) -> SupportDomainEntity | None:
        row = SupportDomain.objects.filter(code=code).first()
        return self._to_entity(row) if row is not None else None

    @staticmethod
    def _to_entity(row: SupportDomain) -> SupportDomainEntity:
        return SupportDomainEntity(
            id=row.id,
            code=row.code,
            name=row.name,
            display_order=row.display_order,
        )
