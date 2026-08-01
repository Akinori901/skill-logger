"""テスト環境設定"""

from .base import *  # noqa: F401, F403

DEBUG = True

# テスト用DB: SQLite をインメモリで動かし高速化する（本番と同じ SQLite エンジン）。
DATABASES["default"]["TEST"] = {"NAME": ":memory:"}  # noqa: F405

# テスト高速化: パスワードハッシュを軽量化
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
