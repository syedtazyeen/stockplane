import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";

import {
  createProduct,
  deleteProduct,
  updateProduct,
} from "@/api/products";
import { invalidateProductQueries } from "@/lib/invalidate-business-queries";
import { toastError, toastSuccess } from "@/lib/toast";

export function useCreateProductMutation(businessId) {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: (payload) => createProduct(businessId, payload),
    onSuccess: () => {
      invalidateProductQueries(queryClient, businessId);
      toastSuccess("Product created.");
      navigate({
        to: "/$businessId/products",
        params: { businessId },
      });
    },
    onError: (error) => toastError(error, "Unable to create product."),
  });
}

export function useUpdateProductMutation(businessId, productId) {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: (payload) => updateProduct(businessId, productId, payload),
    onSuccess: () => {
      invalidateProductQueries(queryClient, businessId, { productId });
      toastSuccess("Product updated.");
      navigate({
        to: "/$businessId/products",
        params: { businessId },
      });
    },
    onError: (error) => toastError(error, "Unable to update product."),
  });
}

export function useDeleteProductMutation(businessId) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (productId) => deleteProduct(businessId, productId),
    onSuccess: (_data, productId) => {
      invalidateProductQueries(queryClient, businessId, { productId });
      toastSuccess("Product deleted.");
    },
    onError: (error) => toastError(error, "Unable to delete product."),
  });
}
