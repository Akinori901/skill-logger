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
  is_public?: boolean;
  display_order?: number;
  achievements?: Achievement[];
  urls?: EngagementUrl[];
  domain_links?: EngagementDomainLink[];
  created_at?: string;
  updated_at?: string;
}

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
