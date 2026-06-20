import { createFileRoute, Outlet } from "@tanstack/react-router";

import { requireGuest } from "@/api/auth";

export const Route = createFileRoute("/_auth")({
  beforeLoad: ({ context }) => requireGuest(context.queryClient),
  component: () => <Outlet />,
});
