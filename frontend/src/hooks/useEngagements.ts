import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { careersApi, supportDomainsApi } from "../api/careers";
import type { Engagement } from "../types/careers";

export const useEngagements = () =>
  useQuery({ queryKey: ["engagements"], queryFn: careersApi.list });

export const useSupportDomains = () =>
  useQuery({ queryKey: ["support-domains"], queryFn: supportDomainsApi.list });

export const useSaveEngagement = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: Engagement) =>
      payload.id ? careersApi.update(payload.id, payload) : careersApi.create(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["engagements"] }),
  });
};

export const useDeleteEngagement = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => careersApi.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["engagements"] }),
  });
};
