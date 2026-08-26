"""職務経歴書 / スキルシート PDF 出力サービス（サーバ HTML→PDF）。

蓄積した案件エンティティ（と任意のユーザープロフィール）から、
「サマリシート → 案件詳細 → スキルシート」の3ゾーン構成 PDF を生成する。
HTML テンプレートを組み立て WeasyPrint で PDF 化する。

体裁方針（採用担当が短時間でスキャンできることを優先）:
- 情報密度を下げ、案件は罫線ボックス（page-break-inside:avoid でページ跨ぎ分断を防ぐ）
- 企業名は出さず、業界＋規模で代替（anonymize 既定 True）
- スキルは経験年数を全角ブロック文字（■□）でバー可視化（外部アセット不要）
- 段組みは table + border:none セルで実現（WeasyPrint 63 は Grid/Flex 非推奨）

日本語フォント(Noto CJK JP)は Docker イメージに同梱済み。PR1(PoC)で
Lambda(Amazon Linux 2023)上での日本語描画を検証済み。
"""

from __future__ import annotations

from datetime import date
from html import escape
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from apps.careers.domain.entities import AchievementEntity, EngagementEntity

_CATEGORY_LABELS = {
    "speed": "速度改善",
    "cost": "コスト削減",
    "quality": "品質向上",
    "ops": "運用改善",
    "incident": "障害削減",
    "release": "リリース改善",
    "review": "レビュー体制改善",
}

# スキル年数バーの最大目盛（■□ の総数）。この年数以上は満杯表示。
_SKILL_BAR_MAX_YEARS = 10

# AI駆動開発の取り組み（AI活用セクションで前面に出す差別化要素）。
# 「AIを使った」でなく「AIをどう業務に組み込む仕組みを作ったか」を示す。
_AI_DRIVEN_WORKS = [
    "AIエージェント向けのスキル（再利用可能な作業手順）を作成し、定型業務を自動化・標準化",
    "コーディング規約やレビュー観点を rules として整備し、AIの生成品質を安定化・属人化を排除",
    "複数エージェントのオーケストレーション設定を構築し、調査・実装・レビューを並列処理で高速化",
    "対話型コマンド（スタッフ）を設計し、チーム全体で同じ手順・品質でAIを運用できる体制を整備",
    "コンテキスト設計の工夫（情報を絞る）でハルシネーションを抑え、実装スピードと品質を両立",
]

# 設計・アーキテクチャの一文（ヒーローの自己紹介リード末尾に添える）。
# クリーンアーキ(4層)/DDD/レイヤードの採用は案件リポの構造で確認済み。
# 各アーキの詳細（どの案件でどう使ったか）は案件カードの achievements に個別記載する。
_ARCHITECTURE_LEAD = (
    "設計面では、DDD志向のレイヤードアーキテクチャによる"
    "保守性・テスト容易性の高い設計を得意としています。"
)

# スキル表のカテゴリ分類（採用担当がスキャンしやすいよう技術を役割別に整理）。
# 各カテゴリ内は年数降順で並べる。どれにも入らない技術は「その他」に集約。
_SKILL_CATEGORIES: list[tuple[str, list[str]]] = [
    ("言語", ["PHP", "Python", "JavaScript", "TypeScript", "C#", "C", "SQL", "Shell", "VBScript"]),
    ("FW・ライブラリ", ["Laravel", "CakePHP", "Django", "Vue", "React", "Next.js", "Nuxt", "Vite", "pandas", "NumPy", "Sanctum"]),
    # DB は「プロダクト」を並べる。SQL は問い合わせ言語なので言語カテゴリへ移動した。
    ("DB", ["MySQL", "PostgreSQL", "DynamoDB", "Redis", "Access"]),
    ("インフラ・CI/CD", ["Docker", "Kubernetes", "Nginx", "Terraform", "GitHub Actions", "GitLab CI", "YAML"]),
    ("テスト・API", ["PHPUnit", "Vitest", "Cypress", "Selenium", "Swagger"]),
]

# 「その他」カテゴリに載せる技術のホワイトリスト。カテゴリ未分類の技術は
# 雑多に増える(Bootstrap/webpack/WordPress 等)ため、ここに挙げたものだけを
# 「その他」に表示し、スキルシートを1ページに収める。名寄せ後の名称で判定する。
_OTHER_ALLOWLIST = {"JSON", "jQuery", "draw.io", "Blade", "CSS", "HTML"}

# 基盤技術: ほぼ全案件で使うが、git集計(自分がコミットしたファイルの拡張子)には
# 出にくい技術。Dockerfile/マイグレーションを毎回書くわけではないので過小評価される。
# これらは「キャリア全期間(全案件の最古開始〜最新終了)」で年数を出す。
# ※特定案件のみで使った技術は manual_skills で個別指定する(AWS 等)。
# ※Shell/Bash は「主体的に書いた開発言語」ではなく Docker/CI 付随の運用スクリプトが
#   主なため基盤技術から除外し、実際に .sh を書いた案件の期間・関与度で年数を出す。
_FOUNDATION_TECH = {
    "Docker",
    "SQL",
    "Git",
    "Linux",
    "YAML",
    "Makefile",
    "Nginx",
}

# 非技術(設定/環境/雑多ファイルの拡張子)。git集計で拡張子=言語名にすると
# env/conf/pem/neon 等が「技術」として混入するため、スキル表から除外する。
# ※scan-git-local.sh でも除外しているが、既存取込データにも残るため集計側でも弾く。
_NON_TECH_TOKENS = {
    "env",
    "conf",
    "cnf",
    "config",
    "ini",
    "toml",
    "neon",
    "properties",
    "htaccess",
    "htpasswd",
    "pem",
    "key",
    "crt",
    "pub",
    "pid",
    "lock",
    "dot",
    "po",
    "pot",
    "editorconfig",
    "eslintignore",
    "dockerignore",
    "gitignore",
    "gitattributes",
    "example",
    "sample",
    "dist",
    "tpl",
    "tmpl",
    "ctp",
    "cop",
    "diff",
    "patch",
    "bak",
    "backup",
    "cache",
    "log",
    "tmp",
    "swp",
    "dev",
    "develop",
    "prod",
    "production",
    "stage",
    "staging",
    "local",
    "test",
    "testing",
    "skip",
    "text",
    "h",
    "xml",
    "csproj",
    "mdc",
    "less",  # CSSプリプロセッサの拡張子。CSSに含まれるものとしてスキル単体には出さない
}

