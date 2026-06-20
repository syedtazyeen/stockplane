import { queryOptions } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";

function businessPath(businessId, path) {
  return `/businesses/${businessId}${path}`;
}

export const dashboardQueryKey = (businessId) => ["dashboard", businessId];

function mapLowStockProduct(item) {
  return {
    product_id: item.product_id,
    quantity_on_hand: item.quantity_on_hand,
    available_quantity: item.available_quantity,
    reorder_point: item.reorder_point,
    product: {
      name: item.product_name,
      sku: item.product_sku,
    },
  };
}

export async function fetchDashboardStats(businessId) {
  const { data } = await apiClient.get(businessPath(businessId, "/stats"));

  return {
    productCount: data.product_count,
    customerCount: data.customer_count,
    orderCount: data.order_count,
    lowStockCount: data.low_stock_count,
    lowStockItems: data.low_stock_products.map(mapLowStockProduct),
  };
}

export function dashboardQueryOptions(businessId) {
  return queryOptions({
    queryKey: dashboardQueryKey(businessId),
    queryFn: () => fetchDashboardStats(businessId),
    staleTime: 30_000,
  });
}
