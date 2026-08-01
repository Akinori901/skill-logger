"""共通 View モジュール。

`UserDetailsView` はフロントエンドが現在のユーザー情報を取得するために叩く。
認証は CognitoJWTAuthentication が適用され、Cognito JIT で解決された
Django User がそのまま返る。
"""

from __future__ import annotations

from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated


class _UserDetailsSerializer(serializers.ModelSerializer[User]):
    """`/api/auth/user/` のレスポンス serializer。"""

    class Meta:
        model = User
        fields = ("pk", "username", "email", "first_name", "last_name", "is_superuser")
        read_only_fields = fields


class UserDetailsView(RetrieveAPIView[User]):
    """`GET /api/auth/user/` — 認証済みユーザーの情報を返す。"""

    permission_classes = (IsAuthenticated,)
    serializer_class = _UserDetailsSerializer

    def get_object(self) -> User:
        return self.request.user  # type: ignore[return-value]
