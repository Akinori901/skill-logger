"""支援領域マスタ View。"""

from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.careers.presentation.serializers import SupportDomainSerializer
from config import container


class SupportDomainListView(APIView):
    """GET /api/careers/support-domains/  支援領域マスタ一覧"""

    def get(self, request: Request) -> Response:
        usecase = container.careers_list_support_domains_usecase()
        entities = usecase.execute()
        data = [
            SupportDomainSerializer({"id": e.id, "code": e.code, "name": e.name, "display_order": e.display_order}).data
            for e in entities
        ]
        return Response(data)