# A4・日本語・印刷体裁の CSS（マッチング向けデザイン。信頼感のある濃紺基調）。
# weasyprint 63 は flex/grid が不安定なため table / inline-block で組む。
# 改ページ: 案件カード・スキルカードは page-break-inside:avoid で途中で切れないようにする。
_ACCENT = "#1a3a6b"
_ACCENT2 = "#2b5aa0"
_CSS = """
@page { size: A4; margin: 11mm 13mm; }
body { font-family: 'Noto Sans CJK JP', 'Noto Sans JP', sans-serif;
       font-size: 10pt; color: #1a2230; line-height: 1.4; }
h1 { font-size: 15pt; margin: 0 0 6px; color: #1a3a6b; }
h2 { font-size: 12pt; color: #1a3a6b; margin: 11px 0 6px;
     border-left: 4px solid #1a3a6b; padding-left: 9px; }
.section { margin-bottom: 4px; white-space: pre-wrap; }
.muted { color: #6b7480; font-size: 9pt; }
.page-break { page-break-before: always; }

/* ヒーロー（氏名・肩書・リード・主要スキルチップ） */
.hero { background: #1a3a6b; color: #fff; border-radius: 10px;
        padding: 16px 20px; margin-bottom: 6px; }
.hero .name { font-size: 19pt; font-weight: 800; letter-spacing: .02em; }
.hero .attr { font-size: 10pt; color: #cdd9ee; margin-top: 2px; }
.hero .lead { font-size: 9.5pt; color: #e8eef7; margin-top: 9px; }
.hero .chips { margin-top: 10px; }
.hero .chip { display: inline-block; background: rgba(255,255,255,0.14);
              border: 1px solid rgba(255,255,255,0.30); border-radius: 12px;
              padding: 2px 10px; margin: 2px 4px 2px 0; font-size: 9pt; }
.hero .chip b { font-weight: 700; }
.hero .chip .cy { color: #cdd9ee; margin-left: 5px; }

/* スキル: カテゴリ別カード（2列） */
table.skillgrid { border-collapse: separate; border-spacing: 8px 0; width: 100%; table-layout: fixed; }
table.skillgrid td { vertical-align: top; width: 50%; padding: 0; }
.scard { border: 1px solid #e2e7ee; border-radius: 8px; padding: 9px 11px; margin-bottom: 8px;
         page-break-inside: avoid; line-height: 1.55; }
.scat { font-weight: 700; font-size: 9.5pt; color: #5a6472; margin-bottom: 5px; letter-spacing: .03em; }
table.srow { border-collapse: collapse; width: 100%; table-layout: fixed; }
table.srow td { font-size: 9pt; padding: 2px 0; vertical-align: middle; }
.srow .st { font-weight: 600; }
.srow .st .ver { color: #6b7480; font-weight: 400; font-size: 8pt; margin-left: 4px; }
.srow .barcell { width: 66px; }
/* バーは WeasyPrint で確実に描画されるよう block 要素で組む。
   inline-block + 子span の % 幅は WeasyPrint で 0 に潰れることがあるため使わない。 */
.srow .sbar { display: block; width: 60px; height: 6px; background: #e2e7ee;
              border-radius: 3px; overflow: hidden; }
.srow .sfill { display: block; height: 6px; background: #2b5aa0; border-radius: 3px; }
.srow .sy { width: 42px; text-align: right; color: #5a6472; white-space: nowrap; }
.srow .sc { width: 30px; text-align: right; color: #6b7480; font-size: 8pt; }

/* AI活用（取り組みリスト＋ツール表） */
.aiwork { border: 1px solid #cfe0f5; background: #f2f7fd; border-radius: 8px;
          padding: 10px 13px; margin-bottom: 8px; page-break-inside: avoid; }
.aiwork .aititle { font-weight: 700; color: #1a3a6b; margin-bottom: 4px; }
.aiwork ul { margin: 2px 0 0; padding-left: 18px; }
.aiwork li { font-size: 9.5pt; margin: 2px 0; }
table.data { border-collapse: collapse; width: 100%; margin-top: 6px; page-break-inside: avoid; }
table.data th, table.data td { border: 1px solid #dbe2ea; padding: 4px 8px; font-size: 9pt; text-align: left; }
table.data th { background: #eef3fa; color: #1a3a6b; }

/* 自己PR */
.label { font-weight: 700; color: #1a3a6b; margin-top: 4px; }

/* 案件カード（新しい順・page-break-inside:avoidで途中で切れない） */
.ecard { border: 1px solid #e2e7ee; border-radius: 8px; padding: 7px 12px;
         margin-bottom: 6px; page-break-inside: avoid; }
.ecard .ehead { margin-bottom: 2px; }
.ecard .enum { color: #2b5aa0; font-weight: 800; font-size: 10pt; margin-right: 6px; }
.ecard .etitle { font-weight: 700; font-size: 11pt; color: #1a2230; }
.ecard .eperiod { color: #6b7480; font-size: 9pt; float: right; }
.ecard .emeta { color: #5a6472; font-size: 9pt; margin: 1px 0 3px; }
.ecard .label { font-size: 9pt; margin-top: 3px; }
.ecard .section { font-size: 9.5pt; }
.ver-line { font-size: 9pt; color: #5a6472; margin: 3px 0; }
.ver-line .tech-cat { font-weight: 700; color: #1a3a6b; }

/* 担当工程・技術タグ */
.phase { display: inline-block; background: #eef3fa; color: #1a3a6b;
         border: 1px solid #cfe0f5; border-radius: 4px;
         padding: 1px 8px; margin: 1px 3px 1px 0; font-size: 8.5pt; }
.ttag { display: inline-block; background: #f4f6f9; color: #33404f;
        border: 1px solid #e2e7ee; border-radius: 4px;
        padding: 1px 7px; margin: 1px 3px 1px 0; font-size: 8.5pt; }

/* アーキテクチャ層図（上位層→下位層の積み重ね。カード内で改ページ分断しない） */
.archdiagram { page-break-inside: avoid; margin: 1px 0 1px; }
.archdiagram .archname { font-size: 9pt; font-weight: 700; color: #1a3a6b; margin-bottom: 3px; }
.archdiagram .archgrid { display: table; width: 100%; border-collapse: separate;
        border-spacing: 6px 0; table-layout: fixed; }
.archdiagram .archrow { display: table-row; }
.archdiagram .archcol { display: table-cell; width: 50%; vertical-align: top; }
.archdiagram .archlayer { display: block; background: #f2f7fd; border: 1px solid #cfe0f5;
        border-left: 3px solid #2b5aa0; border-radius: 4px; color: #1a2230;
        padding: 2px 12px; margin-bottom: 2px; font-size: 8.5pt; font-weight: 600; }
.ttag .tv { color: #2b5aa0; }
.tech-line { font-size: 9pt; margin: 1px 0; }
.tech-cat { font-weight: 700; color: #5a6472; }
.ach { margin: 2px 0; font-size: 9.5pt; }
.tag { color: #0d7d5a; font-weight: 700; }

/* 段組み用テーブル（罫線なし） */
table.layout { border-collapse: collapse; width: 100%; }
table.layout td { border: none; padding: 0; vertical-align: top; }
"""

