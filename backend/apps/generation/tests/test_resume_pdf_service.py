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

    def test_own_engagement_excluded_from_details_by_default(self) -> None:
        """既定(include_own=False)では自社プロダクトが案件詳細に出ない。"""
        es = [
            EngagementEntity(user_id=1, title="受託案件X", engagement_type="client"),
            EngagementEntity(user_id=1, title="自社プロダクトY", engagement_type="own"),
        ]
        html = _svc()._build_html(es, None, anonymize=False)
        assert "受託案件X" in html
        assert "自社プロダクトY" not in html

    def test_own_engagement_shown_in_details_when_included(self) -> None:
        """include_own=True なら自社プロダクトも案件詳細に載る。"""
        es = [
            EngagementEntity(user_id=1, title="受託案件X", engagement_type="client"),
            EngagementEntity(user_id=1, title="自社プロダクトY", engagement_type="own"),
        ]
        html = _svc()._build_html(es, None, anonymize=False, include_own=True)
        assert "受託案件X" in html
        assert "自社プロダクトY" in html

    def test_unclassified_engagement_kept_in_details(self) -> None:
        """engagement_type 未分類("")は外部参加案件側として残す（誤って消さない）。"""
        es = [EngagementEntity(user_id=1, title="未分類案件Z", engagement_type="")]
        html = _svc()._build_html(es, None, anonymize=False)
        assert "未分類案件Z" in html

    def test_own_engagement_still_counted_in_skill_years(self) -> None:
        """自社プロダクトは案件詳細から外れてもスキル年数には効く。

        この非対称がこの機能の要件そのもの（自己研鑽も経験年数として数える）。
        """
        es = [
            EngagementEntity(
                user_id=1,
                title="受託案件X",
                engagement_type="client",
                period_start="2024-01",
                period_end="2024-06",
                tech_stack=["Python"],
            ),
            EngagementEntity(
                user_id=1,
                title="自社プロダクトY",
                engagement_type="own",
                period_start="2024-01",
                period_end="2024-06",
                tech_stack=["Go"],
            ),
        ]
        html = _svc()._build_html(es, None, anonymize=False)
        # 案件詳細からは消えるが、集計には自社プロダクトの技術が残る。
        assert "自社プロダクトY" not in html
        stats = {t: y for t, y, _ in _svc()._aggregate_skill_years(es)}
        assert "Go" in stats  # 自社プロダクト由来の技術が年数に効いている
        assert "Python" in stats
        # ヒーローの主要スキルチップにも出る（チップはカテゴリ白リストを通さない）。
        assert "Go" in html

    def test_own_engagement_versions_kept_in_skill_matrix(self) -> None:
        """自社プロダクトのバージョン表記もスキル欄には残る。"""
        e = EngagementEntity(
            user_id=1,
            title="自社プロダクトY",
            engagement_type="own",
            period_start="2024-01",
            period_end="2024-06",
            tech_stack=["Laravel"],
            tech_versions={"Laravel": "11.0"},
        )
        assert _svc()._skill_version_ranges([e]).get("Laravel") == "11.0"
        html = _svc()._build_html([e], None, anonymize=False)
        assert "11.0" in html

    def test_details_empty_when_all_engagements_are_own(self) -> None:
        """全件が自社プロダクトなら案件詳細は空メッセージになる（スキル欄は残る）。"""
        es = [
            EngagementEntity(
                user_id=1,
                title="自社プロダクトY",
                engagement_type="own",
                period_start="2024-01",
                period_end="2024-06",
                tech_stack=["Python"],
            )
        ]
        html = _svc()._build_html(es, None, anonymize=False)
        assert "対象の案件がありません" in html
        assert "Python" in html

    def test_note_shown_when_own_omitted(self) -> None:
        """自社プロダクトを実際に外したときはスキル欄に注記が出る。"""
        es = [
            EngagementEntity(user_id=1, title="受託案件X", engagement_type="client"),
            EngagementEntity(user_id=1, title="自社プロダクトY", engagement_type="own"),
        ]
        html = _svc()._build_html(es, None, anonymize=False)
        assert "※年数・件数は自社プロダクトを含む" in html
        assert "案件詳細は外部参加案件のみ記載" in html

    def test_note_hidden_when_own_included(self) -> None:
        """include_own=True なら除外が起きないので注記を出さない。"""
        es = [
            EngagementEntity(user_id=1, title="受託案件X", engagement_type="client"),
            EngagementEntity(user_id=1, title="自社プロダクトY", engagement_type="own"),
        ]
        html = _svc()._build_html(es, None, anonymize=False, include_own=True)
        assert "※年数・件数は自社プロダクトを含む" not in html

    def test_note_hidden_when_no_own_engagements(self) -> None:
        """自社プロダクトが1件も無ければ、既定でも注記は出さない（事実と合わないため）。"""
        es = [EngagementEntity(user_id=1, title="受託案件X", engagement_type="client")]
        html = _svc()._build_html(es, None, anonymize=False)
        assert "※年数・件数は自社プロダクトを含む" not in html

    def test_title_equal_to_company_is_masked(self) -> None:
        """案件名が企業名そのもの（[inv] 取込）でも実名が漏れない。"""
        e = EngagementEntity(
            user_id=1, title="[inv] 秘密株式会社", industry="製造業", company_name="秘密株式会社"
        )
        html = _svc()._render_engagement(e, 3, anonymize=True)
        assert "秘密株式会社" not in html
        assert "案件3：製造業" in html

    def test_title_containing_company_is_masked(self) -> None:
        """案件名に企業名が含まれる場合も見出しから落とす（部分一致）。"""
        e = EngagementEntity(
            user_id=1, title="[inv] 秘密株式会社の基幹刷新", industry="製造業", company_name="秘密株式会社"
        )
        html = _svc()._render_engagement(e, 4, anonymize=True)
        assert "秘密株式会社" not in html

    def test_title_masks_client_and_sier_names(self) -> None:
        """client / sier の実名が案件名に入っていても伏せる。"""
        e = EngagementEntity(
            user_id=1, title="[inv] ナイショ商事の案件", industry="小売業", client="ナイショ商事"
        )
        assert "ナイショ商事" not in _svc()._render_engagement(e, 1, anonymize=True)
        e2 = EngagementEntity(
            user_id=1, title="[inv] ヒミツSIerの案件", industry="小売業", sier="ヒミツSIer"
        )
        assert "ヒミツSIer" not in _svc()._render_engagement(e2, 1, anonymize=True)

    def test_harmless_title_kept_when_masked(self) -> None:
        """実名を含まない案件名は、匿名化時も見出しとして残す（伏せすぎない）。"""
        e = EngagementEntity(
            user_id=1, title="[inv] 在庫管理システム刷新", industry="製造業", company_name="秘密株式会社"
        )
        html = _svc()._render_engagement(e, 1, anonymize=True)
        assert "在庫管理システム刷新" in html
        assert "秘密株式会社" not in html

    def test_is_public_forces_mask_even_when_slider_off(self) -> None:
        """is_public=True（公開向け）はスライダーOFFでも実名を出さない。"""
        e = EngagementEntity(
            user_id=1, title="[inv] 案件名", industry="保険業", company_name="出さない会社", is_public=True
        )
        html = _svc()._render_engagement(e, 1, anonymize=False)
        assert "出さない会社" not in html

    def test_go_and_ruby_rendered_in_skill_matrix(self) -> None:
        """自社プロダクト由来の Go / Ruby / Rails がスキル表に出る。"""
        es = [
            EngagementEntity(
                user_id=1, title="A", engagement_type="own",
                period_start="2024-01", period_end="2024-06",
                tech_stack=["Go", "Ruby", "Rails"],
            )
        ]
        html = _svc()._render_skill_matrix(es)
        assert "Go" in html
        assert "Ruby" in html
        assert "Rails" in html

    def test_hcl_is_folded_into_terraform(self) -> None:
        """HCL は Terraform に名寄せし、同じスキルが2行に割れないようにする。"""
        from apps.generation.application.services.resume_pdf_service import _canonical_tech

        assert _canonical_tech("HCL") == "Terraform"
        # Terraform は基盤技術(union×0.6)なので、表示下限(0.5年)を超える期間を与える。
        es = [
            EngagementEntity(
                user_id=1, title="A", period_start="2022-01", period_end="2023-12",
                tech_stack=["HCL", "Terraform"],
            )
        ]
        stats = [t for t, _y, _c in _svc()._aggregate_skill_years(es)]
        assert stats.count("Terraform") == 1  # HCL と別行に割れない
        assert "HCL" not in stats

    def test_static_analysis_tools_rendered(self) -> None:
        """静的解析(PHPStan/deptrac/packwerk)がスキル表に出る。"""
        es = [
            EngagementEntity(
                user_id=1, title="A", engagement_type="own",
                period_start="2024-01", period_end="2024-06",
                tech_stack=["PHPStan", "deptrac", "packwerk"],
            )
        ]
        html = _svc()._render_skill_matrix(es)
        assert "PHPStan" in html
        assert "deptrac" in html
        assert "packwerk" in html

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
        # 非匿名時の見出しは「企業名 / 案件名」（_display_title の仕様）。
        assert '<span class="etitle">公開OK株式会社 / 公開OK案件</span>' in html
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
        """tech_weights(関与度)を期間に掛ける。重み0.5なら年数は半分。

        重み 1.0 は git 実測ではなく detected(存在検出)を意味するため、
        _DETECTED_RATIO で割り引く（1.0 のまま計上すると Redis 等の
        「使っただけ」の技術が主力言語と同じ年数になる）。
        """
        # PHP/Laravel は主力技術(_CORE_TECH)で割引対象外のため、非主力の Vue で検証する。
        e = EngagementEntity(
            user_id=1, title="A", period_start="2022-01", period_end="2023-12", tech_stack=["Vue", "Python"]
        )
        e.tech_weights = {"Vue": 1.0, "Python": 0.5}
        stats = {s[0]: s[1] for s in _svc()._aggregate_skill_years([e])}
        # 24ヶ月=2.0年。Vue=detected(1.0)→2.0×0.4=0.8年、Python=実測0.5→1.0年
        assert stats["Vue"] == 0.8
        assert stats["Python"] == 1.0

    def test_core_tech_not_discounted(self) -> None:
        """主力技術(PHP/Laravel)は detected 係数で割り引かず案件期間そのものを出す。

        Laravel は 2017-09 以降ほぼ切れ目なく案件が続く主力なので、
        「検出されただけ」の Redis と同じ係数で割ると実態から大きく外れる。
        """
        e = EngagementEntity(
            user_id=1, title="A", period_start="2020-01", period_end="2023-12",
            tech_stack=["Laravel", "Redis"],
        )
        e.tech_weights = {"Laravel": 1.0, "Redis": 1.0}
        stats = {s[0]: s[1] for s in _svc()._aggregate_skill_years([e])}
        assert stats["Laravel"] == 4.0  # 48ヶ月フル（割り引かない）
        assert stats["Redis"] == 1.6  # 48ヶ月 × 0.4

    def test_core_tech_not_capped_by_manual_skills(self) -> None:
        """主力技術は manual_skills による頭打ちを受けない。

        PHP は案件ごとに 1.5/0.3 等の manual_skills が入っているが、これは
        案件単位の値なので、これで全体年数が削られると 8.8年 が 1.5年 になる。
        """
        es = [
            EngagementEntity(
                user_id=1, title="A", period_start="2018-01", period_end="2021-12", tech_stack=["PHP"]
            ),
            EngagementEntity(
                user_id=1, title="B", period_start="2022-01", period_end="2023-12", tech_stack=["PHP"]
            ),
        ]
        es[0].manual_skills = {"PHP": 1.5}
        stats = {s[0]: s[1] for s in _svc()._aggregate_skill_years(es)}
        assert stats["PHP"] == 6.0  # 2018-01〜2023-12 の72ヶ月フル

    def test_detected_weight_discounted_vs_measured(self) -> None:
        """同じ期間でも detected(1.0) は git 実測(0.9)より低く出る。

        「使った事実」より「実際に書いた量」を優先する、という年数モデルの意図。
        """
        e = EngagementEntity(
            user_id=1, title="A", period_start="2020-01", period_end="2023-12", tech_stack=["Redis", "PHP"]
        )
        e.tech_weights = {"Redis": 1.0, "PHP": 0.9}
        stats = {s[0]: s[1] for s in _svc()._aggregate_skill_years([e])}
        assert stats["PHP"] > stats["Redis"]

    def test_ci_and_iac_treated_as_foundation(self) -> None:
        """GitHub Actions/Terraform は「最初に組んで以降触らない」ので基盤技術扱い。"""
        from apps.generation.application.services.resume_pdf_service import _FOUNDATION_TECH

        assert "GitHub Actions" in _FOUNDATION_TECH
        assert "Terraform" in _FOUNDATION_TECH
        assert "Swagger" in _FOUNDATION_TECH
        e = EngagementEntity(
            user_id=1, title="A", period_start="2020-01", period_end="2023-12",
            tech_stack=["GitHub Actions"],
        )
        e.tech_weights = {"GitHub Actions": 1.0}
        stats = {s[0]: s[1] for s in _svc()._aggregate_skill_years([e])}
        # 48ヶ月(4.0年) × 0.6 = 2.4年。detected 係数ではなく基盤係数が適用される。
        assert stats["GitHub Actions"] == 2.4

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

    def test_foundation_tech_uses_used_engagements_not_career(self) -> None:
        """基盤技術は「使った案件の期間 union × 係数」。行数重みには従わない。

        旧実装はキャリア全期間フルカウントで、Docker を使っていない案件の期間まで
        算入していた（Nginx 10.2年 等の過大評価）。Dockerfile は案件開始時に書いて
        以降ほぼ触らないため、使った案件の期間にも係数を掛けて実態に寄せる。
        """
        es = [
            EngagementEntity(
                user_id=1, title="A", period_start="2020-01", period_end="2021-12", tech_stack=["Docker"]
            ),
            EngagementEntity(user_id=1, title="B", period_start="2023-01", period_end="2023-12", tech_stack=["PHP"]),
        ]
        # 重み0.001でも基盤技術なので重みは無視される。
        es[0].tech_weights = {"Docker": 0.001}
        stats = {s[0]: s[1] for s in _svc()._aggregate_skill_years(es)}
        # 案件Aの24ヶ月(2.0年) × 係数0.6 = 1.2年。案件B(Docker未使用)の期間は入らない。
        assert stats["Docker"] == 1.2

    def test_low_year_skills_hidden(self) -> None:
        """0.5年未満の技術はスキル表に出さない（0.0年の空バー行を作らない）。"""
        es = [
            EngagementEntity(
                user_id=1, title="A", period_start="2024-01", period_end="2024-02", tech_stack=["Go"]
            )
        ]
        stats = {s[0]: s[1] for s in _svc()._aggregate_skill_years(es)}
        assert "Go" not in stats  # 2ヶ月=0.2年なので非表示

    def test_manual_skills_sum_across_engagements(self) -> None:
        """同一技術が複数案件にあるとき、manual_skills は案件ごとに合算される。

        旧実装は max() で最大の1案件分しか採らず、23案件やった PHP が 1.5年 に
        なるという過少評価だった。
        """
        # 主力技術(PHP/Laravel)は manual_skills の頭打ちを受けないため、Python で検証する。
        es = [
            EngagementEntity(
                user_id=1, title="A", period_start="2020-01", period_end="2021-12", tech_stack=["Python"]
            ),
            EngagementEntity(
                user_id=1, title="B", period_start="2022-01", period_end="2023-12", tech_stack=["Python"]
            ),
        ]
        es[0].manual_skills = {"Python": 1.0}
        es[1].manual_skills = {"Python": 1.0}
        stats = {s[0]: s[1] for s in _svc()._aggregate_skill_years(es)}
        assert stats["Python"] == 2.0  # max(1.0) ではなく合算

    def test_manual_skills_not_double_counted_on_overlap(self) -> None:
        """期間が重なる案件の manual_skills は union なので二重に数えない。"""
        es = [
            EngagementEntity(
                user_id=1, title="A", period_start="2024-01", period_end="2024-12", tech_stack=["Python"]
            ),
            EngagementEntity(
                user_id=1, title="B", period_start="2024-01", period_end="2024-12", tech_stack=["Python"]
            ),
        ]
        es[0].manual_skills = {"Python": 1.0}
        es[1].manual_skills = {"Python": 1.0}
        stats = {s[0]: s[1] for s in _svc()._aggregate_skill_years(es)}
        assert stats["Python"] == 1.0  # 同一期間なので合算されない

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
