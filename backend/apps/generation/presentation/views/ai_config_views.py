"""AI設定 View。"""

from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.request_utils import current_user_id
from apps.generation.presentation.serializers import AiConfigSerializer
from config import container


class AiConfigView(APIView):
    """GET /api/generation/ai-config/   現在の設定（api_key はマスク）
    PUT /api/generation/ai-config/   設定保存
    """

    def get(self, request: Request) -> Response:
        usecase = container.get_ai_config_usecase()
        entity = usecase.execute(current_user_id(request))
        return Response(AiConfigSerializer.entity_to_dict(entity))

    def put(self, request: Request) -> Response:
        serializer = AiConfigSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        entity = serializer.to_entity(user_id=current_user_id(request))
        usecase = container.save_ai_config_usecase()
        saved = usecase.execute(entity)
        return Response(AiConfigSerializer.entity_to_dict(saved))
