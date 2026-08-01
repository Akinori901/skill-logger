"""Django 共通設定"""

import os
from pathlib import Path

import environ

# backend/ ディレクトリ
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# django-environ で .env 読み込み
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
)
env_file = BASE_DIR.parent / ".env"
if env_file.exists():
    environ.Env.read_env(env_file)

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# --- Application definition ---

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party
    "rest_framework",
    "corsheaders",
    # Local apps
    "apps.core",
    "apps.auth_cognito",
    "apps.careers",
    "apps.generation",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# --- Database ---
# 本番(Lambda+EFS)・開発・テストすべて SQLite に統一する。
# データ量が小さく実質単一ユーザーのため RDS/MySQL は使わない（コスト最適化）。
# 保存先は SQLITE_PATH で上書き可（本番は EFS 上の /mnt/efs/db.sqlite3）。

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": env("SQLITE_PATH", default=str(BASE_DIR / "db.sqlite3")),
        "OPTIONS": {
            "timeout": 20,
            "init_command": "PRAGMA busy_timeout=20000;",
        },
    }
}

# --- Password validation ---

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Internationalization ---

LANGUAGE_CODE = "ja"
TIME_ZONE = "Asia/Tokyo"
USE_I18N = True
USE_TZ = True

# --- Static files ---

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# --- Default primary key field type ---

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Django REST Framework ---
#
# 認証方針:
#   共通 Cognito 認証（qol-user-pool）。CognitoJWTAuthentication が
#   `Authorization: Bearer <cognito_jwt>` を検証し、JIT プロビジョニングで
#   m_user_allowed_emails に許可登録済みのユーザーだけ通す（招待制）。
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.auth_cognito.presentation.drf_authentication.CognitoJWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DATETIME_FORMAT": "%Y-%m-%dT%H:%M:%S%z",
    "DATE_FORMAT": "%Y-%m-%d",
}

# --- Cognito (OAuth) ---
# 共通 Cognito 基盤 qol-user-pool の値。本番/ローカルとも env 経由で注入する。
# 未設定時（default=""）は CognitoJWTAuthentication が常に None を返し全 API が 401。
COGNITO_USER_POOL_ID = env("COGNITO_USER_POOL_ID", default="")
COGNITO_REGION = env("COGNITO_REGION", default="ap-northeast-1")
COGNITO_WEB_CLIENT_ID = env("COGNITO_WEB_CLIENT_ID", default="")
COGNITO_DOMAIN_PREFIX = env("COGNITO_DOMAIN_PREFIX", default="")

# JWT 検証時に許可する client_id の集合（web client のみ。空文字は除外）。
COGNITO_ALLOWED_CLIENT_IDS = tuple(client_id for client_id in (COGNITO_WEB_CLIENT_ID,) if client_id)

# JWT issuer（token の iss claim と完全一致を要求する）
COGNITO_JWT_ISSUER = (
    f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}" if COGNITO_USER_POOL_ID else ""
)

# JWKS URL（公開鍵取得用）
COGNITO_JWKS_URL = f"{COGNITO_JWT_ISSUER}/.well-known/jwks.json" if COGNITO_USER_POOL_ID else ""

# 初期管理者メール（seed が m_user_allowed_emails に登録する。締め出し防止）。
# qol-user-pool の initial_admin_email と一致させること。
INITIAL_ADMIN_EMAIL = env("INITIAL_ADMIN_EMAIL", default="")

# --- LLM (AI 申請文生成) ---
# API キーは DB(AiConfig) にユーザー単位で保存する。
# _BASE_URL を上書きしたい場合（eval-proxy 経由等）に使用。空ならプロバイダ既定。
LLM_API_BASE_URL = env("LLM_API_BASE_URL", default="")

# --- Logging ---

LOG_DIR = os.environ.get("LOG_DIR", "/tmp")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
