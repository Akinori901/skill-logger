"""優先領域の申請文を一括生成するユースケース。

指定された領域コード群を逐次生成する（レート制限に配慮）。
生成に失敗した領域はスキップし、結果に含めない。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from apps.generation.domain.exceptions import StatementSourceNotFoundError

if TYPE_CHECKING:
    from apps.careers.domain.repositories import SupportDomainRepository
    from apps.generation.domain.entities import DomainStatementEntity

    from .generate_domain_statement_usecase import GenerateDomainStatementUseCase


class GenerateAllStatementsUseCase:
    def __init__(
        self,
        single_usecase: GenerateDomainStatementUseCase,
        support_domain_repository: SupportDomainRepository,
    ) -> None:
        self._single = single_usecase
        self._domain_repo = support_domain_repository

    def execute(self, user_id: int, domain_codes: list[str]) -> list[DomainStatementEntity]:
        results: list[DomainStatementEntity] = []
        for priority, code in enumerate(domain_codes, start=1):
            try:
                statement = self._single.execute(user_id, code)
            except StatementSourceNotFoundError:
                # 紐づく案件がない領域はスキップ
                continue
            statement.priority = priority
            results.append(statement)
        return results
