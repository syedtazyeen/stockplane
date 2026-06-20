import { queryOptions } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";

function businessPath(businessId, path) {
  return `/businesses/${businessId}${path}`;
}

export const customersQueryKey = (businessId) => ["customers", businessId];

export async function listCustomers(businessId, params = {}) {
  const { data } = await apiClient.get(businessPath(businessId, "/customers"), {
    params,
  });
  return data;
}

export async function getCustomer(businessId, customerId) {
  const { data } = await apiClient.get(
    businessPath(businessId, `/customers/${customerId}`),
  );
  return data;
}

export async function createCustomer(businessId, payload) {
  const { data } = await apiClient.post(
    businessPath(businessId, "/customers"),
    payload,
  );
  return data;
}

export async function updateCustomer(businessId, customerId, payload) {
  const { data } = await apiClient.patch(
    businessPath(businessId, `/customers/${customerId}`),
    payload,
  );
  return data;
}

export async function deleteCustomer(businessId, customerId) {
  const { data } = await apiClient.delete(
    businessPath(businessId, `/customers/${customerId}`),
  );
  return data;
}

export function customersQueryOptions(businessId, filters = {}) {
  return queryOptions({
    queryKey: [...customersQueryKey(businessId), filters],
    queryFn: () => listCustomers(businessId, filters),
  });
}