# 担当工程コード → 表示ラベル（Phase 2 で entities 側に正式定義。PDF はフォールバック辞書を持つ）
_PHASE_LABELS = {
    "req": "要件定義",
    "basic": "基本設計",
    "detail": "詳細設計",
    "backend": "Back実装",
    "frontend": "Front実装",
    "test": "テスト",
    "research": "調査",
    "refactor": "リファクタ",
}

_CONTRACT_LABELS = {
    "contract": "請負",
    "quasi": "準委任",
    "dispatch": "派遣",
}

_TECH_CATEGORY_LABELS = {
    "language": "言語",
    "db": "DB",
    "framework": "FW",
    "cloud": "クラウド",
    "tool": "ツール",
}

# 技術名の表記ゆれ名寄せ（skill-inventory は Linguist=大文字始まりと
# package.json=小文字の両方から拾うため Vue/vue 等が二重集計される）。
# 正規化後の表示名を値にする。キーは小文字化して照合する。
_TECH_CANONICAL = {
    "vue": "Vue",
    "vue.js": "Vue",
    "vuejs": "Vue",
    "react": "React",
    "react.js": "React",
    "nuxt": "Nuxt",
    "next": "Next.js",
    "next.js": "Next.js",
    "node": "Node.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "vite": "Vite",
    "vitest": "Vitest",
    "django": "Django",
    "laravel": "Laravel",
    # detected_tech(マーカー検出=大文字)と git言語(小文字)の二重表示を防ぐ名寄せ。
    "cypress": "Cypress",
    "docker": "Docker",
    "dockerfile": "Docker",
    "phpunit": "PHPUnit",
    "swagger": "Swagger",
    "openapi": "Swagger",
    "terraform": "Terraform",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "tailwindcss": "Tailwind CSS",
    "tailwind": "Tailwind CSS",
    "pandas": "pandas",
    "numpy": "NumPy",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "python": "Python",
    "php": "PHP",
    "html": "HTML",
    "css": "CSS",
    "sql": "SQL",
    "shell": "Shell",
    "dockerfile": "Docker",
    "docker": "Docker",
    "makefile": "Makefile",
    "hcl": "HCL",
    "yaml": "YAML",
}


def _canonical_tech(name: str) -> str:
    """技術名を表記ゆれ名寄せする。未知の名前はそのまま返す。"""
    key = name.strip().lower()
    return _TECH_CANONICAL.get(key, name.strip())


def _clean_version(ver: str) -> str:
    """composer/npm のバージョン制約(^8.12 | ~5.4.0 | ^7.3|^8.0)を読みやすく整える。

    先頭の ^ ~ >= 等を落とし、複数候補(|)は最初を採る。'8.4.5' や '8.12' の形にする。
    """
    v = str(ver).strip()
    v = v.split("|")[0].strip()  # "^7.3|^8.0" → "^7.3"
    return v.lstrip("^~>=<v ").strip()


def _version_key(ver: str) -> tuple[int, ...]:
    """バージョン文字列を数値順に比較するためのキー(3.9 < 3.12 になるように)。"""
    parts = []
    for p in str(ver).replace("-", ".").split("."):
        num = "".join(ch for ch in p if ch.isdigit())
        parts.append(int(num) if num else 0)
    return tuple(parts)


