import { queryOptions } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";

function businessPath(businessId, path) {
  return `/businesses/${businessId}${path}`;
}

export const productsQueryKey = (businessId) => ["products", businessId];

export async function listProducts(businessId, params = {}) {
  const { data } = await apiClient.get(businessPath(businessId, "/products"), {
    params,
  });
  return data;
}

export async function getProduct(businessId, productId) {
  const { data } = await apiClient.get(
    businessPath(businessId, `/products/${productId}`),
  );
  return data;
}

export async function createProduct(businessId, payload) {
  const { data } = await apiClient.post(
    businessPath(businessId, "/products"),
    payload,
  );
  return data;
}

export async function updateProduct(businessId, productId, payload) {
  const { data } = await apiClient.patch(
    businessPath(businessId, `/products/${productId}`),
    payload,
  );
  return data;
}

export async function deleteProduct(businessId, productId) {
  await apiClient.delete(businessPath(businessId, `/products/${productId}`));
}

export function productsQueryOptions(businessId, filters = {}) {
  return queryOptions({
    queryKey: [...productsQueryKey(businessId), filters],
    queryFn: () => listProducts(businessId, filters),
  });
}

export function productQueryOptions(businessId, productId) {
  return queryOptions({
    queryKey: [...productsQueryKey(businessId), productId],
    queryFn: () => getProduct(businessId, productId),
  });
}
