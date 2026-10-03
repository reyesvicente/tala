import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, isTransient } from "@/lib/api";

import type { NewTranscriptionValues } from "./schema";
import type { Page, ServiceInfo, Transcription, TranscriptionSummary } from "./types";

export const transcriptionKeys = {
  all: ["transcriptions"] as const,
  info: () => [...transcriptionKeys.all, "info"] as const,
  detail: (slug: string) => [...transcriptionKeys.all, "detail", slug] as const,
  history: (page: number, query: string) => [...transcriptionKeys.all, "history", page, query] as const,
};

export function useHistory(page: number, query: string) {
  return useQuery({
    queryKey: transcriptionKeys.history(page, query),
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page), page_size: "20" });
      if (query) params.set("q", query);
      return api.get<Page<TranscriptionSummary>>(`/transcriptions?${params}`);
    },
    placeholderData: keepPreviousData,
  });
}

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
    // Poll while Whisper is working, stop once it's settled. Keep polling (slower) through
    // brief outages such as a deploy, so the page recovers on its own.
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "pending" || status === "processing") return isTransient(query.state.error) ? 5000 : 1500;
      return false;
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
    onSuccess: (data) => {
      queryClient.setQueryData(transcriptionKeys.detail(data.slug), data);
      queryClient.invalidateQueries({ queryKey: [...transcriptionKeys.all, "history"] });
    },
  });
}

export function useDeleteTranscription() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (slug: string) => api.delete<null>(`/transcriptions/${encodeURIComponent(slug)}`),
    onSuccess: (_, slug) => {
      queryClient.removeQueries({ queryKey: transcriptionKeys.detail(slug) });
      queryClient.invalidateQueries({ queryKey: [...transcriptionKeys.all, "history"] });
    },
  });
}
