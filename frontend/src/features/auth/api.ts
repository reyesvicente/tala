import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, ApiError } from "@/lib/api";

import type { User } from "./types";

export const authKeys = {
  me: ["auth", "me"] as const,
};

export function useMe() {
  return useQuery({
    queryKey: authKeys.me,
    // Logged out is a normal state, not an error.
    queryFn: async () => {
      try {
        return await api.get<User>("/auth/me");
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) return null;
        throw error;
      }
    },
    staleTime: 5 * 60_000,
  });
}

function useSetUser() {
  const queryClient = useQueryClient();
  return (user: User | null) => {
    queryClient.setQueryData(authKeys.me, user);
    // History belongs to whoever is logged in now.
    queryClient.removeQueries({ queryKey: ["transcriptions", "history"] });
  };
}

export function useLogin() {
  const setUser = useSetUser();
  return useMutation({
    mutationFn: (body: { email: string; password: string }) => api.postJson<User>("/auth/login", body),
    onSuccess: setUser,
  });
}

export function useRegister() {
  const setUser = useSetUser();
  return useMutation({
    mutationFn: (body: { email: string; password: string }) => api.postJson<User>("/auth/register", body),
    onSuccess: setUser,
  });
}

export function useLogout() {
  return useMutation({
    mutationFn: () => api.postJson<null>("/auth/logout"),
    // Full reload to the home page: drops every cached query from memory and avoids
    // protected pages redirecting to /login mid-logout.
    onSuccess: () => window.location.assign("/"),
  });
}

export function useForgotPassword() {
  return useMutation({
    mutationFn: (body: { email: string }) => api.postJson<null>("/auth/forgot-password", body),
  });
}

export function useResetPassword() {
  const setUser = useSetUser();
  return useMutation({
    mutationFn: (body: { token: string; password: string }) => api.postJson<User>("/auth/reset-password", body),
    onSuccess: setUser,
  });
}
