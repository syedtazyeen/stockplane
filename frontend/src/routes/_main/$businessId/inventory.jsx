import { createFileRoute } from "@tanstack/react-router";
import { lazy, Suspense } from "react";

import { PageSpinner } from "@/components/shared/page-spinner";
import { inventoryQueryOptions } from "@/api/inventory";
import { productsQueryOptions } from "@/api/products";
import {
  parseInventoryListSearch,
  toInventoryApiParams,
} from "@/lib/list-search";

const InventoryPage = lazy(() =>
  import("@/components/pages/inventory-page").then((module) => ({
    default: module.InventoryPage,
  })),
);

export const Route = createFileRoute("/_main/$businessId/inventory")({
  validateSearch: parseInventoryListSearch,
  loader: async ({ context, params, search }) => {
    const { businessId } = params;
    const listSearch = parseInventoryListSearch(search);

    await Promise.all([
      context.queryClient.ensureQueryData(
        inventoryQueryOptions(businessId, toInventoryApiParams(listSearch)),
      ),
      context.queryClient.ensureQueryData(
        productsQueryOptions(businessId, {}),
      ),
    ]);
  },
  component: InventoryRoute,
});

function InventoryRoute() {
  return (
    <Suspense fallback={<PageSpinner />}>
      <InventoryPage />
    </Suspense>
  );
}
