"""本番環境設定（Lambda + RDS）"""

from .base import *  # noqa: F401, F403

DEBUG = False

# --- Database (EFS 上の SQLite) ---
# データ量が小さく実質単一ユーザーのため RDS ではなく EFS 上の SQLite を使う。
# Lambda 環境変数 SQLITE_PATH に EFS マウント先のパス(/mnt/efs/db.sqlite3)を渡す。
# 書き込み競合対策: API Lambda は reserved_concurrent_executions=1 で直列化しているが、
# 保険として busy_timeout も設定する（EFS/NFS 上では WAL より rollback journal が無難）。
DATABASES = {  # noqa: F405
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": env("SQLITE_PATH", default="/mnt/efs/db.sqlite3"),  # noqa: F405
        "OPTIONS": {
            "timeout": 20,
            "init_command": "PRAGMA busy_timeout=20000;",
        },
    }
}

# --- Cache (DB-backed cache for Lambda) ---
CACHES = {  # noqa: F405
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "django_cache",
        "TIMEOUT": 1800,  # 30分
        "OPTIONS": {
            "MAX_ENTRIES": 200,
        },
    }
}

# CORS: CloudFront 経由のためワイルドカード許可
CORS_ALLOW_ALL_ORIGINS = True

# セキュリティ設定
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# 静的ファイル（Lambda環境ではS3等を使用）
STATIC_URL = env("STATIC_URL", default="/static/")  # noqa: F405
