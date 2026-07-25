"""MVP 用の仮認証。

このプロジェクトは単一ユーザー運用の MVP としてスタートするため、認証は
`settings.DEV_FIXED_USER_ID` の Django ユーザーを常に request.user に固定する
だけの軽量な仕組みにしている。

Phase B（共通 Cognito 化）で、fair-value-calculator の
`apps.auth_cognito.presentation.drf_authentication.CognitoJWTAuthentication`
に差し替える。差し替え時はこのファイルと settings の
DEFAULT_AUTHENTICATION_CLASSES を除去するだけでよい。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication

if TYPE_CHECKING:
    from django.contrib.auth.models import User
    from rest_framework.request import Request

UserModel = get_user_model()


class DevFixedUserAuthentication(BaseAuthentication):
    """常に settings.DEV_FIXED_USER_ID のユーザーで認証済みとみなす仮認証。"""

    def authenticate(self, request: Request) -> tuple[User, None] | None:
        user_id = getattr(settings, "DEV_FIXED_USER_ID", 1)
        user = UserModel.objects.filter(pk=user_id).first()
        if user is None:
            # seed 未実行時などはフォールバックで先頭ユーザーを使う
            user = UserModel.objects.order_by("pk").first()
        if user is None:
            return None
        return (user, None)
