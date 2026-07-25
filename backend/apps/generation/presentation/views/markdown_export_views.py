"""棚卸しMarkdown出力 View。"""

from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.request_utils import current_user_id
from config import container


class MarkdownExportView(APIView):
    """GET /api/generation/engagements/markdown/?ids=1,2,3  棚卸しMarkdown出力"""

    def get(self, request: Request) -> Response:
        ids_param = request.query_params.get("ids", "")
        engagement_ids = [int(x) for x in ids_param.split(",") if x.strip().isdigit()] or None
        usecase = container.export_engagements_markdown_usecase()
        markdown = usecase.execute(current_user_id(request), engagement_ids)
        return Response({"markdown": markdown})
