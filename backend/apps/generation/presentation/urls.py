"""generation URL ルーティング。"""

from django.urls import path

from apps.generation.presentation.views.ai_config_views import AiConfigView
from apps.generation.presentation.views.generate_views import (
    GenerateAllStatementsView,
    GenerateDomainStatementView,
    GenerateEngagementFieldView,
    GenerateEngagementNarrativeView,
    GenerateProfileNarrativeView,
)
from apps.generation.presentation.views.markdown_export_views import MarkdownExportView
from apps.generation.presentation.views.pdf_export_views import PdfExportView
from apps.generation.presentation.views.statement_views import StatementListView

urlpatterns = [
    path("generation/ai-config/", AiConfigView.as_view(), name="ai_config"),
    path(
        "generation/domains/<str:domain_code>/statement/",
        GenerateDomainStatementView.as_view(),
        name="generate_domain_statement",
    ),
    path(
        "generation/statements/generate-all/",
        GenerateAllStatementsView.as_view(),
        name="generate_all_statements",
    ),
    path("generation/statements/", StatementListView.as_view(), name="statement_list"),
    path(
        "generation/engagements/markdown/",
        MarkdownExportView.as_view(),
        name="markdown_export",
    ),
    path(
        "generation/engagements/pdf/",
        PdfExportView.as_view(),
        name="pdf_export",
    ),
    path(
        "generation/profile/narrative/",
        GenerateProfileNarrativeView.as_view(),
        name="generate_profile_narrative",
    ),
    path(
        "generation/engagements/<int:engagement_id>/narrative/",
        GenerateEngagementNarrativeView.as_view(),
        name="generate_engagement_narrative",
    ),
    path(
        "generation/engagements/<int:engagement_id>/field/",
        GenerateEngagementFieldView.as_view(),
        name="generate_engagement_field",
    ),
]
