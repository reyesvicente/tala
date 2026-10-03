import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";

import type { NewTranscriptionValues } from "./schema";
import type { ServiceInfo, Transcription } from "./types";

export const transcriptionKeys = {
  all: ["transcriptions"] as const,
  info: () => [...transcriptionKeys.all, "info"] as const,
  detail: (slug: string) => [...transcriptionKeys.all, "detail", slug] as const,
};

export function useServiceInfo() {
  return useQuery({
    queryKey: transcriptionKeys.info(),
    queryFn: () => api.get<ServiceInfo>("/info"),
    staleTime: Infinity,
  });
}

export function useTranscription(slug: string) {
  return useQuery({
    queryKey: transcriptionKeys.detail(slug),
    queryFn: () => api.get<Transcription>(`/transcriptions/${encodeURIComponent(slug)}`),
    // Poll while Whisper is working, stop once it's settled.
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "pending" || status === "processing" ? 1500 : false;
    },
  });
}

export function useCreateTranscription() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (values: NewTranscriptionValues) => {
      const form = new FormData();
      form.append("file", values.file);
      form.append("task", values.task);
      if (values.language) form.append("language", values.language);
      return api.postForm<Transcription>("/transcriptions", form);
    },
    onSuccess: (data) => queryClient.setQueryData(transcriptionKeys.detail(data.slug), data),
  });
}

export function useDeleteTranscription() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (slug: string) => api.delete<null>(`/transcriptions/${encodeURIComponent(slug)}`),
    onSuccess: (_, slug) => queryClient.removeQueries({ queryKey: transcriptionKeys.detail(slug) }),
  });
}
