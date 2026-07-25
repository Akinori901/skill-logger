.PHONY: help up down build logs logs-backend logs-frontend logs-db restart ps \
       backend-shell frontend-shell mysql \
       migrate makemigrations seed test-backend lint format format-check type-check quality \
       test-frontend lint-frontend build-frontend setup

# ===========================
# Docker
# ===========================

help: ## コマンド一覧を表示
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

up: ## コンテナ起動
	docker compose up -d

down: ## コンテナ停止
	docker compose down

build: ## コンテナビルド
	docker compose build

logs: ## 全コンテナのログ表示
	docker compose logs -f

logs-backend: ## バックエンドのログ表示
	docker compose logs -f backend

logs-frontend: ## フロントエンドのログ表示
	docker compose logs -f frontend

logs-db: ## DBのログ表示
	docker compose logs -f db

restart: ## 全コンテナ再起動
	docker compose restart

ps: ## コンテナ状態確認
	docker compose ps

# ===========================
# Shell接続
# ===========================

backend-shell: ## バックエンドコンテナに入る
	docker compose exec backend bash

frontend-shell: ## フロントエンドコンテナに入る
	docker compose exec frontend sh

mysql: ## MySQLに接続
	docker compose exec db mysql -uskill_user -pskill_password skill_logger

# ===========================
# Backend
# ===========================

migrate: ## マイグレーション実行
	docker compose exec backend uv run python manage.py migrate

makemigrations: ## マイグレーションファイル作成
	docker compose exec backend uv run python manage.py makemigrations

seed: ## 初期データ投入（admin/admin1234 + 支援領域12マスタ）
	docker compose exec backend uv run python manage.py seed

test-backend: ## バックエンドテスト実行
	docker compose exec backend uv run python -m pytest -v

lint: ## Ruff Lint実行
	docker compose exec backend uv run ruff check .

format: ## Ruff Format実行
	docker compose exec backend uv run ruff format .

format-check: ## Ruff Formatチェック（修正なし）
	docker compose exec backend uv run ruff format --check .

type-check: ## mypy型チェック実行
	docker compose exec backend uv run mypy .

quality: lint format-check type-check ## コード品質チェック（lint + format-check + type-check）

# ===========================
# Frontend
# ===========================

test-frontend: ## フロントエンドテスト実行
	docker compose exec frontend npm run test

lint-frontend: ## フロントエンド Lint
	docker compose exec frontend npm run lint

build-frontend: ## フロントエンドビルド
	docker compose exec frontend npm run build

# ===========================
# セットアップ
# ===========================

setup: build up migrate seed ## 初回セットアップ（build → up → migrate → seed）
	@echo "セットアップ完了。フロント: http://localhost:$${FRONTEND_PORT:-9999}  API: http://localhost:$${BACKEND_PORT:-19000}"
