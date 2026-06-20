import { createFileRoute } from "@tanstack/react-router";
import { lazy, Suspense } from "react";

import { PageSpinner } from "@/components/shared/page-spinner";

const ProductFormPage = lazy(() =>
  import("@/components/pages/product-form-page").then((module) => ({
    default: module.ProductFormPage,
  })),
);

export const Route = createFileRoute("/_main/$businessId/products/new")({
  component: NewProductRoute,
});

function NewProductRoute() {
  return (
    <Suspense fallback={<PageSpinner />}>
      <ProductFormPage />
    </Suspense>
  );
}
