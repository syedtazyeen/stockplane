import { createFileRoute } from "@tanstack/react-router";
import { lazy, Suspense } from "react";

import { PageSpinner } from "@/components/shared/page-spinner";
import { productsQueryOptions } from "@/api/products";
import {
  parseProductsListSearch,
  toProductsApiParams,
} from "@/lib/list-search";

const ProductsPage = lazy(() =>
  import("@/components/pages/products-page").then((module) => ({
    default: module.ProductsPage,
  })),
);

export const Route = createFileRoute("/_main/$businessId/products/")({
  validateSearch: parseProductsListSearch,
  loader: ({ context, params, search }) =>
    context.queryClient.ensureQueryData(
      productsQueryOptions(
        params.businessId,
        toProductsApiParams(parseProductsListSearch(search)),
      ),
    ),
  component: ProductsIndexRoute,
});

function ProductsIndexRoute() {
  return (
    <Suspense fallback={<PageSpinner />}>
      <ProductsPage />
    </Suspense>
  );
}
