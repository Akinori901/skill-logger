"""DI Container — 依存関係の解決を一元管理するファクトリ関数群。

全てのファクトリ関数はローカルインポートを使用し、循環参照を回避する。
（fair-value-calculator/backend/config/container.py と同じ方式）
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.careers.application.usecases.delete_engagement_usecase import DeleteEngagementUseCase
    from apps.careers.application.usecases.get_engagement_usecase import GetEngagementUseCase
    from apps.careers.application.usecases.import_from_inventory_usecase import ImportFromInventoryUseCase
    from apps.careers.application.usecases.list_engagements_usecase import ListEngagementsUseCase
    from apps.careers.application.usecases.list_support_domains_usecase import ListSupportDomainsUseCase
    from apps.careers.application.usecases.save_engagement_usecase import SaveEngagementUseCase
    from apps.careers.infrastructure.repositories.django_engagement_repository import DjangoEngagementRepository
    from apps.careers.infrastructure.repositories.django_support_domain_repository import (
        DjangoSupportDomainRepository,
    )
    from apps.generation.application.services.markdown_export_service import MarkdownExportService
    from apps.generation.application.usecases.export_engagements_markdown_usecase import (
        ExportEngagementsMarkdownUseCase,
    )
    from apps.generation.application.usecases.generate_all_statements_usecase import GenerateAllStatementsUseCase
    from apps.generation.application.usecases.generate_domain_statement_usecase import (
        GenerateDomainStatementUseCase,
    )
    from apps.generation.application.usecases.get_ai_config_usecase import GetAiConfigUseCase
    from apps.generation.application.usecases.list_statements_usecase import ListStatementsUseCase
    from apps.generation.application.usecases.save_ai_config_usecase import SaveAiConfigUseCase
    from apps.generation.application.usecases.save_domain_statement_usecase import SaveDomainStatementUseCase
    from apps.generation.infrastructure.repositories.django_ai_config_repository import DjangoAiConfigRepository
    from apps.generation.infrastructure.repositories.django_ai_generation_log_repository import (
        DjangoAiGenerationLogRepository,
    )
    from apps.generation.infrastructure.repositories.django_statement_repository import DjangoStatementRepository


# ============================================================
# careers
# ============================================================


def _engagement_repository() -> DjangoEngagementRepository:
    from apps.careers.infrastructure.repositories.django_engagement_repository import DjangoEngagementRepository

    return DjangoEngagementRepository()


def _support_domain_repository() -> DjangoSupportDomainRepository:
    from apps.careers.infrastructure.repositories.django_support_domain_repository import (
        DjangoSupportDomainRepository,
    )

    return DjangoSupportDomainRepository()


def careers_save_engagement_usecase() -> SaveEngagementUseCase:
    from apps.careers.application.usecases.save_engagement_usecase import SaveEngagementUseCase

    return SaveEngagementUseCase(engagement_repository=_engagement_repository())


def careers_list_engagements_usecase() -> ListEngagementsUseCase:
    from apps.careers.application.usecases.list_engagements_usecase import ListEngagementsUseCase

    return ListEngagementsUseCase(engagement_repository=_engagement_repository())


def careers_get_engagement_usecase() -> GetEngagementUseCase:
    from apps.careers.application.usecases.get_engagement_usecase import GetEngagementUseCase

    return GetEngagementUseCase(engagement_repository=_engagement_repository())


def careers_delete_engagement_usecase() -> DeleteEngagementUseCase:
    from apps.careers.application.usecases.delete_engagement_usecase import DeleteEngagementUseCase

    return DeleteEngagementUseCase(engagement_repository=_engagement_repository())


def careers_list_support_domains_usecase() -> ListSupportDomainsUseCase:
    from apps.careers.application.usecases.list_support_domains_usecase import ListSupportDomainsUseCase

    return ListSupportDomainsUseCase(support_domain_repository=_support_domain_repository())


def careers_import_from_inventory_usecase() -> ImportFromInventoryUseCase:
    from apps.careers.application.usecases.import_from_inventory_usecase import ImportFromInventoryUseCase

    return ImportFromInventoryUseCase(engagement_repository=_engagement_repository())


# ============================================================
# generation
# ============================================================


def _ai_config_repository() -> DjangoAiConfigRepository:
    from apps.generation.infrastructure.repositories.django_ai_config_repository import DjangoAiConfigRepository

    return DjangoAiConfigRepository()


def _statement_repository() -> DjangoStatementRepository:
    from apps.generation.infrastructure.repositories.django_statement_repository import DjangoStatementRepository

    return DjangoStatementRepository()


def _ai_generation_log_repository() -> DjangoAiGenerationLogRepository:
    from apps.generation.infrastructure.repositories.django_ai_generation_log_repository import (
        DjangoAiGenerationLogRepository,
    )

    return DjangoAiGenerationLogRepository()


def markdown_export_service() -> MarkdownExportService:
    from apps.generation.application.services.markdown_export_service import MarkdownExportService

    return MarkdownExportService()


def get_ai_config_usecase() -> GetAiConfigUseCase:
    from apps.generation.application.usecases.get_ai_config_usecase import GetAiConfigUseCase

    return GetAiConfigUseCase(ai_config_repository=_ai_config_repository())


def save_ai_config_usecase() -> SaveAiConfigUseCase:
    from apps.generation.application.usecases.save_ai_config_usecase import SaveAiConfigUseCase

    return SaveAiConfigUseCase(ai_config_repository=_ai_config_repository())


def export_engagements_markdown_usecase() -> ExportEngagementsMarkdownUseCase:
    from apps.generation.application.usecases.export_engagements_markdown_usecase import (
        ExportEngagementsMarkdownUseCase,
    )

    return ExportEngagementsMarkdownUseCase(
        engagement_repository=_engagement_repository(),
        markdown_export_service=markdown_export_service(),
    )


def generate_domain_statement_usecase() -> GenerateDomainStatementUseCase:
    from apps.generation.application.usecases.generate_domain_statement_usecase import (
        GenerateDomainStatementUseCase,
    )

    return GenerateDomainStatementUseCase(
        engagement_repository=_engagement_repository(),
        support_domain_repository=_support_domain_repository(),
        ai_config_repository=_ai_config_repository(),
        statement_repository=_statement_repository(),
        generation_log_repository=_ai_generation_log_repository(),
    )


def generate_all_statements_usecase() -> GenerateAllStatementsUseCase:
    from apps.generation.application.usecases.generate_all_statements_usecase import GenerateAllStatementsUseCase

    return GenerateAllStatementsUseCase(
        single_usecase=generate_domain_statement_usecase(),
        support_domain_repository=_support_domain_repository(),
    )


def list_statements_usecase() -> ListStatementsUseCase:
    from apps.generation.application.usecases.list_statements_usecase import ListStatementsUseCase

    return ListStatementsUseCase(statement_repository=_statement_repository())


def save_domain_statement_usecase() -> SaveDomainStatementUseCase:
    from apps.generation.application.usecases.save_domain_statement_usecase import SaveDomainStatementUseCase

    return SaveDomainStatementUseCase(statement_repository=_statement_repository())
