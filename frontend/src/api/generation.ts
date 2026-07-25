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
};
