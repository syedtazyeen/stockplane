import { createFileRoute, Outlet } from "@tanstack/react-router";

export const Route = createFileRoute("/_main/$businessId/products")({
  component: ProductsLayout,
});

function ProductsLayout() {
  return <Outlet />;
}
