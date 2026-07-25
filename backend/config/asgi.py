"""ASGI config for skill-logger project.

本番環境(Lambda)では Mangum を経由して ASGI アプリケーションを実行する。
Lambda のエントリーポイント: config.asgi.handler
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

application = get_asgi_application()

# AWS Lambda ハンドラー（Mangum）
try:
    from mangum import Mangum

    handler = Mangum(application, lifespan="off")  # type: ignore[arg-type]
except ImportError:
    # ローカル開発時は Mangum 不要
    pass
