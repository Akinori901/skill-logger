"""棚卸しドメイン例外。"""

from __future__ import annotations

from apps.core.exceptions import DomainError, EntityNotFoundError


class EngagementNotFoundError(EntityNotFoundError):
    """案件が見つからない。"""


class InvalidEngagementError(DomainError):
    """案件の入力が不正。"""


class SupportDomainNotFoundError(EntityNotFoundError):
    """支援領域が見つからない。"""
