export type AchievementCategory =
  | "speed"
  | "cost"
  | "quality"
  | "ops"
  | "incident"
  | "release"
  | "review";

export const ACHIEVEMENT_CATEGORY_LABELS: Record<AchievementCategory, string> = {
  speed: "速度改善",
  cost: "コスト削減",
  quality: "品質向上",
  ops: "運用改善",
  incident: "障害削減",
  release: "リリース改善",
  review: "レビュー体制改善",
};

export interface Achievement {
  id?: number | null;
  category: AchievementCategory;
  description: string;
  metric_before?: string | null;
  metric_after?: string | null;
  metric_unit?: string;
  metric_delta_pct?: string | null;
}

export interface EngagementUrl {
  id?: number | null;
  url: string;
  label?: string;
}

export interface EngagementDomainLink {
  id?: number | null;
  support_domain_id: number;
  relevance: number;
}

export interface Engagement {
  id?: number | null;
  title: string;
  industry?: string;
  company_name?: string;
  company_size_employees?: number | null;
  dev_org_size?: number | null;
  period_start?: string;
  period_end?: string;
  position?: string;
  overview?: string;
  responsibilities?: string;
  tech_stack?: string[];
  challenges?: string;
  phases?: string[];
  contract_type?: string;
  tech_categorized?: Record<string, string[]>;
  narrative?: string;
  is_public?: boolean;
  display_order?: number;
  achievements?: Achievement[];
  urls?: EngagementUrl[];
  domain_links?: EngagementDomainLink[];
  created_at?: string;
  updated_at?: string;
}

export interface AiUsageItem {
  tool: string;
  how: string;
  effect: string;
}

/** 職務経歴書サマリ（ユーザー単位のプロフィール）。 */
export interface UserProfile {
  display_name?: string;
  age_range?: string;
  residence?: string;
  headline?: string;
  summary?: string;
  strengths?: string;
  good_at?: string;
  ai_usage?: AiUsageItem[];
  created_at?: string;
  updated_at?: string;
}

/** 担当工程（コード→表示ラベル）。バックエンド ENGAGEMENT_PHASES と対応。 */
export const ENGAGEMENT_PHASES: { code: string; label: string }[] = [
  { code: "req", label: "要件定義" },
  { code: "basic", label: "基本設計" },
  { code: "detail", label: "詳細設計" },
  { code: "backend", label: "Back実装" },
  { code: "frontend", label: "Front実装" },
  { code: "test", label: "テスト" },
  { code: "research", label: "調査" },
  { code: "refactor", label: "リファクタ" },
];

/** 雇用形態（コード→表示ラベル）。バックエンド CONTRACT_TYPES と対応。 */
export const CONTRACT_TYPES: { code: string; label: string }[] = [
  { code: "contract", label: "請負" },
  { code: "quasi", label: "準委任" },
  { code: "dispatch", label: "派遣" },
];

/** 技術の種別（tech_categorized のキー→表示ラベル）。バックエンド TECH_CATEGORIES と対応。 */
export const TECH_CATEGORIES: { code: string; label: string }[] = [
  { code: "language", label: "言語" },
  { code: "db", label: "DB" },
  { code: "framework", label: "フレームワーク" },
  { code: "cloud", label: "クラウド" },
  { code: "tool", label: "ツール" },
];

export interface SupportDomain {
  id: number;
  code: string;
  name: string;
  display_order: number;
}

export interface DomainStatement {
  id?: number | null;
  support_domain_id: number;
  priority: number;
  body: string;
  char_count?: number;
  source_engagement_ids?: number[];
  ai_model?: string;
  generated_at?: string;
  updated_at?: string;
}

export interface AiConfig {
  provider: "gemini" | "claude" | "openai";
  model: string;
  is_enabled: boolean;
  has_api_key?: boolean;
  api_key?: string;
}
