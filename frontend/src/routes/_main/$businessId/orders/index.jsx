import { createFileRoute } from "@tanstack/react-router";
import { lazy, Suspense } from "react";

import { PageSpinner } from "@/components/shared/page-spinner";
import { ordersQueryOptions } from "@/api/orders";
import {
  parseOrdersListSearch,
  toOrdersApiParams,
} from "@/lib/list-search";

const OrdersPage = lazy(() =>
  import("@/components/pages/orders-page").then((module) => ({
    default: module.OrdersPage,
  })),
);

export const Route = createFileRoute("/_main/$businessId/orders/")({
  validateSearch: parseOrdersListSearch,
  loader: ({ context, params, search }) =>
    context.queryClient.ensureQueryData(
      ordersQueryOptions(
        params.businessId,
        toOrdersApiParams(parseOrdersListSearch(search)),
      ),
    ),
  component: OrdersIndexRoute,
});

function OrdersIndexRoute() {
  return (
    <Suspense fallback={<PageSpinner />}>
      <OrdersPage />
    </Suspense>
  );
}
