FROM python:3.13-slim

# DB は SQLite（標準ライブラリ同梱）のため追加のシステム依存は不要。
#
# PDF 生成(WeasyPrint)のネイティブ依存 + 日本語フォント(Noto CJK JP)を導入する
# （本番 Dockerfile.production と同等。debian/slim の apt パッケージ名）。
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# uv インストール
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# 依存インストール（キャッシュ活用のため先にコピー）
COPY pyproject.toml ./
RUN uv sync --extra dev

# ソースコードコピー（開発時はvolumeマウントで上書き）
COPY . .

EXPOSE 8000

# 開発サーバー起動（ASGI = uvicorn、ホットリロード有効）
CMD ["uv", "run", "uvicorn", "config.asgi:application", "--host", "0.0.0.0", "--port", "8000", "--reload"]
