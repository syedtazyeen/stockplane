import { createFileRoute, Outlet } from "@tanstack/react-router";

export const Route = createFileRoute("/_main/$businessId/orders")({
  component: OrdersLayout,
});

function OrdersLayout() {
  return <Outlet />;
}
