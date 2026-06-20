import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";

import {
  cancelOrder,
  confirmOrder,
  createOrder,
  deleteOrder,
  deliverOrder,
  getOrder,
  shipOrder,
  submitOrder,
  updateOrder,
} from "@/api/orders";
import { invalidateOrderQueries } from "@/lib/invalidate-business-queries";
import { createIdempotencyKey } from "@/lib/idempotency";
import { toOrderPayload } from "@/lib/schemas/order";
import { toastError, toastSuccess } from "@/lib/toast";

export function useCreateOrderMutation(businessId) {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: async ({
      values,
      saveAsDraft = false,
      idempotencyKey = createIdempotencyKey(),
    }) => {
      const createdOrder = await createOrder(
        businessId,
        toOrderPayload(values, { saveAsDraft }),
        { idempotencyKey },
      );

      if (saveAsDraft) {
        return { order: createdOrder, saveAsDraft: true };
      }

      const order = await getOrder(businessId, createdOrder.id);
      if (order.status === "PENDING") {
        const confirmedOrder = await confirmOrder(businessId, order.id);
        return { order: confirmedOrder, saveAsDraft: false };
      }

      return { order, saveAsDraft: false };
    },
    onSuccess: ({ order, saveAsDraft }) => {
      invalidateOrderQueries(queryClient, businessId, order.id, {
        includeInventory: !saveAsDraft,
      });
      toastSuccess(
        saveAsDraft ? "Draft order saved." : "Order created and confirmed.",
      );
      navigate({
        to: saveAsDraft
          ? "/$businessId/draft_orders"
          : "/$businessId/orders/$orderId",
        params: saveAsDraft
          ? { businessId }
          : { businessId, orderId: order.id },
      });
    },
    onError: (error) => toastError(error, "Unable to create order."),
  });
}

export function useUpdateOrderMutation(businessId, orderId) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload) => updateOrder(businessId, orderId, payload),
    onSuccess: () => {
      invalidateOrderQueries(queryClient, businessId, orderId, {
        includeInventory: false,
      });
      toastSuccess("Notes updated.");
    },
    onError: (error) => toastError(error, "Unable to update notes."),
  });
}

export function useDeleteOrderMutation(businessId) {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: (orderId) => deleteOrder(businessId, orderId),
    onSuccess: (_data, orderId) => {
      invalidateOrderQueries(queryClient, businessId, orderId);
      toastSuccess("Order deleted.");
      navigate({
        to: "/$businessId/orders",
        params: { businessId },
      });
    },
    onError: (error) => toastError(error, "Unable to delete order."),
  });
}

function createOrderActionHook(
  actionFn,
  { includeInventory = false, successMessage, errorMessage } = {},
) {
  return function useOrderActionMutation(businessId, orderId) {
    const queryClient = useQueryClient();

    return useMutation({
      mutationFn: () => actionFn(businessId, orderId),
      onSuccess: () => {
        invalidateOrderQueries(queryClient, businessId, orderId, {
          includeInventory,
        });
        toastSuccess(successMessage);
      },
      onError: (error) => toastError(error, errorMessage),
    });
  };
}

export const useSubmitOrderMutation = createOrderActionHook(submitOrder, {
  includeInventory: true,
  successMessage: "Order submitted.",
  errorMessage: "Unable to submit order.",
});
export const useConfirmOrderMutation = createOrderActionHook(confirmOrder, {
  successMessage: "Order confirmed.",
  errorMessage: "Unable to confirm order.",
});
export const useShipOrderMutation = createOrderActionHook(shipOrder, {
  successMessage: "Order marked as shipped.",
  errorMessage: "Unable to ship order.",
});
export const useDeliverOrderMutation = createOrderActionHook(deliverOrder, {
  successMessage: "Order marked as delivered.",
  errorMessage: "Unable to deliver order.",
});
export const useCancelOrderMutation = createOrderActionHook(cancelOrder, {
  includeInventory: true,
  successMessage: "Order cancelled.",
  errorMessage: "Unable to cancel order.",
});
