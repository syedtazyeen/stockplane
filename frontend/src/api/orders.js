import { queryOptions } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import { idempotencyHeaders } from "@/lib/idempotency";

function businessPath(businessId, path) {
  return `/businesses/${businessId}${path}`;
}

export const ordersQueryKey = (businessId) => ["orders", businessId];

export async function listOrders(businessId, params = {}) {
  const { data } = await apiClient.get(businessPath(businessId, "/orders"), {
    params,
  });
  return data;
}

export async function getOrder(businessId, orderId) {
  const { data } = await apiClient.get(
    businessPath(businessId, `/orders/${orderId}`),
  );
  return data;
}

export async function createOrder(businessId, payload, { idempotencyKey } = {}) {
  const { data } = await apiClient.post(
    businessPath(businessId, "/orders"),
    payload,
    { headers: idempotencyHeaders(idempotencyKey) },
  );
  return data;
}

export async function updateOrder(businessId, orderId, payload) {
  const { data } = await apiClient.patch(
    businessPath(businessId, `/orders/${orderId}`),
    payload,
  );
  return data;
}

export async function deleteOrder(businessId, orderId) {
  await apiClient.delete(businessPath(businessId, `/orders/${orderId}`));
}

export async function submitOrder(businessId, orderId) {
  const { data } = await apiClient.post(
    businessPath(businessId, `/orders/${orderId}/submit`),
  );
  return data;
}

export async function confirmOrder(businessId, orderId) {
  const { data } = await apiClient.post(
    businessPath(businessId, `/orders/${orderId}/confirm`),
  );
  return data;
}

export async function shipOrder(businessId, orderId) {
  const { data } = await apiClient.post(
    businessPath(businessId, `/orders/${orderId}/ship`),
  );
  return data;
}

export async function deliverOrder(businessId, orderId) {
  const { data } = await apiClient.post(
    businessPath(businessId, `/orders/${orderId}/deliver`),
  );
  return data;
}

export async function cancelOrder(businessId, orderId) {
  const { data } = await apiClient.post(
    businessPath(businessId, `/orders/${orderId}/cancel`),
  );
  return data;
}

export function ordersQueryOptions(businessId, filters = {}) {
  return queryOptions({
    queryKey: [...ordersQueryKey(businessId), filters],
    queryFn: () => listOrders(businessId, filters),
  });
}

export function orderQueryOptions(businessId, orderId) {
  return queryOptions({
    queryKey: [...ordersQueryKey(businessId), orderId],
    queryFn: () => getOrder(businessId, orderId),
  });
}
