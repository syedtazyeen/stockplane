import { createFileRoute, notFound } from "@tanstack/react-router";
import { lazy, Suspense } from "react";

import { PageSpinner } from "@/components/shared/page-spinner";
import { orderQueryOptions } from "@/api/orders";
import { isUuid } from "@/lib/utils";

const OrderDetailPage = lazy(() =>
  import("@/components/pages/order-detail-page").then((module) => ({
    default: module.OrderDetailPage,
  })),
);

export const Route = createFileRoute("/_main/$businessId/orders/$orderId")({
  beforeLoad: ({ params }) => {
    if (!isUuid(params.orderId)) {
      throw notFound();
    }
  },
  loader: async ({ context, params }) => {
    try {
      return await context.queryClient.ensureQueryData(
        orderQueryOptions(params.businessId, params.orderId),
      );
    } catch (error) {
      const status = error.response?.status;
      if (status === 404 || status === 422) {
        throw notFound();
      }
      throw error;
    }
  },
  component: OrderDetailRoute,
});

function OrderDetailRoute() {
  return (
    <Suspense fallback={<PageSpinner />}>
      <OrderDetailPage />
    </Suspense>
  );
}
