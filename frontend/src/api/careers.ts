import type { Engagement, SupportDomain } from "../types/careers";
import { apiClient } from "./client";

export const careersApi = {
  list: async (): Promise<Engagement[]> => {
    const { data } = await apiClient.get("/careers/engagements/");
    return data;
  },
  get: async (id: number): Promise<Engagement> => {
    const { data } = await apiClient.get(`/careers/engagements/${id}/`);
    return data;
  },
  create: async (payload: Engagement): Promise<Engagement> => {
    const { data } = await apiClient.post("/careers/engagements/", payload);
    return data;
  },
  update: async (id: number, payload: Engagement): Promise<Engagement> => {
    const { data } = await apiClient.put(`/careers/engagements/${id}/`, payload);
    return data;
  },
  remove: async (id: number): Promise<void> => {
    await apiClient.delete(`/careers/engagements/${id}/`);
  },
};

export const supportDomainsApi = {
  list: async (): Promise<SupportDomain[]> => {
    const { data } = await apiClient.get("/careers/support-domains/");
    return data;
  },
};

export interface ImportResult {
  created: string[];
  updated: string[];
  skipped: string[];
  created_count: number;
  updated_count: number;
  skipped_count: number;
}

export const importApi = {
  // feed.json をアップロードして取り込む（dryRun=true でプレビュー）
  upload: async (file: File, onlyDecision: string, dryRun: boolean): Promise<ImportResult> => {
    const form = new FormData();
    form.append("file", file);
    if (onlyDecision) form.append("only_decision", onlyDecision);
    form.append("dry_run", String(dryRun));
    const { data } = await apiClient.post("/careers/import/", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  },
};
