import { createFileRoute, notFound } from "@tanstack/react-router";
import { lazy, Suspense } from "react";

import { PageSpinner } from "@/components/shared/page-spinner";
import { productQueryOptions } from "@/api/products";
import { isUuid } from "@/lib/utils";

const ProductEditPage = lazy(() =>
  import("@/components/pages/product-form-page").then((module) => ({
    default: module.ProductEditPage,
  })),
);

export const Route = createFileRoute("/_main/$businessId/products/$productId")({
  beforeLoad: ({ params }) => {
    if (!isUuid(params.productId)) {
      throw notFound();
    }
  },
  loader: async ({ context, params }) => {
    try {
      return await context.queryClient.ensureQueryData(
        productQueryOptions(params.businessId, params.productId),
      );
    } catch (error) {
      const status = error.response?.status;
      if (status === 404 || status === 422) {
        throw notFound();
      }
      throw error;
    }
  },
  component: EditProductRoute,
});

function EditProductRoute() {
  return (
    <Suspense fallback={<PageSpinner />}>
      <ProductEditPage />
    </Suspense>
  );
}
