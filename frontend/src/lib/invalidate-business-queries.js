import { dashboardQueryKey } from "@/api/dashboard";
import { inventoryQueryKey } from "@/api/inventory";
import { orderQueryOptions, ordersQueryKey } from "@/api/orders";
import { productsQueryKey } from "@/api/products";

export function invalidateDashboardQueries(queryClient, businessId) {
  queryClient.invalidateQueries({ queryKey: dashboardQueryKey(businessId) });
}

export function invalidateProductQueries(
  queryClient,
  businessId,
  { productId } = {},
) {
  queryClient.invalidateQueries({ queryKey: productsQueryKey(businessId) });
  queryClient.invalidateQueries({ queryKey: inventoryQueryKey(businessId) });
  invalidateDashboardQueries(queryClient, businessId);

  if (productId) {
    queryClient.invalidateQueries({
      queryKey: [...productsQueryKey(businessId), productId],
    });
  }
}

export function invalidateInventoryQueries(queryClient, businessId) {
  queryClient.invalidateQueries({ queryKey: inventoryQueryKey(businessId) });
  queryClient.invalidateQueries({ queryKey: productsQueryKey(businessId) });
  invalidateDashboardQueries(queryClient, businessId);
}

export function invalidateOrderQueries(
  queryClient,
  businessId,
  orderId,
  { includeInventory = true } = {},
) {
  queryClient.invalidateQueries({ queryKey: ordersQueryKey(businessId) });
  invalidateDashboardQueries(queryClient, businessId);

  if (orderId) {
    queryClient.invalidateQueries({
      queryKey: orderQueryOptions(businessId, orderId).queryKey,
    });
  }

  if (includeInventory) {
    invalidateInventoryQueries(queryClient, businessId);
  }
}
