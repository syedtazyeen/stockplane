import { createFileRoute } from "@tanstack/react-router";
import { lazy, Suspense } from "react";

import { PageSpinner } from "@/components/shared/page-spinner";
import { customersQueryOptions } from "@/api/customers";
import { productsQueryOptions } from "@/api/products";

const OrderFormPage = lazy(() =>
  import("@/components/pages/order-form-page").then((module) => ({
    default: module.OrderFormPage,
  })),
);

export const Route = createFileRoute("/_main/$businessId/orders/new")({
  loader: async ({ context, params }) => {
    const { businessId } = params;
    await Promise.all([
      context.queryClient.ensureQueryData(
        customersQueryOptions(businessId, {}),
      ),
      context.queryClient.ensureQueryData(
        productsQueryOptions(businessId, { status: "ACTIVE" }),
      ),
    ]);
  },
  component: NewOrderRoute,
});

function NewOrderRoute() {
  return (
    <Suspense fallback={<PageSpinner />}>
      <OrderFormPage />
    </Suspense>
  );
}
