import { createFileRoute, Outlet, redirect } from "@tanstack/react-router";

import { ensureAuthenticated } from "@/api/auth";
import { clearSession } from "@/lib/auth-session";

export const Route = createFileRoute("/_main")({
  beforeLoad: async ({ context, location }) => {
    try {
      await ensureAuthenticated(context.queryClient);
    } catch {
      clearSession();
      throw redirect({
        to: "/login",
        search: { redirect: location.href },
      });
    }
  },
  component: () => <Outlet />,
});
