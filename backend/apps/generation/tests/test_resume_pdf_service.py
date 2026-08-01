"""ResumePdfService の HTML 生成ロジックのテスト。

weasyprint(PDF化)はネイティブ依存を要するため、ここでは HTML 組み立て・
技術集計・HTML エスケープ・成果metric整形・匿名化・スキルバーなど
純粋ロジックのみ検証する。実PDF生成の目視検証は Docker(Noto CJK)で実施。
"""

from __future__ import annotations

from decimal import Decimal

from apps.careers.domain.entities import AchievementEntity, EngagementEntity, EngagementUrlEntity
from apps.generation.application.services.resume_pdf_service import ResumePdfService


def _svc() -> ResumePdfService:
    return ResumePdfService()


class TestResumePdfHtml:
    def test_build_html_has_two_zones_no_trailing_skillsheet(self) -> None:
        html = _svc()._build_html([EngagementEntity(user_id=1, title="案件A")], None, anonymize=True)
        assert "スキル・経験" in html  # サマリゾーン
        assert "職務経歴（案件詳細）" in html  # 案件詳細ゾーン
        assert "hero" in html  # ヒーロー(氏名・肩書・リード)
        assert "page-break" in html  # ゾーン間はページ分割
        assert "page-break-inside: avoid" in html  # 案件カードは分断されない
        assert "ecard" in html  # 案件はカード形式

    def test_intro_placeholder_when_no_summary(self) -> None:
        # プロフィール未入力でもヒーロー・スキルが描画され落ちない
        html = _svc()._render_summary([EngagementEntity(user_id=1, title="A")], None)
        assert "スキル・経験" in html

    def test_intro_uses_profile_summary(self) -> None:
        class _P:
            summary = "BEエンジニア歴が長いです。"

        html = _svc()._render_summary([EngagementEntity(user_id=1, title="A")], _P())
        assert "BEエンジニア歴が長いです。" in html

    def test_ai_and_pr_in_summary(self) -> None:
        # AI駆動開発の取り組み・自己PRがサマリに含まれる(順序: スキル→AI→自己PR)
        class _P:
            summary = "要約"
            ai_usage = [{"tool": "Claude Code", "how": "並列指示", "effect": "速度向上"}]
            strengths = "挑戦意欲が高い"
            good_at = "Backend全般"

        html = _svc()._render_summary([EngagementEntity(user_id=1, title="A")], _P())
        assert html.index("スキル・経験") < html.index("AI駆動開発") < html.index("自己PR")
        assert "オーケストレーション" in html  # AI駆動開発の取り組みが明示される

    def test_ai_works_shown_without_profile(self) -> None:
        # プロフィール未入力でもAI駆動開発の取り組みは既定で表示される(差別化要素)
        html = _svc()._render_summary([EngagementEntity(user_id=1, title="A")], None)
        assert "AI駆動開発" in html and "スキル" in html

    def test_skill_matrix_is_two_column(self) -> None:
        es = [
            EngagementEntity(user_id=1, title="A", period_start="2024-01", period_end="2024-06", tech_stack=["Python"]),
            EngagementEntity(user_id=1, title="B", period_start="2024-01", period_end="2024-06", tech_stack=["Go"]),
        ]
        html = _svc()._render_skill_matrix(es)
        assert "skillgrid" in html  # 2列カードレイアウト
        assert "Python" in html
        assert "Go" in html

    def test_skill_matrix_category_cards(self) -> None:
        # カテゴリ別カード(言語等)で表示され、技術と年数が出る
        es = [
            EngagementEntity(user_id=1, title="A", period_start="2024-01", period_end="2024-06", tech_stack=["Python"])
        ]
        html = _svc()._render_skill_matrix(es)
        assert "scard" in html and "scat" in html  # カテゴリカード
        assert "言語" in html  # Python は言語カテゴリ
        assert "Python" in html

    def test_skill_card_renders_bar_and_years(self) -> None:
        # カテゴリカードに技術・バー・年数・件数が出る
        html = _svc()._skill_card("言語", [("Python", 5.0, 3)], {})
        assert "Python" in html
        assert "sbar" in html  # 年数バー
        assert "5.0年" in html
        assert "3件" in html

    def test_engagement_fields_rendered(self) -> None:
        e = EngagementEntity(
            user_id=1,
            title="シフト管理の改善",
            industry="人材サービス業",
            company_size_employees=500,
            dev_org_size=30,
            period_start="2024-04",
            period_end="",
            position="テックリード",
            overview="概要テキスト",
            responsibilities="担当内容",
            tech_stack=["Python", "Django"],
            challenges="苦労した点",
        )
        html = _svc()._render_engagement(e, 1, anonymize=False)
        assert "シフト管理の改善" in html  # anonymize=False なので元タイトル
        assert "2024-04〜現在" in html  # period_end 空 → 現在
        assert "人材サービス業" in html
        assert "従業員約500名 / 開発約30名" in html
        assert "テックリード" in html
        assert "Python" in html and "Django" in html  # 技術タグ
        assert "概要テキスト" in html
        assert "苦労した点" in html

    def test_anonymize_hides_company_name_and_title(self) -> None:
        e = EngagementEntity(
            user_id=1,
            title="[inv] 秘密株式会社",  # skill-inventory 由来のタイトル（企業名入り）
            industry="人材サービス業",
            company_name="秘密株式会社",
        )
        html = _svc()._render_engagement(e, 3, anonymize=True)
        assert "秘密株式会社" not in html  # 会社名もタイトルも伏せる
        assert "案件3：人材サービス業" in html  # 業界ベースの匿名タイトル

    def test_anonymize_title_without_industry(self) -> None:
        e = EngagementEntity(user_id=1, title="[inv] ナイショ社", company_name="ナイショ社")
        html = _svc()._render_engagement(e, 2, anonymize=True)
        assert "ナイショ社" not in html
        assert "案件2" in html

    def test_non_anonymize_shows_company_name_as_title(self) -> None:
        # 非匿名時は企業名(company_name)を見出しに出す。業界はメタ行に。
        e = EngagementEntity(
            user_id=1,
            title="[inv] 公開OK案件",
            industry="人材サービス業",
            company_name="公開OK株式会社",
            is_public=False,
        )
        html = _svc()._render_engagement(e, 1, anonymize=False)
        assert '<span class="etitle">公開OK株式会社</span>' in html  # 見出しは企業名
        assert "[inv]" not in html  # 取込接頭辞は表示しない
        assert "人材サービス業" in html  # 業界はメタ行に出る

    def test_non_anonymize_without_company_falls_back_to_title(self) -> None:
        # 企業名が無い案件は「[inv] 」を除いたタイトルへフォールバック。
        e = EngagementEntity(user_id=1, title="[inv] フォールバック案件", industry="業界")
        html = _svc()._render_engagement(e, 1, anonymize=False)
        assert '<span class="etitle">フォールバック案件</span>' in html
        assert "[inv]" not in html

    def test_public_flag_forces_anonymized_even_when_not_anonymize(self) -> None:
        e = EngagementEntity(
            user_id=1,
            title="[inv] 出さない会社",
            industry="保険業",
            company_name="出さない会社",
            is_public=True,
        )
        html = _svc()._render_engagement(e, 1, anonymize=False)
        assert "出さない会社" not in html
        assert "案件1：保険業" in html

    def test_achievement_metric_formatting(self) -> None:
        e = EngagementEntity(user_id=1, title="A")
        e.achievements = [
            AchievementEntity(
                category="speed",
                description="バッチ短縮",
                metric_before=Decimal("120"),
                metric_after=Decimal("18"),
                metric_unit="分",
                metric_delta_pct=Decimal("85"),
            )
        ]
        html = _svc()._render_engagement(e, 1, anonymize=True)
        assert "[速度改善]" in html
        assert "120分 → 18分" in html
        assert "85%" in html

    def test_html_escaping_prevents_injection(self) -> None:
        e = EngagementEntity(user_id=1, title="<script>alert(1)</script>")
        html = _svc()._render_engagement(e, 1, anonymize=False)
        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_url_rendered_with_label(self) -> None:
        e = EngagementEntity(user_id=1, title="A")
        e.urls = [EngagementUrlEntity(url="https://example.com", label="サービス")]
        html = _svc()._render_engagement(e, 1, anonymize=True)
        assert "サービス: https://example.com" in html

    def test_skill_years_aggregation_and_bar(self) -> None:
        es = [
            EngagementEntity(user_id=1, title="A", period_start="2024-01", period_end="2024-06", tech_stack=["Python"]),
            EngagementEntity(user_id=1, title="B", period_start="2024-07", period_end="2025-01", tech_stack=["Python"]),
        ]
        stats = _svc()._aggregate_skill_years(es)
        assert stats[0][0] == "Python"
        assert stats[0][2] == 2  # 案件数
        html = _svc()._render_skill_matrix(es)
        assert "sbar" in html  # 経験年数バー

    def test_details_empty_message(self) -> None:
        html = _svc()._render_details([], anonymize=True)
        assert "対象の案件がありません" in html

    def test_tech_name_canonicalization(self) -> None:
        # Vue と vue、React と react が名寄せされ1つに集約される
        es = [
            EngagementEntity(
                user_id=1, title="A", period_start="2024-01", period_end="2024-06", tech_stack=["Vue", "React"]
            ),
            EngagementEntity(
                user_id=1, title="B", period_start="2024-07", period_end="2024-12", tech_stack=["vue", "react"]
            ),
        ]
        stats = _svc()._aggregate_skill_years(es)
        techs = {s[0]: s for s in stats}
        assert "Vue" in techs
        assert "vue" not in techs  # 小文字は Vue に統合
        assert techs["Vue"][2] == 2  # 2案件に集約

    def test_skill_years_applies_tech_weights(self) -> None:
        # tech_weights(関与度)を期間に掛ける。重み0.5なら年数は半分。
        e = EngagementEntity(
            user_id=1, title="A", period_start="2022-01", period_end="2023-12", tech_stack=["PHP", "Python"]
        )
        e.tech_weights = {"PHP": 1.0, "Python": 0.5}
        stats = {s[0]: s[1] for s in _svc()._aggregate_skill_years([e])}
        # 24ヶ月=2.0年。PHP=重み1.0→2.0年、Python=重み0.5→1.0年
        assert stats["PHP"] == 2.0
        assert stats["Python"] == 1.0

    def test_skill_years_weight_unset_is_full(self) -> None:
        # tech_weights 未設定の技術は重み1.0(前方互換: 従来どおりフルカウント)
        e = EngagementEntity(user_id=1, title="A", period_start="2022-01", period_end="2022-12", tech_stack=["Go"])
        stats = {s[0]: s[1] for s in _svc()._aggregate_skill_years([e])}
        assert stats["Go"] == 1.0  # 12ヶ月=1.0年、重み未設定=1.0

    def test_manual_skills_floor(self) -> None:
        # manual_skills は最小保証。git由来が0でも指定年数を出す。
        e = EngagementEntity(user_id=1, title="A", period_start="2022-01", period_end="2022-06")
        e.manual_skills = {"pandas": 0.5}
        stats = {s[0]: s[1] for s in _svc()._aggregate_skill_years([e])}
        assert stats["pandas"] == 0.5

    def test_foundation_tech_spans_career(self) -> None:
        # 基盤技術(Docker/SQL等)は行数でなくキャリア全期間で年数を出す。
        es = [
            EngagementEntity(user_id=1, title="A", period_start="2020-01", period_end="2020-12", tech_stack=["Docker"]),
            EngagementEntity(user_id=1, title="B", period_start="2023-01", period_end="2023-12", tech_stack=["PHP"]),
        ]
        # Docker は重み0.001でも、基盤技術なのでキャリア全期間(2020-01〜2023-12=48ヶ月=4.0年)
        es[0].tech_weights = {"Docker": 0.001}
        stats = {s[0]: s[1] for s in _svc()._aggregate_skill_years(es)}
        assert stats["Docker"] == 4.0  # 行数重みでなくキャリア全期間

    def test_non_tech_extensions_excluded(self) -> None:
        # env/conf/pem 等の設定・雑多ファイルはスキルに出さない。
        e = EngagementEntity(
            user_id=1,
            title="A",
            period_start="2022-01",
            period_end="2022-12",
            tech_stack=["PHP", "env", "conf", "pem", "neon"],
        )
        techs = {s[0] for s in _svc()._aggregate_skill_years([e])}
        assert "PHP" in techs
        assert "env" not in techs
        assert "conf" not in techs
        assert "pem" not in techs
        assert "neon" not in techs

    def test_manual_skills_override_period(self) -> None:
        # manual_skills 指定技術は「指定年数を正」とし期間フルカウントしない。
        # pandas 等は frameworks 由来で重み1.0になりがちだがコードに大量には書かない
        # ため、指定年数(実務利用の実感)を採用する。
        e = EngagementEntity(user_id=1, title="A", period_start="2020-01", period_end="2023-12", tech_stack=["pandas"])
        e.tech_weights = {"pandas": 1.0}  # frameworks由来の誤った重み
        e.manual_skills = {"pandas": 0.5}
        stats = {s[0]: s[1] for s in _svc()._aggregate_skill_years([e])}
        assert stats["pandas"] == 0.5  # 48ヶ月フル(4.0年)でなく指定0.5年

    def test_skill_years_merges_overlapping_periods(self) -> None:
        # 同一技術が期間の重なる2案件に登場 → 重複を排除して実月数で計算
        es = [
            EngagementEntity(user_id=1, title="A", period_start="2024-01", period_end="2024-12", tech_stack=["Python"]),
            EngagementEntity(user_id=1, title="B", period_start="2024-06", period_end="2025-05", tech_stack=["Python"]),
        ]
        stats = _svc()._aggregate_skill_years(es)
        # 2024-01〜2025-05 = 17ヶ月（重複2024-06〜12を二重計上しない）→ 約1.4年
        # 単純合算なら 12+12=24ヶ月=2.0年 になるはず。マージで小さくなることを確認
        years = stats[0][1]
        assert years < 1.6  # 約1.4年（単純合算2.0年より小さい）
        assert stats[0][2] == 2
