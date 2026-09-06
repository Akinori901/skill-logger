"""共通認証基盤（auth-console）との連携のテスト。

移行中の判定は「中央 OR m_user_allowed_emails」。どちらかで許可されれば通す。
最も大事なのは、中央が落ちたときに全員が締め出されないこと。
"""

from __future__ import annotations

import httpx
import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache

from apps.auth_cognito.application.services.jit_provision_service import JitProvisionService
from apps.auth_cognito.domain.entities import CentralAuthzEntity, CognitoClaimsEntity
from apps.auth_cognito.domain.exceptions import UserNotAllowedError
from apps.auth_cognito.domain.repositories import CentralAuthzRepository
from apps.auth_cognito.infrastructure.models import CognitoLink, UserAllowedEmail
from apps.auth_cognito.infrastructure.repositories.central_authz_repository import (
    HttpCentralAuthzRepository,
)
from apps.auth_cognito.infrastructure.repositories.django_cognito_repositories import (
    DjangoCognitoLinkRepository,
    DjangoUserAllowedEmailRepository,
)

pytestmark = pytest.mark.django_db


class _StubCentral(CentralAuthzRepository):
    """中央の応答を差し替えるためのスタブ。"""

    def __init__(self, result: CentralAuthzEntity | None) -> None:
        self._result = result
        self.calls: list[str] = []

    def fetch(self, email: str) -> CentralAuthzEntity | None:
        self.calls.append(email)
        return self._result


def _claims(*, sub: str = "sub-1", email: str = "someone@example.com") -> CognitoClaimsEntity:
    return CognitoClaimsEntity(
        sub=sub,
        client_id="web-client",
        token_use="access",
        provider="cognito",
        email=email,
        name="Someone",
        email_verified=True,
    )


def _service(central: CentralAuthzRepository | None) -> JitProvisionService:
    return JitProvisionService(
        link_repo=DjangoCognitoLinkRepository(),
        allowed_repo=DjangoUserAllowedEmailRepository(),
        central_repo=central,
    )


class TestOrJudgement:
    """「中央 OR 既存」の判定。"""

    def test_allows_via_existing_list_without_asking_central(self) -> None:
        """既存リストにあれば中央を見ずに通す。"""
        user_model = get_user_model()
        user = user_model._default_manager.create(username="u1", email="u1@example.com")  # noqa: SLF001
        UserAllowedEmail.objects.create(user=user, email="u1@example.com")

        central = _StubCentral(CentralAuthzEntity(allowed=False))
        result = _service(central).provision(_claims(email="u1@example.com"))

        assert result.pk == user.pk
        # 既存で通るなら中央に問い合わせる必要はない
        assert central.calls == []

    def test_allows_via_existing_list_when_central_is_down(self) -> None:
        """最重要。障害時に締め出されないこと。"""
        user_model = get_user_model()
        user = user_model._default_manager.create(username="u2", email="u2@example.com")  # noqa: SLF001
        UserAllowedEmail.objects.create(user=user, email="u2@example.com")

        # None = 判断が得られなかった（中央が落ちている）
        result = _service(_StubCentral(None)).provision(_claims(email="u2@example.com"))

        assert result.pk == user.pk

    def test_denies_when_central_denies_and_not_in_existing_list(self) -> None:
        """中央が拒否し、既存リストにも無ければ拒否する。"""
        with pytest.raises(UserNotAllowedError):
            _service(_StubCentral(CentralAuthzEntity(allowed=False))).provision(
                _claims(email="stranger@example.com")
            )

    def test_denies_when_only_central_allows_because_no_user_to_link(self) -> None:
        """中央で許可されても、このサービスに利用者登録が無ければ入れない。

        誰の auth_user に紐付けるかを決められないため。中央への完全移行時に
        ここでユーザーを作る判断が要る。
        """
        with pytest.raises(UserNotAllowedError, match="登録されていません"):
            _service(_StubCentral(CentralAuthzEntity(allowed=True))).provision(
                _claims(email="central-only@example.com")
            )

    def test_falls_back_to_existing_list_when_central_not_configured(self) -> None:
        """中央未設定なら従来どおり既存リストだけで判定する。"""
        user_model = get_user_model()
        user = user_model._default_manager.create(username="u3", email="u3@example.com")  # noqa: SLF001
        UserAllowedEmail.objects.create(user=user, email="u3@example.com")

        result = _service(None).provision(_claims(email="u3@example.com"))
        assert result.pk == user.pk

        with pytest.raises(UserNotAllowedError):
            _service(None).provision(_claims(sub="s9", email="nobody@example.com"))


class TestRevocation:
    """許可の取り消しが効くこと。"""

    def test_denies_linked_user_when_permission_revoked(self) -> None:
        """リンク済みでも、許可が消えていれば拒否する。"""
        user_model = get_user_model()
        user = user_model._default_manager.create(username="u4", email="u4@example.com")  # noqa: SLF001
        CognitoLink.objects.create(
            cognito_sub="sub-linked",
            user=user,
            provider="cognito",
            cognito_email="u4@example.com",
        )

        with pytest.raises(UserNotAllowedError):
            _service(_StubCentral(CentralAuthzEntity(allowed=False))).provision(
                _claims(sub="sub-linked", email="u4@example.com")
            )


class TestHttpRepository:
    """HTTP 実装。拒否と「判断が得られなかった」を区別できること。"""

    def setup_method(self) -> None:
        cache.clear()

    def _repo(self) -> HttpCentralAuthzRepository:
        return HttpCentralAuthzRepository(base_url="https://central.example", cache_ttl=0)

    def test_reads_allowed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """許可を読み取る。"""
        def fake_get(*_args: object, **_kwargs: object) -> httpx.Response:
            return httpx.Response(200, json={"allowed": True, "role": "member", "scopes": ["a"]})

        monkeypatch.setattr(httpx, "get", fake_get)
        got = self._repo().fetch("x@example.com")

        assert got is not None
        assert got.allowed is True
        assert got.scopes == ("a",)

    def test_reads_denied(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """拒否を読み取る。"""
        monkeypatch.setattr(httpx, "get", lambda *a, **k: httpx.Response(200, json={"allowed": False}))
        got = self._repo().fetch("x@example.com")

        assert got is not None
        assert got.allowed is False

    def test_returns_none_when_unreachable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """到達できなければ None を返す。"""
        def boom(*_args: object, **_kwargs: object) -> httpx.Response:
            raise httpx.ConnectError("unreachable")

        monkeypatch.setattr(httpx, "get", boom)
        assert self._repo().fetch("x@example.com") is None

    def test_returns_none_on_server_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """中央の障害を「拒否」と解釈すると全員が締め出される。"""
        monkeypatch.setattr(httpx, "get", lambda *a, **k: httpx.Response(503))
        assert self._repo().fetch("x@example.com") is None

    def test_returns_none_on_broken_json(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """壊れた JSON は None として扱う。"""
        monkeypatch.setattr(httpx, "get", lambda *a, **k: httpx.Response(200, content=b"not json"))
        assert self._repo().fetch("x@example.com") is None

    def test_returns_none_when_url_not_set(self) -> None:
        """URL 未設定なら None。"""
        assert HttpCentralAuthzRepository(base_url="").fetch("x@example.com") is None

    def test_returns_none_when_email_empty(self) -> None:
        """email が空なら None。"""
        assert self._repo().fetch("") is None
