"""棚卸しデータ取り込み View（ブラウザからの feed アップロード）。

skill-inventory の skilllogger-feed/v1（JSON）を受け取り、案件を取り込む。
dry_run=true でプレビュー（保存せず対象を返す）。
"""

from __future__ import annotations

from typing import Any

from rest_framework import status
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.request_utils import current_user_id
from config import container


class ImportInventoryView(APIView):
    """POST /api/careers/import/  feed を取り込む

    受け取り方は2通り:
      - JSON body に feed をそのまま（{"feed": {...}, "only_decision": "...", "dry_run": true}）
      - multipart で file=feed.json をアップロード（フォームフィールド only_decision / dry_run 併用可）
    """

    parser_classes = [JSONParser, MultiPartParser]

    def post(self, request: Request) -> Response:
        feed, only_decision, dry_run = self._extract(request)
        if feed is None:
            return Response(
                {"detail": "feed が指定されていません（JSON body の feed か multipart の file）"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not isinstance(feed, dict) or feed.get("schema", "").split("/")[0] != "skilllogger-feed":
            return Response(
                {"detail": "schema が skilllogger-feed ではありません"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        usecase = container.careers_import_from_inventory_usecase()
        result = usecase.execute(
            current_user_id(request),
            feed,
            only_decision=only_decision or None,
            dry_run=dry_run,
        )
        return Response(result.as_dict())

    @staticmethod
    def _extract(request: Request) -> tuple[dict[str, Any] | None, str, bool]:
        # multipart（ファイルアップロード）
        if request.FILES.get("file"):
            import json

            try:
                feed = json.load(request.FILES["file"])
            except (ValueError, UnicodeDecodeError):
                feed = None
            only = request.data.get("only_decision", "")
            dry = str(request.data.get("dry_run", "")).lower() in ("1", "true", "yes")
            return feed, only, dry

        # JSON body
        feed = request.data.get("feed")
        only = request.data.get("only_decision", "")
        dry = bool(request.data.get("dry_run", False))
        return feed, only, dry
