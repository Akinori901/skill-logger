"""View 共通のリクエストユーティリティ。"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rest_framework.request import Request


def current_user_id(request: Request) -> int:
    """認証済みユーザーの ID を int で返す。

    IsAuthenticated 済みの View から呼ぶ前提。request.user.pk の型が
    Optional のため、mypy strict 対策と実行時保証を兼ねてここで確定する。
    """
    pk = request.user.pk
    if pk is None:
        raise PermissionError("認証されていません")
    return int(pk)
