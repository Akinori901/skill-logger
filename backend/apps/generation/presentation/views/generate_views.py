"""申請文生成 View。

ドメイン例外を HTTP ステータスに変換する:
  AiConfigNotFoundError -> 402
  AiRateLimitExceededError -> 429
  StatementSourceNotFoundError -> 400
  AiApiKeyInvalidError -> 400
"""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.request_utils import current_user_id
from apps.generation.domain.exceptions import (
    AiApiKeyInvalidError,
    AiConfigNotFoundError,
    AiRateLimitExceededError,
    StatementSourceNotFoundError,
)
from apps.generation.presentation.serializers import DomainStatementSerializer
from config import container


def _handle_generation_errors[T: Callable[..., Response]](fn: T) -> T:
    """生成系の共通例外→HTTP 変換デコレータ。"""

    @wraps(fn)
    def wrapper(self: APIView, request: Request, *args: Any, **kwargs: Any) -> Response:
        try:
            return fn(self, request, *args, **kwargs)
        except AiConfigNotFoundError as e:
            return Response({"detail": str(e)}, status=status.HTTP_402_PAYMENT_REQUIRED)
        except AiRateLimitExceededError as e:
            return Response({"detail": str(e)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except (StatementSourceNotFoundError, AiApiKeyInvalidError) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except (TimeoutError, RuntimeError) as e:
            return Response({"detail": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    return wrapper  # type: ignore[return-value]


class GenerateDomainStatementView(APIView):
    """POST /api/generation/domains/<code>/statement/  単一領域の申請文生成"""

    @_handle_generation_errors
    def post(self, request: Request, domain_code: str) -> Response:
        persist = bool(request.data.get("persist", False))
        usecase = container.generate_domain_statement_usecase()
        statement = usecase.execute(current_user_id(request), domain_code, persist=persist)
        return Response(DomainStatementSerializer.entity_to_dict(statement))


class GenerateAllStatementsView(APIView):
    """POST /api/generation/statements/generate-all/  優先領域を一括生成

    body: { "domain_codes": ["modernization", "in_house_dev", ...] }（優先順）
    """

    @_handle_generation_errors
    def post(self, request: Request) -> Response:
        domain_codes = request.data.get("domain_codes", [])
        usecase = container.generate_all_statements_usecase()
        statements = usecase.execute(current_user_id(request), domain_codes)
        return Response([DomainStatementSerializer.entity_to_dict(s) for s in statements])
