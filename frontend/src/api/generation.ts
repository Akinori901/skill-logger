import type { AiConfig, DomainStatement } from "../types/careers";
import { apiClient } from "./client";

export const generationApi = {
  getAiConfig: async (): Promise<AiConfig> => {
    const { data } = await apiClient.get("/generation/ai-config/");
    return data;
  },
  saveAiConfig: async (payload: AiConfig): Promise<AiConfig> => {
    const { data } = await apiClient.put("/generation/ai-config/", payload);
    return data;
  },
  generateAll: async (domainCodes: string[]): Promise<DomainStatement[]> => {
    const { data } = await apiClient.post("/generation/statements/generate-all/", {
      domain_codes: domainCodes,
    });
    return data;
  },
  listStatements: async (): Promise<DomainStatement[]> => {
    const { data } = await apiClient.get("/generation/statements/");
    return data;
  },
  saveStatement: async (payload: DomainStatement): Promise<DomainStatement> => {
    const { data } = await apiClient.post("/generation/statements/", payload);
    return data;
  },
  exportMarkdown: async (ids?: number[]): Promise<string> => {
    const params = ids && ids.length ? { ids: ids.join(",") } : undefined;
    const { data } = await apiClient.get("/generation/engagements/markdown/", { params });
    return data.markdown;
  },
  /** 職務経歴書＋スキルシートを1つのPDFとして取得する（バイナリ）。
   * anonymize=true（既定）で企業名を伏せ、業界＋規模で代替する。
   * hideName=true で氏名を伏せる（anonymize とは独立。片方だけ伏せることもできる）。
   * includeOwn=false（既定）で自社プロダクトを案件詳細から外し、外部参加案件だけ載せる。
   * スキル年数・主要スキルチップ・バージョン表記は includeOwn に関わらず常に全案件から集計する。 */
  exportPdf: async (
    ids?: number[],
    anonymize = true,
    hideName = false,
    includeOwn = false,
  ): Promise<Blob> => {
    const params: Record<string, string> = {
      anonymize: String(anonymize),
      hide_name: String(hideName),
      include_own: String(includeOwn),
    };
    if (ids && ids.length) params.ids = ids.join(",");
    const { data } = await apiClient.get("/generation/engagements/pdf/", {
      params,
      responseType: "blob",
    });
    return data;
  },
  /** プロフィールの作文（職務要約/自己PR/AI効果）を Gemini で生成する。 */
  generateProfileNarrative: async (
    kind: "summary" | "strengths" | "good_at" | "ai_effect",
    persist = false,
  ): Promise<string> => {
    const { data } = await apiClient.post("/generation/profile/narrative/", { kind, persist });
    return data.text;
  },
  /** 案件の実績・取り組み文を Gemini で生成する。 */
  generateEngagementNarrative: async (engagementId: number, persist = false): Promise<string> => {
    const { data } = await apiClient.post(
      `/generation/engagements/${engagementId}/narrative/`,
      { persist },
    );
    return data.text;
  },
  /** 案件の単一フィールド（業界/概要/実績）を Gemini で生成する。
   * only_if_empty=true で既存値があるフィールドはスキップ（一括自動埋め用）。 */
  generateEngagementField: async (
    engagementId: number,
    field: "industry" | "overview" | "narrative" | "responsibilities" | "challenges" | "position",
    opts: { persist?: boolean; onlyIfEmpty?: boolean } = {},
  ): Promise<string> => {
    const { data } = await apiClient.post(`/generation/engagements/${engagementId}/field/`, {
      field,
      persist: opts.persist ?? false,
      only_if_empty: opts.onlyIfEmpty ?? false,
    });
    return data.text;
  },
};
