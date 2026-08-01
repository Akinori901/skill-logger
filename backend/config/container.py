"""DI Container — 依存関係の解決を一元管理するファクトリ関数群。

全てのファクトリ関数はローカルインポートを使用し、循環参照を回避する。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.auth_cognito.application.services.cognito_jwt_verifier_service import CognitoJwtVerifierService
    from apps.auth_cognito.application.services.jit_provision_service import JitProvisionService
    from apps.auth_cognito.application.services.jwks_cache_service import JwksCacheService
    from apps.auth_cognito.infrastructure.repositories.django_cognito_repositories import (
        DjangoCognitoLinkRepository,
        DjangoUserAllowedEmailRepository,
    )
    from apps.careers.application.usecases.delete_engagement_usecase import DeleteEngagementUseCase
    from apps.careers.application.usecases.get_engagement_usecase import GetEngagementUseCase
    from apps.careers.application.usecases.get_user_profile_usecase import GetUserProfileUseCase
    from apps.careers.application.usecases.import_from_inventory_usecase import ImportFromInventoryUseCase
    from apps.careers.application.usecases.list_engagements_usecase import ListEngagementsUseCase
    from apps.careers.application.usecases.list_support_domains_usecase import ListSupportDomainsUseCase
    from apps.careers.application.usecases.save_engagement_usecase import SaveEngagementUseCase
    from apps.careers.application.usecases.save_user_profile_usecase import SaveUserProfileUseCase
    from apps.careers.infrastructure.repositories.django_engagement_repository import DjangoEngagementRepository
    from apps.careers.infrastructure.repositories.django_support_domain_repository import (
        DjangoSupportDomainRepository,
    )
    from apps.careers.infrastructure.repositories.django_user_profile_repository import (
        DjangoUserProfileRepository,
    )
    from apps.generation.application.services.markdown_export_service import MarkdownExportService
    from apps.generation.application.services.resume_pdf_service import ResumePdfService
    from apps.generation.application.usecases.export_engagements_markdown_usecase import (
        ExportEngagementsMarkdownUseCase,
    )
    from apps.generation.application.usecases.export_engagements_pdf_usecase import (
        ExportEngagementsPdfUseCase,
    )
    from apps.generation.application.usecases.generate_all_statements_usecase import GenerateAllStatementsUseCase
    from apps.generation.application.usecases.generate_domain_statement_usecase import (
        GenerateDomainStatementUseCase,
    )
    from apps.generation.application.usecases.generate_engagement_field_usecase import (
        GenerateEngagementFieldUseCase,
    )
    from apps.generation.application.usecases.generate_engagement_narrative_usecase import (
        GenerateEngagementNarrativeUseCase,
    )
    from apps.generation.application.usecases.generate_profile_narrative_usecase import (
        GenerateProfileNarrativeUseCase,
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


def _user_profile_repository() -> DjangoUserProfileRepository:
    from apps.careers.infrastructure.repositories.django_user_profile_repository import (
        DjangoUserProfileRepository,
    )

    return DjangoUserProfileRepository()


def careers_get_user_profile_usecase() -> GetUserProfileUseCase:
    from apps.careers.application.usecases.get_user_profile_usecase import GetUserProfileUseCase

    return GetUserProfileUseCase(user_profile_repository=_user_profile_repository())


def careers_save_user_profile_usecase() -> SaveUserProfileUseCase:
    from apps.careers.application.usecases.save_user_profile_usecase import SaveUserProfileUseCase

    return SaveUserProfileUseCase(user_profile_repository=_user_profile_repository())


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


def resume_pdf_service() -> ResumePdfService:
    from apps.generation.application.services.resume_pdf_service import ResumePdfService

    return ResumePdfService()


def export_engagements_pdf_usecase() -> ExportEngagementsPdfUseCase:
    from apps.generation.application.usecases.export_engagements_pdf_usecase import (
        ExportEngagementsPdfUseCase,
    )

    return ExportEngagementsPdfUseCase(
        engagement_repository=_engagement_repository(),
        resume_pdf_service=resume_pdf_service(),
        user_profile_repository=_user_profile_repository(),
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


def generate_profile_narrative_usecase() -> GenerateProfileNarrativeUseCase:
    from apps.generation.application.usecases.generate_profile_narrative_usecase import (
        GenerateProfileNarrativeUseCase,
    )

    return GenerateProfileNarrativeUseCase(
        engagement_repository=_engagement_repository(),
        user_profile_repository=_user_profile_repository(),
        ai_config_repository=_ai_config_repository(),
        generation_log_repository=_ai_generation_log_repository(),
    )


def generate_engagement_narrative_usecase() -> GenerateEngagementNarrativeUseCase:
    from apps.generation.application.usecases.generate_engagement_narrative_usecase import (
        GenerateEngagementNarrativeUseCase,
    )

    return GenerateEngagementNarrativeUseCase(
        engagement_repository=_engagement_repository(),
        ai_config_repository=_ai_config_repository(),
        generation_log_repository=_ai_generation_log_repository(),
    )


def generate_engagement_field_usecase() -> GenerateEngagementFieldUseCase:
    from apps.generation.application.usecases.generate_engagement_field_usecase import (
        GenerateEngagementFieldUseCase,
    )

    return GenerateEngagementFieldUseCase(
        engagement_repository=_engagement_repository(),
        ai_config_repository=_ai_config_repository(),
        generation_log_repository=_ai_generation_log_repository(),
    )


def list_statements_usecase() -> ListStatementsUseCase:
    from apps.generation.application.usecases.list_statements_usecase import ListStatementsUseCase

    return ListStatementsUseCase(statement_repository=_statement_repository())


def save_domain_statement_usecase() -> SaveDomainStatementUseCase:
    from apps.generation.application.usecases.save_domain_statement_usecase import SaveDomainStatementUseCase

    return SaveDomainStatementUseCase(statement_repository=_statement_repository())


# ============================================================
# Cognito OAuth 認証 (apps.auth_cognito)
# ============================================================
#
# 認証に必要な最小構成のみ移植（JWT検証 + JIT + allowed_email 照合）。
# 招待制の admin UI 系（boto3 UserPool 操作）は移植していない。


def cognito_link_repository() -> DjangoCognitoLinkRepository:
    from apps.auth_cognito.infrastructure.repositories.django_cognito_repositories import (
        DjangoCognitoLinkRepository,
    )

    return DjangoCognitoLinkRepository()


def user_allowed_email_repository() -> DjangoUserAllowedEmailRepository:
    from apps.auth_cognito.infrastructure.repositories.django_cognito_repositories import (
        DjangoUserAllowedEmailRepository,
    )

    return DjangoUserAllowedEmailRepository()


def cognito_jwks_cache_service() -> JwksCacheService:
    from django.conf import settings

    from apps.auth_cognito.application.services.jwks_cache_service import JwksCacheService

    return JwksCacheService(jwks_url=settings.COGNITO_JWKS_URL)


def cognito_jwt_verifier_service() -> CognitoJwtVerifierService:
    from django.conf import settings

    from apps.auth_cognito.application.services.cognito_jwt_verifier_service import (
        CognitoJwtVerifierService,
    )

    return CognitoJwtVerifierService(
        jwks_cache=cognito_jwks_cache_service(),
        issuer=settings.COGNITO_JWT_ISSUER,
        allowed_client_ids=settings.COGNITO_ALLOWED_CLIENT_IDS,
    )


def jit_provision_service() -> JitProvisionService:
    from apps.auth_cognito.application.services.jit_provision_service import JitProvisionService

    return JitProvisionService(
        link_repo=cognito_link_repository(),
        allowed_repo=user_allowed_email_repository(),
    )
