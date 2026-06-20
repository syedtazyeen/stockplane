import { createFileRoute } from "@tanstack/react-router";
import { lazy, Suspense } from "react";

import { PageSpinner } from "@/components/shared/page-spinner";
import { ordersQueryOptions } from "@/api/orders";
import {
  parseDraftOrdersListSearch,
  toOrdersApiParams,
} from "@/lib/list-search";

const OrdersPage = lazy(() =>
  import("@/components/pages/orders-page").then((module) => ({
    default: module.OrdersPage,
  })),
);

export const Route = createFileRoute("/_main/$businessId/draft_orders")({
  validateSearch: parseDraftOrdersListSearch,
  loader: ({ context, params, search }) =>
    context.queryClient.ensureQueryData(
      ordersQueryOptions(
        params.businessId,
        toOrdersApiParams(parseDraftOrdersListSearch(search), {
          fixedStatus: "DRAFT",
        }),
      ),
    ),
  component: DraftOrdersRoute,
});

function DraftOrdersRoute() {
  return (
    <Suspense fallback={<PageSpinner />}>
      <OrdersPage
        title="Draft orders"
        routePath="/_main/$businessId/draft_orders"
        fixedStatus="DRAFT"
        emptyTitle="No draft orders"
        emptyDescription="Draft orders will appear here once created."
        showCreateAction={false}
      />
    </Suspense>
  );
}
