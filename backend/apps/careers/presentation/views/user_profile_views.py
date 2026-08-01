"""ユーザープロフィール View（職務経歴書サマリ）。"""

from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.careers.presentation.serializers import UserProfileSerializer
from apps.core.request_utils import current_user_id
from config import container


class UserProfileView(APIView):
    """GET /api/careers/profile/   現在のプロフィール（未登録なら空既定）
    PUT /api/careers/profile/   プロフィール保存（update_or_create）
    """

    def get(self, request: Request) -> Response:
        usecase = container.careers_get_user_profile_usecase()
        entity = usecase.execute(current_user_id(request))
        return Response(UserProfileSerializer.entity_to_dict(entity))

    def put(self, request: Request) -> Response:
        serializer = UserProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        entity = serializer.to_entity(user_id=current_user_id(request))
        usecase = container.careers_save_user_profile_usecase()
        saved = usecase.execute(entity)
        return Response(UserProfileSerializer.entity_to_dict(saved))
