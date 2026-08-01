"""職務経歴書/スキルシート PDF 出力 View。"""

from __future__ import annotations

from urllib.parse import quote

from django.http import HttpResponse
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.core.request_utils import current_user_id
from config import container


class PdfExportView(APIView):
    """GET /api/generation/engagements/pdf/?ids=1,2,3

    職務経歴書＋スキルシートを 1 つの PDF にまとめてダウンロードする。
    ids 省略時は当該ユーザーの全案件を対象にする。
    """

    def get(self, request: Request) -> HttpResponse:
        ids_param = request.query_params.get("ids", "")
        engagement_ids = [int(x) for x in ids_param.split(",") if x.strip().isdigit()] or None
        # anonymize は既定 True。明示的に "false" のときだけ企業名を出す。
        anonymize = request.query_params.get("anonymize", "true").lower() != "false"

        usecase = container.export_engagements_pdf_usecase()
        pdf_bytes = usecase.execute(current_user_id(request), engagement_ids, anonymize=anonymize)

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        # 日本語ファイル名は RFC 5987 の filename*（UTF-8 パーセントエンコード）で渡す。
        # 非対応クライアント向けに ASCII の filename もフォールバックで併記する。
        filename = "スキルシート.pdf"
        response["Content-Disposition"] = (
            f"attachment; filename=\"skill-sheet.pdf\"; filename*=UTF-8''{quote(filename)}"
        )
        return response
