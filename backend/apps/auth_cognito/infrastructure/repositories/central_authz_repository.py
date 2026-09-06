"""共通認証基盤（qol-auth-console）への認可問い合わせ実装。"""

from __future__ import annotations

import logging

import httpx
from django.core.cache import cache

from apps.auth_cognito.domain.entities import CentralAuthzEntity
from apps.auth_cognito.domain.repositories import CentralAuthzRepository

logger = logging.getLogger(__name__)

# このアプリを中央がどう呼んでいるか。中央の設定画面のキーと一致させる。
_APP_KEY = "skilllogger"
_CACHE_PREFIX = "central_authz_v1"


class HttpCentralAuthzRepository(CentralAuthzRepository):
    """中央に HTTP で問い合わせる。

    認証は全リクエストで走るため結果をキャッシュする。権限変更の反映は
    最大 TTL 分遅れるが、遅れるのは「開放」の方向で締め出しではない。
    """

    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 3.0,
        cache_ttl: int = 60,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._cache_ttl = cache_ttl

    def fetch(self, email: str) -> CentralAuthzEntity | None:
        if not self._base_url or not email:
            return None

        key = f"{_CACHE_PREFIX}:{email.lower()}"
        cached = cache.get(key)
        if cached is not None:
            # 「判断が得られなかった」もキャッシュする（中央が落ちている間、
            # 毎リクエストでタイムアウトを待たされないため）。
            return cached if isinstance(cached, CentralAuthzEntity) else None

        result = self._request(email)
        cache.set(key, result if result is not None else False, self._cache_ttl)
        return result

    def _request(self, email: str) -> CentralAuthzEntity | None:
        try:
            res = httpx.get(
                f"{self._base_url}/api/authz",
                params={"email": email.lower(), "app": _APP_KEY},
                timeout=self._timeout,
            )
        except httpx.HTTPError:
            logger.warning("中央への問い合わせに失敗しました", exc_info=True)
            return None

        if res.status_code != httpx.codes.OK:
            # 5xx を「拒否」と解釈すると障害が締め出しに化ける。
            logger.warning("中央が %s を返しました", res.status_code)
            return None

        try:
            body = res.json()
        except ValueError:
            logger.warning("中央の応答を JSON として読めませんでした", exc_info=True)
            return None

        scopes = body.get("scopes")
        return CentralAuthzEntity(
            allowed=body.get("allowed") is True,
            role=body.get("role") or "member",
            scopes=tuple(s for s in scopes if isinstance(s, str)) if isinstance(scopes, list) else (),
        )
