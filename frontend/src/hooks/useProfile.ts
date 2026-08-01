import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { profileApi } from "../api/careers";
import type { UserProfile } from "../types/careers";

export const useProfile = () =>
  useQuery({ queryKey: ["profile"], queryFn: profileApi.get });

export const useSaveProfile = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: UserProfile) => profileApi.save(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["profile"] }),
  });
};
