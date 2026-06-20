import { queryOptions } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";

function businessPath(businessId, path) {
  return `/businesses/${businessId}${path}`;
}

export const inventoryQueryKey = (businessId) => ["inventory", businessId];

export async function listInventory(businessId, params = {}) {
  const { data } = await apiClient.get(businessPath(businessId, "/inventory"), {
    params,
  });
  return data;
}

export async function listInventoryTransactions(businessId, params = {}) {
  const { data } = await apiClient.get(
    businessPath(businessId, "/inventory/transactions"),
    { params },
  );
  return data;
}

export async function adjustInventory(businessId, productId, payload) {
  const { data } = await apiClient.post(
    businessPath(businessId, `/inventory/${productId}/adjust`),
    payload,
  );
  return data;
}

export async function setInventory(businessId, productId, payload) {
  const { data } = await apiClient.put(
    businessPath(businessId, `/inventory/${productId}/set`),
    payload,
  );
  return data;
}

export function inventoryQueryOptions(businessId, filters = {}) {
  return queryOptions({
    queryKey: [...inventoryQueryKey(businessId), filters],
    queryFn: () => listInventory(businessId, filters),
  });
}

export function inventoryTransactionsQueryOptions(businessId, filters = {}) {
  return queryOptions({
    queryKey: [...inventoryQueryKey(businessId), "transactions", filters],
    queryFn: () => listInventoryTransactions(businessId, filters),
  });
}