class ResumePdfService:
    """案件エンティティ（＋任意プロフィール）→ サマリ＋案件詳細＋スキルシート統合 PDF(bytes)。"""

    def render_pdf(
        self,
        engagements: list[EngagementEntity],
        profile: object | None = None,
        *,
        anonymize: bool = True,
    ) -> bytes:
        """PDF を生成する。

        Args:
            engagements: 対象案件。
            profile: UserProfileEntity（Phase 3 で導入）。None の場合はサマリの
                プロフィール欄を省略しスキルマトリクスのみ表示する。
            anonymize: True（既定）なら企業名を出さず業界＋規模で代替する。
        """
        html = self._build_html(engagements, profile, anonymize=anonymize)
        # 遅延 import: weasyprint はネイティブ依存を要するため、import 時点で
        # 環境が整っていない場合のエラーを PDF 生成時に閉じ込める。
        from weasyprint import HTML  # noqa: PLC0415

        return cast("bytes", HTML(string=html).write_pdf())

    # --- HTML 組み立て ---

    def _build_html(self, engagements: list[EngagementEntity], profile: object | None, *, anonymize: bool) -> str:
        # 2ゾーン構成: サマリ（スキルマトリクス込み）→ 案件詳細。
        # 末尾のスキルシートはサマリのスキルマトリクスと重複するため廃止。
        summary = self._render_summary(engagements, profile)
        details = self._render_details(engagements, anonymize=anonymize)
        return (
            f"<html><head><meta charset='utf-8'><style>{_CSS}</style></head>"
            f"<body>{summary}"
            f"<div class='page-break'></div>{details}</body></html>"
        )

    # --- ゾーン1: サマリシート ---

    def _render_summary(self, engagements: list[EngagementEntity], profile: object | None) -> str:
        parts: list[str] = []
        # ヒーロー（氏名・肩書・自己紹介リード・主要スキルチップ）を1ブロックに。
        parts.append(self._render_hero(engagements, profile))

        # スキル・経験（カテゴリ別カード・バージョン付き）
        parts.append("<h2>スキル・経験</h2>")
        parts.append(self._render_skill_matrix(engagements))

        # 生成AI活用（取り組み＋ツール表）。AI駆動開発は今後の注目ポイントなので前面に。
        parts.append("<h2>生成AI活用・AI駆動開発</h2>")
        parts.append(self._render_ai_usage(self._profile_list_attr(profile, "ai_usage")))

        # 自己PR（強み / 得意業務）
        strengths = self._profile_attr(profile, "strengths")
        good_at = self._profile_attr(profile, "good_at")
        if strengths or good_at:
            parts.append("<h2>自己PR</h2>")
            if strengths:
                parts.append(f'<div class="label">強み</div><div class="section">{escape(strengths)}</div>')
            if good_at:
                parts.append(f'<div class="label">得意業務</div><div class="section">{escape(good_at)}</div>')

        return "".join(parts)

    def _render_hero(self, engagements: list[EngagementEntity], profile: object | None) -> str:
        name = self._profile_attr(profile, "display_name") or "職務経歴書"
        attrs = [escape(v) for key in ("age_range", "residence", "headline") if (v := self._profile_attr(profile, key))]
        attr_line = " ｜ ".join(attrs)
        # リード文（自己紹介）。末尾に設計・アーキテクチャの一文を添える。
        # アーキの詳細は各案件カードの「実績・取り組み」に個別記載するため、
        # ヒーローでは大きなブロックにせず一文だけで第一印象を作る。
        summary_text = self._profile_attr(profile, "summary")
        lead_text = " ".join(t for t in (summary_text, _ARCHITECTURE_LEAD) if t)
        lead = f'<div class="lead">{escape(lead_text)}</div>' if lead_text else ""
        # 主要スキル(年数上位)をチップに。一目で「何ができる人か」を伝える。
        stats = self._aggregate_skill_years(engagements)
        chips = "".join(
            f'<span class="chip"><b>{escape(t)}</b><span class="cy">{y:.0f}年</span></span>' for t, y, _ in stats[:8]
        )
        chip_block = f'<div class="chips">{chips}</div>' if chips else ""
        return (
            f'<div class="hero"><div class="name">{escape(name)}</div>'
            f'<div class="attr">{attr_line}</div>{lead}{chip_block}</div>'
        )

    def _render_skill_matrix(self, engagements: list[EngagementEntity]) -> str:
        stats = self._aggregate_skill_years(engagements)
        if not stats:
            return "<p class='muted'>技術情報が登録されていません。</p>"
        years_by = {t: (y, c) for t, y, c in stats}
        versions = self._skill_version_ranges(engagements)

        # カテゴリ別に分類（言語/FW/DB/インフラ・CI/テスト・API/その他）。
        cards: list[str] = []
        assigned: set[str] = set()
        for cat, techs in _SKILL_CATEGORIES:
            rows = [(t, *years_by[t]) for t in techs if t in years_by]
            rows.sort(key=lambda r: -r[1])
            if rows:
                assigned.update(t for t, *_ in rows)
                cards.append(self._skill_card(cat, rows, versions))
        # どのカテゴリにも入らない技術は「その他」に集約。ただし雑多に増えるため
        # ホワイトリスト(_OTHER_ALLOWLIST)のものだけ表示し、1ページ収まりを担保する。
        rest = [
            (t, y, c)
            for t, (y, c) in years_by.items()
            if t not in assigned and (t in _OTHER_ALLOWLIST or _canonical_tech(t) in _OTHER_ALLOWLIST)
        ]
        rest.sort(key=lambda r: -r[1])
        if rest:
            cards.append(self._skill_card("その他", rest, versions))

        # カードを2列テーブルに振り分け（縦の高さを均す簡易バランス）。
        left, right = [], []
        lh = rh = 0
        for c in cards:
            weight = c.count("<tr")  # 行数≒高さの近似
            if lh <= rh:
                left.append(c)
                lh += weight + 2
            else:
                right.append(c)
                rh += weight + 2
        return f'<table class="skillgrid"><tr><td>{"".join(left)}</td><td>{"".join(right)}</td></tr></table>'

    def _skill_card(self, cat: str, rows: list[tuple[str, float, int]], versions: dict[str, str]) -> str:
        items: list[str] = []
        for tech, years, count in rows:
            ver = versions.get(tech, "")
            ver_html = f'<span class="ver">{escape(ver)}</span>' if ver else ""
            filled = min(int(round(years * 10)), 100)
            items.append(
                "<tr>"
                f'<td class="st">{escape(tech)}{ver_html}</td>'
                f'<td class="barcell"><div class="sbar"><div class="sfill" style="width:{filled}%"></div></div></td>'
                f'<td class="sy">{years:.1f}年</td>'
                f'<td class="sc">{count}件</td>'
                "</tr>"
            )
        return (
            f'<div class="scard"><div class="scat">{escape(cat)}</div>'
            f'<table class="srow">{"".join(items)}</table></div>'
        )

    def _skill_version_ranges(self, engagements: list[EngagementEntity]) -> dict[str, str]:
        """技術ごとのバージョンレンジ（最小〜最大）を集約。'8.0' や '5.7〜8.4' 等。"""
        collected: dict[str, set[str]] = {}
        for e in engagements:
            for t, v in (getattr(e, "tech_versions", None) or {}).items():
                cv = _clean_version(v)
                if cv:
                    collected.setdefault(_canonical_tech(t), set()).add(cv)
        result: dict[str, str] = {}
        for tech, vers in collected.items():
            # 数値順にソート(文字列順だと 3.12 < 3.9 のように誤る)。
            sv = sorted(vers, key=_version_key)
            result[tech] = sv[0] if len(sv) == 1 else f"{sv[0]}〜{sv[-1]}"
        return result

    # --- ゾーン2: 案件詳細 ---

    def _render_details(self, engagements: list[EngagementEntity], *, anonymize: bool) -> str:
        parts = ["<h1>職務経歴（案件詳細）</h1>"]
        if not engagements:
            parts.append("<p class='muted'>対象の案件がありません。</p>")
        # 新しい順(直近の実績を上)に並べる。終了→開始の降順。期間空(現在進行中)は最上位。
        ordered = sorted(
            engagements,
            key=lambda e: (e.period_end or "9999-99", e.period_start or ""),
            reverse=True,
        )
        # 匿名時の企業仮名マップを構築。集約キー(sier優先→company_name)が同一の案件には同一仮名(企業A/企業B…)を
        # 割り当て、「同じ企業から複数案件」が読み手に伝わるようにする。登場順(期間降順)で採番。
        alias_map = self._build_company_aliases(ordered)
        for i, e in enumerate(ordered, start=1):
            parts.append(self._render_engagement(e, i, anonymize=anonymize, alias_map=alias_map))
        return "".join(parts)

    @staticmethod
    def _label(n: int) -> str:
        """0→A, 1→B, …, 25→Z, 26→AA … と桁上がりするアルファベット表記。"""
        label = ""
        while True:
            label = chr(ord("A") + (n % 26)) + label
            n = n // 26 - 1
            if n < 0:
                break
        return label

    def _build_company_aliases(self, ordered: list[EngagementEntity]) -> dict[str, str]:
        """匿名見出しの集約仮名を返す。案件ごとに2系統を使い分ける:

        - sier あり: 同一 sier を「企業A/企業B…」に束ねる（SIer経由の集約軸）。
          キー = "sier:<sier>"、値 = "企業A"。
        - sier なし（直取引・自社案件など）: 同一 company_name を client 名 + 連番で
          束ねる。「食品メーカー A / 食品メーカー B」のように、企業を伏せつつ同一企業を示す。
          キー = "company:<company_name>"、値 = "<client> <A/B>"（clientが無ければ空→
          _display_title 側で「案件N：業界」にフォールバック）。

        同一 company_name が1件しかなければ連番(A)は付けない（単独案件をぼかしすぎない）。
        """
        # sier ごと採番（企業A/B…）
        aliases: dict[str, str] = {}
        sier_seen: list[str] = []
        # company ごと: 出現順の index と、その client を記録（sier 無しのみ対象）
        company_order: dict[str, int] = {}
        company_client: dict[str, str] = {}
        company_count: dict[str, int] = {}
        for e in ordered:
            sier = (e.sier or "").strip()
            company = (e.company_name or "").strip()
            if sier:
                if sier not in sier_seen:
                    sier_seen.append(sier)
                aliases[f"sier:{sier}"] = f"企業{self._label(sier_seen.index(sier))}"
            elif company:
                if company not in company_order:
                    company_order[company] = len(company_order)
                    company_client[company] = (e.client or "").strip()
                company_count[company] = company_count.get(company, 0) + 1
        # sier なし company の連番ラベルを確定（同一 company が2件以上のときだけ連番）
        per_client_index: dict[str, int] = {}
        for company, _idx in company_order.items():
            client = company_client.get(company, "")
            if not client:
                continue
            if company_count.get(company, 0) >= 2:
                i = per_client_index.get(client, 0)
                aliases[f"company:{company}"] = f"{client} {self._label(i)}"
                per_client_index[client] = i + 1
            else:
                aliases[f"company:{company}"] = client
        return aliases

    def _should_mask_company(self, e: EngagementEntity, *, anonymize: bool) -> bool:
        """この案件の企業名を伏せるか。
        ルール:
          - is_public=False（絶対に実名を出さない企業）: スライダーに関わらず常に伏せる。
          - is_public=True（実名を出してよい企業）: スライダー(anonymize)に従う。
        """
        if not e.is_public:
            return True
        return anonymize

    def _display_title(
        self,
        e: EngagementEntity,
        index: int,
        *,
        anonymize: bool,
        alias_map: dict[str, str] | None = None,
    ) -> str:
        """案件詳細の見出し。

        - 伏せるとき（sier あり）: 「企業A（SIer集約） / メーカー業種 / 案件名」。
        - 伏せるとき（sier なし＝直取引・自社案件など）: 「メーカー業種 A / 案件名」。
          同一 company_name が複数あれば client に連番(A/B…)を付け同一企業を示す。
          企業A(SIer仮名)は付けない。
          いずれも空要素は省く。全て空なら「案件N：業界」にフォールバック。
        - 出すとき: 企業名（company_name） / 案件名。
        """
        company = e.company_name.strip() if e.company_name else ""
        title = (e.title or "").replace("[inv] ", "").strip()
        amap = alias_map or {}
        if self._should_mask_company(e, anonymize=anonymize):
            sier = (e.sier or "").strip()
            if sier:
                # 企業A（SIer） / メーカー業種 / 案件名
                alias = amap.get(f"sier:{sier}")
                client = (e.client or "").strip()
                parts = [p for p in (alias, client, title) if p]
            else:
                # メーカー業種[ 連番] / 案件名（company_name で集約、企業A仮名は付けない）
                label = amap.get(f"company:{company}") if company else ""
                parts = [p for p in (label, title) if p]
            if parts:
                return " / ".join(parts)
            industry = e.industry.strip() if e.industry else ""
            head = f"案件{index}"
            return f"{head}：{industry}" if industry else head
        if company:
            return f"{company} / {title}" if title else company
        return title or f"案件{index}"

    def _render_engagement(
        self,
        e: EngagementEntity,
        index: int,
        *,
        anonymize: bool,
        alias_map: dict[str, str] | None = None,
    ) -> str:
        # カード。page-break-inside:avoid で PDF 化時に途中で切れないようにする。
        rows: list[str] = ['<div class="ecard">']
        period = self._period(e)
        title = self._display_title(e, index, anonymize=anonymize, alias_map=alias_map)
        # ヘッダ: 通し番号＋タイトル＋期間(右)。
        rows.append(
            f'<div class="ehead"><span class="eperiod">{escape(period)}</span>'
            f'<span class="enum">#{index}</span>'
            f'<span class="etitle">{escape(title)}</span></div>'
        )
        # メタ行: 業界 ｜ 規模 ｜ 雇用形態 ｜ 役割（会社名は出さない）
        rows.append(f'<div class="emeta">{self._meta_line(e, anonymize=anonymize)}</div>')

        # overview は実質的な本文がある時だけ出す。skill-inventory 取込で YAML の
        # ブロック記法（">" や "|"）だけが値に残るケースがあり、その場合は概要欄を出さない。
        overview = e.overview.strip() if e.overview else ""
        if overview and overview not in (">", "|"):
            rows.append(f'<div class="label">プロジェクト概要</div><div class="section">{escape(overview)}</div>')

        # 担当工程（担当分だけ塗りタグ）
        phase_tags = self._phase_tags(e)
        if phase_tags:
            rows.append(f'<div class="label">担当工程</div><div>{phase_tags}</div>')

        # 業務内容（事実）
        if e.responsibilities:
            rows.append(f'<div class="label">担当したこと</div><div class="section">{escape(e.responsibilities)}</div>')

        # 実績・取り組み（narrative=作文があれば優先、無ければ challenges）
        narrative_attr = self._engagement_attr(e, "narrative")
        narrative = str(narrative_attr) if narrative_attr else e.challenges
        if narrative:
            rows.append(f'<div class="label">実績・取り組み</div><div class="section">{escape(narrative)}</div>')

        # アーキテクチャ（採用した層構造を図で可視化。リポ構造で採用実態を確認済み）
        arch = self._arch_diagram(e)
        if arch:
            rows.append(arch)

        # 技術（種別分離: tech_categorized 優先 → flat フォールバック）
        rows.append(self._tech_block(e))

        # 成果（数字付き）
        if e.achievements:
            rows.append('<div class="label">成果</div>')
            for a in e.achievements:
                rows.append(self._achievement(a))

        # 実績URL
        if e.urls:
            rows.append('<div class="label">実績URL</div>')
            for u in e.urls:
                label = f"{escape(u.label)}: " if u.label else ""
                rows.append(f'<div class="ach">・{label}{escape(u.url)}</div>')

        rows.append("</div>")
        return "".join(r for r in rows if r)

    def _meta_line(self, e: EngagementEntity, *, anonymize: bool) -> str:
        parts: list[str] = []
        # 会社名は見出し(etitle)に集約するため、メタ行は常に業界+規模+役割で構成する
        # （非匿名時の会社名重複を避ける）。業界が無い案件は規模/役割のみ。
        if e.industry:
            parts.append(escape(e.industry))
        scale = self._company_scale(e)
        if scale:
            parts.append(escape(scale))
        contract = self._contract_label(e)
        if contract:
            parts.append(escape(contract))
        if e.position:
            parts.append(escape(e.position))
        return " ｜ ".join(parts)

    def _phase_tags(self, e: EngagementEntity) -> str:
        phases = self._engagement_attr(e, "phases") or []
        if not isinstance(phases, list):
            return ""
        tags = []
        for code in phases:
            label = _PHASE_LABELS.get(str(code), str(code))
            tags.append(f'<span class="phase">{escape(label)}</span>')
        return "".join(tags)

    def _arch_diagram(self, e: EngagementEntity) -> str:
        """採用アーキテクチャの層構造を図で可視化する。

        architecture = {"name": str, "layers": [str, ...]} を、上位層→下位層に
        積み重なるボックスで描画する。WeasyPrint 安定のため table/div の block で組み、
        カード内で改ページ分断しないよう page-break-inside:avoid を効かせる。
        """
        arch = self._engagement_attr(e, "architecture")
        if not isinstance(arch, dict) or not arch:
            return ""
        name = str(arch.get("name") or "").strip()
        layers = arch.get("layers") or []
        if not isinstance(layers, list) or not layers:
            return ""
        head = f'<div class="archname">{escape(name)}</div>' if name else ""
        # 層は上位→下位の順序を保ちつつ2列で描画し、縦の高さを抑える。
        # 左列=前半・右列=後半（奇数層は左列が1つ多い）。各列は上から順に読む。
        # WeasyPrint 63 は flex/grid 非推奨のため table(2セル×N行)で組む。
        half = (len(layers) + 1) // 2
        left, right = layers[:half], layers[half:]
        rows = []
        for i in range(half):
            lcell = f'<div class="archlayer">{escape(str(left[i]))}</div>' if i < len(left) else ""
            rcell = f'<div class="archlayer">{escape(str(right[i]))}</div>' if i < len(right) else ""
            rows.append(
                f'<div class="archrow"><div class="archcol">{lcell}</div>'
                f'<div class="archcol">{rcell}</div></div>'
            )
        boxes = "".join(rows)
        return (
            '<div class="label">アーキテクチャ</div>'
            f'<div class="archdiagram">{head}<div class="archgrid">{boxes}</div></div>'
        )

    def _tech_block(self, e: EngagementEntity) -> str:
        categorized = self._engagement_attr(e, "tech_categorized")
        versions = getattr(e, "tech_versions", None) or {}
        lines: list[str] = []
        if isinstance(categorized, dict) and any(categorized.values()):
            for cat_code, label in _TECH_CATEGORY_LABELS.items():
                vals = categorized.get(cat_code) or []
                if vals:
                    joined = "、".join(escape(str(v)) for v in vals)
                    lines.append(f'<div class="tech-line"><span class="tech-cat">{label}</span>：{joined}</div>')
        elif e.tech_stack:
            # 表記ゆれ名寄せ(cypress/Cypress)＋非技術除外＋重複解消。バージョンがあれば併記。
            norm_ver = {_canonical_tech(t): _clean_version(v) for t, v in versions.items() if v}
            seen: list[str] = []
            tags: list[str] = []
            for t in e.tech_stack:
                ct = _canonical_tech(t)
                if ct.lower() in _NON_TECH_TOKENS or ct in seen:
                    continue
                seen.append(ct)
                ver = norm_ver.get(ct, "")
                ver_html = f' <span class="tv">{escape(ver)}</span>' if ver else ""
                tags.append(f'<span class="ttag">{escape(ct)}{ver_html}</span>')
            lines.append(f"<div>{''.join(tags)}</div>")
        if not lines:
            return ""
        return '<div class="label">使用技術</div>' + "".join(lines)

    # --- 集計ヘルパ ---

    def _all_techs(self, e: EngagementEntity) -> list[str]:
        """案件の技術を categorized 優先 → flat フォールバックで平坦なリストに。
        表記ゆれは名寄せする。"""
        categorized = self._engagement_attr(e, "tech_categorized")
        raw: list[str]
        if isinstance(categorized, dict) and any(categorized.values()):
            raw = []
            for vals in categorized.values():
                raw.extend(str(v).strip() for v in (vals or []) if str(v).strip())
        else:
            raw = [t.strip() for t in e.tech_stack if t.strip()]
        return [_canonical_tech(t) for t in raw]

    def _aggregate_skill_years(self, engagements: list[EngagementEntity]) -> list[tuple[str, float, int]]:
        """技術ごとに、登場案件の期間を「関与度で重み付け」して実経験年数と案件数を集計する。

        同時期に並行した案件の期間が重複カウントされないよう、技術ごとに月単位で
        「その月の最大関与度(重み)」を取り、重み付き月数を数える(union相当)。
        重みは案件の tech_weights(言語比率等、0.0〜1.0)。未設定の技術は重み1.0(前方互換)。
        さらに manual_skills(git集計に出ない実務利用の指定年数)を最小保証として加算する。

        Returns: [(技術, 年数, 案件数)] を (年数降順, 名前昇順) で。
        """
        # manual_skills で年数指定された技術は「期間フルカウント」の対象外にする。
        # pandas 等のライブラリはコードに大量には書かないので frameworks 由来の
        # 重み1.0で期間フル計上すると過大になる。指定年数を正とする。
        manual_years: dict[str, float] = {}
        for e in engagements:
            for tech, yrs in (getattr(e, "manual_skills", None) or {}).items():
                t = _canonical_tech(tech)
                manual_years[t] = max(manual_years.get(t, 0.0), float(yrs))

        # キャリア全期間(最古開始〜最新終了の連続月数)。基盤技術の年数に使う。
        # 基盤技術は「キャリアを通じて使い続ける」ので案件間の空白も含めた連続期間。
        spans = [s for s in (self._period_span(e) for e in engagements) if s]
        career_months = (max(t for _, t in spans) - min(s for s, _ in spans) + 1) if spans else 0

        # tech -> {月インデックス: その月の最大関与度}
        month_weight: dict[str, dict[int, float]] = {}
        counts: dict[str, int] = {}
        for e in engagements:
            span = self._period_span(e)
            # tech_weights のキーは feed 由来で表記ゆれ(react/vite 等小文字)がある。
            # _all_techs は正規化名(React/Vite)を返すので、重みも正規化キーで引けるようにする。
            # 同じ正規化キーに複数の重みが来たら(例 cypress=0.0 と Cypress=1.0)最大を採る
            # (detected の 1.0 を git言語の低い比率が上書きしないよう順序非依存にする)。
            raw_weights = getattr(e, "tech_weights", None) or {}
            weights: dict[str, float] = {}
            for k, v in raw_weights.items():
                ck = _canonical_tech(k)
                weights[ck] = max(weights.get(ck, 0.0), v)
            for tech in set(self._all_techs(e)):
                if tech in _NON_TECH_TOKENS:  # 設定/環境/雑多ファイル(env/conf 等)は技術でない
                    continue
                counts[tech] = counts.get(tech, 0) + 1
                # 手動年数指定・基盤技術は個別ロジックで年数を出すので期間集計しない。
                if tech in manual_years or tech in _FOUNDATION_TECH or span is None:
                    continue
                w = weights.get(tech, 1.0)  # 重み未設定は1.0(従来どおりフルカウント)
                if w <= 0:
                    continue
                mw = month_weight.setdefault(tech, {})
                for m in range(span[0], span[1] + 1):
                    if w > mw.get(m, 0.0):
                        mw[m] = w

        result: list[tuple[str, float, int]] = []
        all_techs = (set(counts) | set(manual_years)) - _NON_TECH_TOKENS
        for tech in all_techs:
            if tech in manual_years:
                years = manual_years[tech]  # 手動指定の年数を正とする
            elif tech in _FOUNDATION_TECH:
                years = career_months / 12  # 基盤技術はキャリア全期間
            else:
                years = sum(month_weight.get(tech, {}).values()) / 12
            result.append((tech, round(years, 1), counts.get(tech, 0)))
        return sorted(result, key=lambda x: (-x[1], x[0]))

    @staticmethod
    def _period_span(e: EngagementEntity) -> tuple[int, int] | None:
        """案件期間を通し月インデックスの [開始, 終了]（両端含む）で返す。

        period_end 空（現在進行中）は今月まで。start が無ければ None。
        """
        start = _parse_ym(e.period_start)
        if start is None:
            return None
        end = _parse_ym(e.period_end)
        if end is None:
            today = date.today()  # noqa: DTZ011  経過月の概算に用いるためローカル日付で十分
            end = (today.year, today.month)
        s = start[0] * 12 + start[1]
        t = end[0] * 12 + end[1]
        return (s, max(s, t))

    @staticmethod
    def _year_bar(years: float) -> str:
        filled = min(int(round(years)), _SKILL_BAR_MAX_YEARS)
        return "■" * filled + "□" * (_SKILL_BAR_MAX_YEARS - filled)

    # --- 整形ヘルパ ---

    @staticmethod
    def _company_scale(e: EngagementEntity) -> str:
        parts = []
        if e.company_size_employees is not None:
            parts.append(f"従業員約{e.company_size_employees}名")
        if e.dev_org_size is not None:
            parts.append(f"開発約{e.dev_org_size}名")
        return " / ".join(parts)

    @staticmethod
    def _contract_label(e: EngagementEntity) -> str:
        code = ResumePdfService._engagement_attr(e, "contract_type")
        if not code:
            return ""
        return _CONTRACT_LABELS.get(str(code), str(code))

    @staticmethod
    def _period(e: EngagementEntity) -> str:
        if not e.period_start:
            return ""
        end = e.period_end or "現在"
        return f"{e.period_start}〜{end}"

    def _achievement(self, a: AchievementEntity) -> str:
        label = _CATEGORY_LABELS.get(a.category, a.category)
        metric = self._metric_text(a)
        suffix = f"（{escape(metric)}）" if metric else ""
        return f'<div class="ach"><span class="tag">[{escape(label)}]</span> {escape(a.description)}{suffix}</div>'

    @classmethod
    def _metric_text(cls, a: AchievementEntity) -> str:
        before = a.metric_before
        after = a.metric_after
        unit = a.metric_unit or ""
        delta = a.metric_delta_pct
        if before is None and after is None:
            return ""
        text = ""
        if before is not None and after is not None:
            text = f"{cls._num(before)}{unit} → {cls._num(after)}{unit}"
        elif after is not None:
            text = f"{cls._num(after)}{unit}"
        if delta is not None:
            text = f"{text}（{cls._num(delta)}%）" if text else f"{cls._num(delta)}%改善"
        return text

    @staticmethod
    def _num(value: object) -> str:
        """Decimal の末尾ゼロを落として文字列化する。"""
        s = str(value)
        if "." in s:
            s = s.rstrip("0").rstrip(".")
        return s

    # --- profile / engagement の任意属性アクセス（Phase 2/3 追加フィールドに前方互換） ---

    @staticmethod
    def _profile_attr(profile: object | None, name: str) -> str:
        if profile is None:
            return ""
        value = getattr(profile, name, "")
        return str(value) if value else ""

    @staticmethod
    def _profile_list_attr(profile: object | None, name: str) -> list[dict[str, str]]:
        if profile is None:
            return []
        value = getattr(profile, name, None)
        return value if isinstance(value, list) else []

    def _render_ai_usage(self, ai_usage: list[dict[str, str]]) -> str:
        parts: list[str] = []
        # AI駆動開発の取り組み(スキル作成・ルール整備・オーケストレーション設定)を前面に。
        # 今後の注目ポイントであり、単なる「AIを使った」でなく「AIをどう運用する仕組みを
        # 作ったか」を示す差別化要素。プロフィール未入力でも既定の取り組みを表示する。
        works = _AI_DRIVEN_WORKS
        items = "".join(f"<li>{escape(w)}</li>" for w in works)
        parts.append(f'<div class="aiwork"><div class="aititle">AI駆動開発の取り組み</div><ul>{items}</ul></div>')
        # 利用ツールと効果の表。
        if ai_usage:
            rows = ['<table class="data"><tr><th>ツール</th><th>組み込み方</th><th>効果</th></tr>']
            for item in ai_usage:
                tool = escape(str(item.get("tool", "")))
                how = escape(str(item.get("how", "")))
                effect = escape(str(item.get("effect", "")))
                rows.append(f"<tr><td>{tool}</td><td>{how}</td><td>{effect}</td></tr>")
            rows.append("</table>")
            parts.append("".join(rows))
        return "".join(parts)

    @staticmethod
    def _engagement_attr(e: EngagementEntity, name: str) -> object:
        """Phase 2 で追加予定のフィールド（phases/contract_type/tech_categorized/narrative）を
        安全に取得する。未追加の環境でも AttributeError にならないようにする。"""
        return getattr(e, name, None)


def _parse_ym(value: str) -> tuple[int, int] | None:
    """'YYYY-MM' を (year, month) に。不正なら None。"""
    if not value or "-" not in value:
        return None
    try:
        y, m = value.split("-")[:2]
        return int(y), int(m)
    except (ValueError, TypeError):
        return None


def _merged_months(spans: list[tuple[int, int]]) -> int:
    """[開始, 終了]（両端含む・通し月インデックス）の区間群を union して総月数を返す。

    並行案件の期間重複を排除し、実際にその技術に触れていた実月数を数える。
    """
    if not spans:
        return 0
    ordered = sorted(spans)
    total = 0
    cur_s, cur_e = ordered[0]
    for s, e in ordered[1:]:
        if s <= cur_e + 1:  # 連続 or 重複 → 結合（隣接月も繋げる）
            cur_e = max(cur_e, e)
        else:
            total += cur_e - cur_s + 1
            cur_s, cur_e = s, e
    total += cur_e - cur_s + 1
    return total
