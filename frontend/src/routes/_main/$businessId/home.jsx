import { createFileRoute } from "@tanstack/react-router";
import { lazy, Suspense } from "react";

import { dashboardQueryOptions } from "@/api/dashboard";
import { PageSpinner } from "@/components/shared/page-spinner";

const HomePage = lazy(() =>
  import("@/components/pages/home-page").then((module) => ({
    default: module.HomePage,
  })),
);

export const Route = createFileRoute("/_main/$businessId/home")({
  loader: ({ context, params }) =>
    context.queryClient.ensureQueryData(
      dashboardQueryOptions(params.businessId),
    ),
  component: HomeRoute,
});

function HomeRoute() {
  return (
    <Suspense fallback={<PageSpinner />}>
      <HomePage />
    </Suspense>
  );
}
