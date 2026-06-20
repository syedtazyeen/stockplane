import { queryOptions } from "@tanstack/react-query";
import { redirect } from "@tanstack/react-router";

import { apiClient } from "@/lib/api-client";
import {
  clearSession,
  getDefaultBusinessId,
  getStoredUser,
  getToken,
  hasSession,
  setSession,
} from "@/lib/auth-session";

export const authQueryKey = ["auth", "me"];

export async function login({ email, password }) {
  const params = new URLSearchParams();
  params.set("username", email);
  params.set("password", password);

  const { data } = await apiClient.post("/auth/login", params, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });

  return data;
}

export async function register(payload) {
  const { data } = await apiClient.post("/auth/register", payload);
  return data;
}

export async function fetchMe() {
  if (!getToken()) {
    throw new Error("Not authenticated");
  }

  const { data } = await apiClient.get("/auth/me");
  return data;
}

export function authQueryOptions() {
  return queryOptions({
    queryKey: authQueryKey,
    queryFn: fetchMe,
    staleTime: Infinity,
    retry: false,
    initialData: () => getStoredUser() ?? undefined,
    initialDataUpdatedAt: () => (getStoredUser() ? 0 : undefined),
  });
}

export function applyAuthResponse(queryClient, response) {
  setSession({
    accessToken: response.access_token,
    user: response.user,
    memberships: response.memberships,
  });

  queryClient.setQueryData(authQueryKey, response.user);
}

export function logout(queryClient) {
  clearSession();
  queryClient.removeQueries({ queryKey: authQueryKey });
}

export async function ensureAuthenticated(queryClient) {
  if (!getToken()) {
    throw new Error("Not authenticated");
  }

  return queryClient.ensureQueryData(authQueryOptions());
}

export async function requireGuest(queryClient) {
  if (!hasSession()) {
    return;
  }

  try {
    await ensureAuthenticated(queryClient);
  } catch {
    clearSession();
    return;
  }

  const businessId = getDefaultBusinessId();

  throw redirect(
    businessId
      ? { to: "/$businessId/home", params: { businessId } }
      : { to: "/" },
  );
}
