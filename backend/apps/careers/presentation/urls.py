"""careers URL ルーティング。"""

from django.urls import path

from apps.careers.presentation.views.engagement_views import EngagementDetailView, EngagementListView
from apps.careers.presentation.views.import_views import ImportInventoryView
from apps.careers.presentation.views.support_domain_views import SupportDomainListView

urlpatterns = [
    path("careers/engagements/", EngagementListView.as_view(), name="engagement_list"),
    path("careers/engagements/<int:engagement_id>/", EngagementDetailView.as_view(), name="engagement_detail"),
    path("careers/support-domains/", SupportDomainListView.as_view(), name="support_domain_list"),
    path("careers/import/", ImportInventoryView.as_view(), name="import_inventory"),
]
