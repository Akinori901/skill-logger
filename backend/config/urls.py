from django.conf import settings
from django.urls import include, path

from apps.core.views import UserDetailsView

urlpatterns = [
    # 認証済みユーザー情報取得（MVP は仮認証で固定ユーザーを返す）
    path("api/auth/user/", UserDetailsView.as_view(), name="user_details"),
    path("api/", include("apps.careers.presentation.urls")),
    path("api/", include("apps.generation.presentation.urls")),
]

# Django admin はローカル開発(DEBUG)時のみ有効化する。
# 本番(DEBUG=False)では admin ルート自体をマウントせず、外部露出を防ぐ。
if settings.DEBUG:
    from django.contrib import admin

    urlpatterns.insert(0, path("admin/", admin.site.urls))
