import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  adjustInventory,
  setInventory,
} from "@/api/inventory";
import { invalidateInventoryQueries } from "@/lib/invalidate-business-queries";
import { toastError, toastSuccess } from "@/lib/toast";

export function useAdjustInventoryMutation(businessId) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ productId, payload }) =>
      adjustInventory(businessId, productId, payload),
    onSuccess: () => {
      invalidateInventoryQueries(queryClient, businessId);
      toastSuccess("Inventory updated.");
    },
    onError: (error) => toastError(error, "Unable to adjust inventory."),
  });
}

export function useSetInventoryMutation(businessId) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ productId, payload }) =>
      setInventory(businessId, productId, payload),
    onSuccess: () => {
      invalidateInventoryQueries(queryClient, businessId);
      toastSuccess("Inventory updated.");
    },
    onError: (error) => toastError(error, "Unable to update inventory."),
  });
}
