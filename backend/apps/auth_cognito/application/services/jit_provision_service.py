"""Cognito 認証時の Just-In-Time プロビジョニングサービス。"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.db import transaction

from apps.auth_cognito.domain.entities import CognitoLinkEntity
from apps.auth_cognito.domain.exceptions import UserNotAllowedError

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser

    from apps.auth_cognito.domain.entities import CognitoClaimsEntity, UserAllowedEmailEntity
    from apps.auth_cognito.domain.repositories import (
        CentralAuthzRepository,
        CognitoLinkRepository,
        UserAllowedEmailRepository,
    )

logger = logging.getLogger(__name__)


class JitProvisionService:
    """Cognito ログイン時に既存 auth_user と m_cognito_links を紐付ける。

    許可判定は**毎回**行う。リンク済みなら素通しにすると、一度ログインした人の
    許可を後から取り消せなくなるため。判定は「中央 OR m_user_allowed_emails」で、
    移行中はどちらかで許可されれば通す（締め出されないため）。

    解決順序:
      1. 許可判定（中央 OR `m_user_allowed_emails`）。どちらでも許可されなければ
         `UserNotAllowedError` を raise (招待制を担保)
      2. `m_cognito_links.cognito_sub` で既存リンクを検索 → ヒットすればその user を返す
      3. `m_user_allowed_emails` の user に紐付ける
         (1 つの auth_user に Cognito と Google など複数 identity を紐付け可能)

    既存ユーザーの `is_superuser` / `is_staff` は変更しない (ロックアウト回避)。
    """

    def __init__(
        self,
        link_repo: CognitoLinkRepository,
        allowed_repo: UserAllowedEmailRepository,
        central_repo: CentralAuthzRepository | None = None,
    ) -> None:
        self._link_repo = link_repo
        self._allowed_repo = allowed_repo
        # 未指定なら中央を使わず、従来どおり m_user_allowed_emails だけで判定する。
        self._central_repo = central_repo

    @transaction.atomic
    def provision(self, claims: CognitoClaimsEntity) -> AbstractBaseUser:
        user_model = get_user_model()

        if not claims.email:
            msg = "Cognito JWT に email claim がありません。管理者に問い合わせてください。"
            raise UserNotAllowedError(msg)

        allowed = self._allowed_repo.find_by_email(claims.email)
        if not self._is_allowed(claims.email, allowed):
            msg = f"email {claims.email} はログインを許可されていません。管理者に許可登録を依頼してください。"
            raise UserNotAllowedError(msg)

        # 許可を確認したうえでリンクを見る。順序が逆だと、リンク済みの人の
        # 許可を取り消しても入れてしまう。
        link = self._link_repo.find_by_sub(claims.sub)
        if link is not None:
            existing: AbstractBaseUser = user_model._default_manager.get(pk=link.user_id)  # noqa: SLF001
            return existing

        if allowed is None:
            # 中央だけが許可している状態。紐付ける先の auth_user が無いため、
            # 誰に紐付けるかを決められない。中央への完全移行時に、ここで
            # ユーザーを作る判断が要る。
            msg = (
                f"email {claims.email} は中央で許可されていますが、"
                "このサービスの利用者として登録されていません。管理者に登録を依頼してください。"
            )
            raise UserNotAllowedError(msg)

        self._link_repo.save(
            CognitoLinkEntity(
                cognito_sub=claims.sub,
                user_id=allowed.user_id,
                provider=claims.provider or "cognito",
                cognito_email=claims.email,
            )
        )
        return user_model._default_manager.get(pk=allowed.user_id)  # noqa: SLF001

    def _is_allowed(self, email: str, allowed: UserAllowedEmailEntity | None) -> bool:
        """中央 OR m_user_allowed_emails。移行中はどちらかで許可されれば通す。

        中央の判断が得られない（None）ことと、中央が拒否したことは区別する。
        混ぜると中央の障害時に全員が締め出される。
        """
        if allowed is not None:
            return True

        if self._central_repo is None:
            return False

        central = self._central_repo.fetch(email)
        return central is not None and central.allowed
