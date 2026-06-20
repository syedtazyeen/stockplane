import { createFileRoute } from "@tanstack/react-router";

import { NotFound } from "@/components/shared/not-found";

export const Route = createFileRoute("/_main/$businessId/$")({
  component: NotFound,
});
