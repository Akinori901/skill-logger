from django.contrib import admin
from django.urls import include, path

from apps.core.views import UserDetailsView

urlpatterns = [
    path("admin/", admin.site.urls),
    # 認証済みユーザー情報取得（MVP は仮認証で固定ユーザーを返す）
    path("api/auth/user/", UserDetailsView.as_view(), name="user_details"),
    path("api/", include("apps.careers.presentation.urls")),
    path("api/", include("apps.generation.presentation.urls")),
]
