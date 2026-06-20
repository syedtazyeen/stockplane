import { createFileRoute, redirect } from "@tanstack/react-router";

export const Route = createFileRoute("/_main/$businessId/")({
  beforeLoad: ({ params }) => {
    throw redirect({
      to: "/$businessId/home",
      params: { businessId: params.businessId },
    });
  },
});
