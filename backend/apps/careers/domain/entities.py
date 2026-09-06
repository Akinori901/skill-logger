"""棚卸し（業務経歴）ドメインエンティティ。

Django ORM / DRF に依存しない純粋なデータ構造（クリーンアーキの domain 層規約）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime
    from decimal import Decimal


# 成果カテゴリ（Expert 申請の成果軸）
ACHIEVEMENT_CATEGORIES = (
    "speed",  # 速度改善
    "cost",  # コスト削減
    "quality",  # 品質向上
    "ops",  # 運用改善
    "incident",  # 障害削減
    "release",  # リリース改善
    "review",  # レビュー体制改善
)

# 担当工程（案件で担当した開発フェーズ。職務経歴書の「担当工程」に対応）
ENGAGEMENT_PHASES = (
    "req",  # 要件定義
    "basic",  # 基本設計
    "detail",  # 詳細設計
    "backend",  # Back実装
    "frontend",  # Front実装
    "test",  # テスト
    "research",  # 調査
    "refactor",  # リファクタ
)

# 雇用形態（契約種別）
CONTRACT_TYPES = (
    "contract",  # 請負
    "quasi",  # 準委任
    "dispatch",  # 派遣
)

# 技術の種別（tech_categorized のキー）
TECH_CATEGORIES = (
    "language",  # 言語
    "db",  # DB
    "framework",  # フレームワーク
    "cloud",  # クラウド
    "tool",  # ツール
)


@dataclass
class AchievementEntity:
    """成果（数字付き構造）。

    metric_before/after/unit を持つことで、生成文に定量値を差し込める。
    """

    category: str  # ACHIEVEMENT_CATEGORIES のいずれか
    description: str
    metric_before: Decimal | None = None
    metric_after: Decimal | None = None
    metric_unit: str = ""
    metric_delta_pct: Decimal | None = None
    id: int | None = None


@dataclass
class EngagementUrlEntity:
    """実績URL。"""

    url: str
    label: str = ""
    # URL の種別。"repo"=公開リポ（private 案件の public への道）、""=汎用の実績URL。
    # 記事の GitHub 動線フッターは kind=="repo" の url を引く。空は従来どおりの実績URL。
    kind: str = ""
    id: int | None = None


@dataclass
class EngagementDomainLink:
    """案件と支援領域の紐付け（寄与度つき）。"""

    support_domain_id: int
    relevance: int = 3  # 1-5、その領域への寄与度
    id: int | None = None


@dataclass
class EngagementEntity:
    """案件（棚卸しの主エンティティ）。"""

    user_id: int
    title: str
    industry: str = ""
    company_name: str = ""
    client: str = ""   # 案件先（end）
    agent: str = ""    # 紹介元エージェント
    sier: str = ""     # 実装元SIer
    company_size_employees: int | None = None
    dev_org_size: int | None = None
    period_start: str = ""  # YYYY-MM
    period_end: str = ""  # YYYY-MM（空=現在）
    position: str = ""
    overview: str = ""
    responsibilities: str = ""
    tech_stack: list[str] = field(default_factory=list)
    challenges: str = ""
    # 担当した開発工程（ENGAGEMENT_PHASES のコード配列）
    phases: list[str] = field(default_factory=list)
    # 雇用形態（CONTRACT_TYPES のいずれか。未設定は空）
    contract_type: str = ""
    # 技術の種別分離（TECH_CATEGORIES をキーとする配列 dict）。
    # 既存 tech_stack(flat) は温存し、集計/PDF は categorized 優先→flat フォールバック。
    tech_categorized: dict[str, list[str]] = field(default_factory=dict)
    # 技術ごとの関与度の重み（技術名→0.0〜1.0）。skill-inventory の言語比率(pct)や
    # フレームワークの主要度から算出し、スキル経験年数の集計で期間に掛ける。
    # 空 dict の技術は重み1.0扱い（前方互換: 未設定の既存案件は従来どおりフルカウント）。
    tech_weights: dict[str, float] = field(default_factory=dict)
    # git集計に出ない実務技術の手動補完（技術名→年数）。pandas 等のライブラリ的利用は
    # コミット行に現れず言語集計で0になるため、実務利用年数を最小保証として加算する。
    manual_skills: dict[str, float] = field(default_factory=dict)
    # 案件で使った技術のバージョン（技術名→版）。「Laravel 8.12」等を案件詳細に出す。
    tech_versions: dict[str, str] = field(default_factory=dict)
    # 採用したアーキテクチャ構造（案件詳細に層図を出す）。
    # 形式: {"name": "クリーンアーキテクチャ（4層・DDD志向）",
    #        "layers": ["Presentation", "Application（UseCase）", "Domain（Entities）", "Infrastructure"]}
    # 空 dict の案件は層図を出さない。リポ構造で採用実態を確認したものだけ付与する。
    architecture: dict[str, object] = field(default_factory=dict)
    # 実績・取り組みの作文（Gemini 生成 or 手入力）。事実の responsibilities とは別。
    narrative: str = ""
    # 案件レジストリの共通キー（skill-inventory の ledger/projects.yaml の key）。
    # Publicity の projects.yaml / redaction/<key>.yaml / jobs.projectKey と同一語彙で紐づく。
    # 空＝記事化対象でない案件。実ローカルパスはここには持たない（Publicity ローカルにのみ）。
    project_key: str = ""
    # 稼働中フラグ。週次ネタ収穫(Publicity weekly_harvest)が is_active な案件だけを
    # 収穫対象にする。過去案件(外付けSSD等)を除外し「今動いている案件」に絞るため。
    is_active: bool = False
    # 記事化のために読む「ローカルのコード配置パス」。Publicity worker が
    # project_key でこの案件を解決するとき、この実パスを収穫対象ディレクトリにする。
    # ${PUBLICITY_SSD_ROOT} 等の環境変数を含められる(自宅/事務所のマウント差を吸収)。
    # ※このパスはローカル(利用者のPC/SSD)を指すだけで、DBに載っても第三者はデータ取得不可。
    local_path: str = ""
    # 記事化・スキャンで読むローカルコード配置パスの複数版(1案件が複数リポを持つ)。
    # 空list なら後方互換で単一 local_path を見る。${PUBLICITY_SSD_ROOT} 等の環境変数可。
    local_paths: list[str] = field(default_factory=list)
    is_public: bool = False  # 匿名化制御（public 出力時に企業名を伏せるか。公開可＝匿名前提）
    # 自社プロダクトか受託案件かの区別。"own"=自社リポ（QOL 等・公開リポあり）、
    # "client"=受託案件（匿名化必須）、""=未分類。真実は skill-inventory の
    # ledger decision（as_is→own）にあり、取り込み時にマップする。is_public（匿名化制御）
    # とは別概念なので混同しない。記事化の匿名化ゲート回避や自社リポ実績表示の分岐に使う。
    engagement_type: str = ""
    display_order: int = 0
    achievements: list[AchievementEntity] = field(default_factory=list)
    urls: list[EngagementUrlEntity] = field(default_factory=list)
    domain_links: list[EngagementDomainLink] = field(default_factory=list)
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def resolved_paths(self) -> list[str]:
        """記事化・スキャンで読むローカルパスを一意に返す。
        local_paths(複数) があればそれ、無ければ単一 local_path、両方空なら[]。
        単一 local_path から複数 local_paths への後方互換をここで吸収する。"""
        if self.local_paths:
            return list(self.local_paths)
        return [self.local_path] if self.local_path else []


@dataclass
class SupportDomainEntity:
    """支援領域マスタ（Expert 申請の12領域）。"""

    code: str
    name: str
    display_order: int = 0
    id: int | None = None


@dataclass
class UserProfileEntity:
    """職務経歴書のサマリ（ユーザー単位のプロフィール）。

    事実（display_name/age_range/residence/headline）と、
    作文（summary/strengths/good_at、Gemini 生成 or 手入力）を分けて持つ。
    ai_usage は生成AI活用の記録 [{"tool","how","effect"}]（effect は作文）。
    スキル別経験年数は保持せず、案件の tech × period から都度集計する
    （事実の単一ソースを案件に置き、二重管理を避ける）。
    """

    user_id: int
    # --- 事実（手入力） ---
    display_name: str = ""  # 氏名（PDF 表示名）
    age_range: str = ""  # 年代 "30代" 等（生年は持たない=匿名性）
    residence: str = ""  # 居住地 "東京都" 等
    headline: str = ""  # 希望ポジション/肩書
    # --- 作文（Gemini 生成 or 手入力、編集可） ---
    summary: str = ""  # 職務要約
    strengths: str = ""  # 自己PR: 強み
    good_at: str = ""  # 自己PR: 得意業務
    # --- 生成AI活用（tool/how は事実、effect は作文） ---
    ai_usage: list[dict[str, str]] = field(default_factory=list)  # [{"tool","how","effect"}]
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
