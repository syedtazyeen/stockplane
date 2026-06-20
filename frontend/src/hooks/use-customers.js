import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  createCustomer,
  customersQueryKey,
  deleteCustomer,
  updateCustomer,
} from "@/api/customers";
import { invalidateDashboardQueries } from "@/lib/invalidate-business-queries";
import { toastError, toastSuccess } from "@/lib/toast";

export function useCreateCustomerMutation(businessId) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload) => createCustomer(businessId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: customersQueryKey(businessId) });
      invalidateDashboardQueries(queryClient, businessId);
      toastSuccess("Customer created.");
    },
    onError: (error) => toastError(error, "Unable to create customer."),
  });
}

export function useUpdateCustomerMutation(businessId) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ customerId, payload }) =>
      updateCustomer(businessId, customerId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: customersQueryKey(businessId) });
      invalidateDashboardQueries(queryClient, businessId);
      toastSuccess("Customer updated.");
    },
    onError: (error) => toastError(error, "Unable to update customer."),
  });
}

export function useDeleteCustomerMutation(businessId) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (customerId) => deleteCustomer(businessId, customerId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: customersQueryKey(businessId) });
      invalidateDashboardQueries(queryClient, businessId);
      toastSuccess("Customer deleted.");
    },
    onError: (error) => toastError(error, "Unable to delete customer."),
  });
}
