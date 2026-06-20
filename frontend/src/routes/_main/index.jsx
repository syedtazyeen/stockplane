import { createFileRoute, redirect } from "@tanstack/react-router";

import { getDefaultBusinessId } from "@/lib/auth-session";

export const Route = createFileRoute("/_main/")({
  beforeLoad: () => {
    const businessId = getDefaultBusinessId();

    if (!businessId) {
      throw redirect({ to: "/login" });
    }

    throw redirect({
      to: "/$businessId/home",
      params: { businessId },
    });
  },
});
