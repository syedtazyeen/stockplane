import { createFileRoute } from "@tanstack/react-router";
import { lazy, Suspense } from "react";

import { PageSpinner } from "@/components/shared/page-spinner";
import { customersQueryOptions } from "@/api/customers";
import {
  parseCustomersListSearch,
  toCustomersApiParams,
} from "@/lib/list-search";

const CustomersPage = lazy(() =>
  import("@/components/pages/customers-page").then((module) => ({
    default: module.CustomersPage,
  })),
);

export const Route = createFileRoute("/_main/$businessId/customers")({
  validateSearch: parseCustomersListSearch,
  loader: ({ context, params, search }) =>
    context.queryClient.ensureQueryData(
      customersQueryOptions(
        params.businessId,
        toCustomersApiParams(parseCustomersListSearch(search)),
      ),
    ),
  component: CustomersRoute,
});

function CustomersRoute() {
  return (
    <Suspense fallback={<PageSpinner />}>
      <CustomersPage />
    </Suspense>
  );
}
