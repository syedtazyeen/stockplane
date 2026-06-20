import axios from "axios";

import { clearSession, getToken } from "@/lib/auth-session";

const API_BASE_URL =
  import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    Accept: "application/json",
  },
});

apiClient.interceptors.request.use((config) => {
  const isAuthRequest =
    config.url?.endsWith("/auth/login") ||
    config.url?.endsWith("/auth/register");

  if (isAuthRequest) {
    return config;
  }

  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && getToken()) {
      clearSession();
    }
    return Promise.reject(error);
  },
);

export function getApiErrorMessage(error, fallback = "Something went wrong.") {
  const detail = error.response?.data?.detail;

  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail) && detail.length > 0) {
    return detail.map((item) => item.msg).join(", ");
  }

  return fallback;
}
