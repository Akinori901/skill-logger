import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { generationApi } from "../api/generation";
import type { AiConfig, DomainStatement } from "../types/careers";

export const useAiConfig = () =>
  useQuery({ queryKey: ["ai-config"], queryFn: generationApi.getAiConfig });

export const useSaveAiConfig = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: AiConfig) => generationApi.saveAiConfig(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["ai-config"] }),
  });
};

export const useStatements = () =>
  useQuery({ queryKey: ["statements"], queryFn: generationApi.listStatements });

export const useGenerateAll = () =>
  useMutation({ mutationFn: (codes: string[]) => generationApi.generateAll(codes) });

export const useSaveStatement = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: DomainStatement) => generationApi.saveStatement(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["statements"] }),
  });
};
