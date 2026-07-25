"""申請文の一覧・手編集保存 View。"""

from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.request_utils import current_user_id
from apps.generation.presentation.serializers import DomainStatementSerializer
from config import container


class StatementListView(APIView):
    """GET /api/generation/statements/         一覧
    POST /api/generation/statements/        手編集保存（upsert）
    """

    def get(self, request: Request) -> Response:
        usecase = container.list_statements_usecase()
        statements = usecase.execute(current_user_id(request))
        return Response([DomainStatementSerializer.entity_to_dict(s) for s in statements])

    def post(self, request: Request) -> Response:
        serializer = DomainStatementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        entity = serializer.to_entity(user_id=current_user_id(request))
        usecase = container.save_domain_statement_usecase()
        saved = usecase.execute(entity)
        return Response(DomainStatementSerializer.entity_to_dict(saved))
