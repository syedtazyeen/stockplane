import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";

import {
  applyAuthResponse,
  authQueryKey,
  authQueryOptions,
  login,
  logout,
  register,
} from "@/api/auth";
import { getDefaultBusinessId } from "@/lib/auth-session";
import { toastError, toastSuccess } from "@/lib/toast";

export function useAuth() {
  return useQuery(authQueryOptions());
}

export function useLoginMutation({ redirectTo } = {}) {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: login,
    onSuccess: (response) => {
      applyAuthResponse(queryClient, response);
      toastSuccess("Signed in.");

      if (redirectTo) {
        window.location.assign(redirectTo);
        return;
      }

      const businessId =
        response.memberships?.[0]?.business?.id ?? getDefaultBusinessId();

      if (businessId) {
        navigate({
          to: "/$businessId/home",
          params: { businessId },
        });
        return;
      }

      navigate({ to: "/" });
    },
    onError: (error) => toastError(error, "Unable to sign in."),
  });
}

export function useRegisterMutation() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: register,
    onSuccess: (response) => {
      applyAuthResponse(queryClient, response);
      toastSuccess("Account created.");
      const businessId =
        response.memberships?.[0]?.business?.id ?? getDefaultBusinessId();

      if (businessId) {
        navigate({
          to: "/$businessId/home",
          params: { businessId },
        });
        return;
      }

      navigate({ to: "/" });
    },
    onError: (error) => toastError(error, "Unable to create account."),
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  return () => {
    logout(queryClient);
    toastSuccess("Signed out.");
    navigate({ to: "/login" });
  };
}

export { authQueryKey };
