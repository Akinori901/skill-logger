# SkillLogger

<p>
  <img alt="Python / Django" src="https://img.shields.io/badge/Django_6-clean_arch-092E20?logo=django&logoColor=white">
  <img alt="React" src="https://img.shields.io/badge/React_19-TypeScript-61DAFB?logo=react&logoColor=black">
  <img alt="AI生成" src="https://img.shields.io/badge/AI生成-Gemini_/_Claude_/_OpenAI-D97757">
  <img alt="AWS" src="https://img.shields.io/badge/AWS-Lambda_/_CloudFront_/_EFS-232F3E?logo=amazonwebservices&logoColor=white">
  <img alt="IaC" src="https://img.shields.io/badge/IaC-Terraform-844FBA?logo=terraform&logoColor=white">
  <img alt="License" src="https://img.shields.io/badge/License-MIT-green">
</p>

> このリポジトリは、非公開の開発リポジトリからリリース時点のスナップショットを公開している
> **ミラー**です。開発履歴は含まれず、`v*` タグごとに1コミットが積まれます。

業務経歴を構造化して棚卸しし、そこから職務経歴書や案件応募（審査申請など）向けの文章を
AI 生成する、個人向けの経歴管理基盤。

案件ごとに「何を・どんな規模の組織で・どんな数字の成果を出したか」を構造化データとして
蓄積しておけば、応募のたびにゼロから書き起こす必要がなくなる。蓄積したデータは Markdown
としても出力でき、AI に渡せば支援領域ごとの申請文の下書きも作れる。

## 主な機能

- **棚卸し**: 案件（業界・会社規模・期間・ポジション・概要・担当・技術・苦労工夫・数字付き成果・実績URL）を構造化して蓄積。
- **支援領域への紐付け**: 各案件を支援領域（モダナイゼーション / 内製化 / AI活用 など12領域）に寄与度つきで紐付け。
- **Markdown 出力**: 蓄積した案件を棚卸し Markdown として出力・コピー。
- **AI 申請文生成**: 支援領域を優先順位つきで選び、紐づく案件から「50〜200字・企業規模・数字入り」の申請文を AI 生成・編集・コピー。LLM は Gemini（既定・無料枠）/ Claude / OpenAI を選択可（API キーはユーザーが登録）。
- **取り込み**: 外部の棚卸しツールが出力した技術メタデータ（言語・FW・期間・規模・関与コミット）を案件の下書きとして取り込み。

## 技術スタック

| レイヤー | 技術 |
|---------|------|
| バックエンド | Python 3.13 / Django 6 / Django REST Framework / SQLite（本番は EFS 上） |
| フロントエンド | React 19 / TypeScript / Vite / MUI / TanStack Query / Zustand |
| 開発基盤 | Docker Compose / uv / ruff / mypy (strict) |
| インフラ | AWS Lambda + API Gateway + S3 + CloudFront + EFS / Terraform / GitHub Actions (OIDC) |

## アーキテクチャ

バックエンドはクリーンアーキテクチャ（4層）を採用し、依存の向きを一方向に保つ。

```
HTTP Request → View → UseCase → Service → Repository(ABC) → Repository(Impl) → Model → DB
```

- `domain/` … エンティティ・リポジトリ抽象・ドメイン例外（外部依存ゼロ）
- `application/` … ユースケース（オーケストレーション）・サービス
- `infrastructure/` … ORM モデル・リポジトリ実装
- `presentation/` … DRF View・Serializer・URL

依存解決は `config/container.py` の DI コンテナに集約している。

## ローカル開発

```bash
cp .env.example .env      # 必要に応じてポート等を編集
make setup                # build → up → migrate → seed
```

- フロント: http://localhost:${FRONTEND_PORT:-9999}
- API: http://localhost:${BACKEND_PORT:-19000}

複数プロジェクトを同時に動かす場合、`.env` の `BACKEND_PORT` / `FRONTEND_PORT` を
変更するとホスト側の公開ポートを衝突しない値にできる。

## 免責事項

- 本ソフトウェアは個人利用を想定したもので、無保証で提供されます（MIT License）。
- 経歴データ・API キー等の秘匿情報はリポジトリに含まれず、DB / 環境変数 のみに存在します。サンプルは架空企業のみを使用しています。

## ライセンス

[MIT License](LICENSE) © 2026 Akinori Fukugi
