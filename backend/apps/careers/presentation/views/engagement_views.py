"""案件 CRUD View。

View → container.factory() → UseCase の配線。ドメイン例外を HTTP ステータスに変換する。
"""

from __future__ import annotations

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.careers.domain.exceptions import EngagementNotFoundError
from apps.careers.presentation.serializers import EngagementSerializer
from apps.core.request_utils import current_user_id
from config import container


class EngagementListView(APIView):
    """GET /api/careers/engagements/  一覧
    POST /api/careers/engagements/  新規作成
    """

    def get(self, request: Request) -> Response:
        usecase = container.careers_list_engagements_usecase()
        entities = usecase.execute(user_id=current_user_id(request))
        data = [EngagementSerializer.entity_to_dict(e) for e in entities]
        return Response(data)

    def post(self, request: Request) -> Response:
        serializer = EngagementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        entity = serializer.to_entity(user_id=current_user_id(request))
        entity.id = None  # POST は必ず新規
        usecase = container.careers_save_engagement_usecase()
        saved = usecase.execute(entity)
        return Response(EngagementSerializer.entity_to_dict(saved), status=status.HTTP_201_CREATED)


class EngagementDetailView(APIView):
    """GET/PUT/DELETE /api/careers/engagements/<id>/"""

    def get(self, request: Request, engagement_id: int) -> Response:
        try:
            usecase = container.careers_get_engagement_usecase()
            entity = usecase.execute(engagement_id, user_id=current_user_id(request))
        except EngagementNotFoundError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(EngagementSerializer.entity_to_dict(entity))

    def put(self, request: Request, engagement_id: int) -> Response:
        serializer = EngagementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        entity = serializer.to_entity(user_id=current_user_id(request))
        entity.id = engagement_id
        try:
            usecase = container.careers_save_engagement_usecase()
            saved = usecase.execute(entity)
        except EngagementNotFoundError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(EngagementSerializer.entity_to_dict(saved))

    def delete(self, request: Request, engagement_id: int) -> Response:
        usecase = container.careers_delete_engagement_usecase()
        usecase.execute(engagement_id, user_id=current_user_id(request))
        return Response(status=status.HTTP_204_NO_CONTENT)
