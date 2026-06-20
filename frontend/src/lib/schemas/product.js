import { z } from "zod";

const productStatusEnum = z.enum(["DRAFT", "ACTIVE", "ARCHIVED"]);

const priceField = z
  .string()
  .trim()
  .refine((value) => value === "" || !Number.isNaN(Number(value)), {
    message: "Enter a valid number",
  })
  .refine((value) => value === "" || Number(value) >= 0, {
    message: "Must be 0 or greater",
  });

export const productFormSchema = z.object({
  sku: z.string().trim().min(1, "SKU is required").max(100),
  name: z.string().trim().min(1, "Name is required").max(255),
  description: z.string().trim().optional(),
  status: productStatusEnum,
  cost_price: priceField,
  selling_price: priceField,
  quantity: z.coerce.number().int().min(0, "Must be 0 or greater"),
  reorder_point: z
    .union([z.literal(""), z.coerce.number().int().min(0)])
    .optional(),
});

export const inventoryRestockSchema = z.object({
  quantity: z.coerce.number().int().min(1, "Must add at least 1 unit"),
  notes: z.string().trim().optional(),
});

export const inventoryManualAdjustSchema = z
  .object({
    transaction_type: z.enum([
      "CORRECTION",
      "DAMAGE",
      "RETURN",
      "SALE",
      "OTHER",
    ]),
    quantity_on_hand: z.coerce.number().int().min(0).optional(),
    quantity_delta: z.coerce.number().int().optional(),
    notes: z.string().trim().optional(),
  })
  .superRefine((values, ctx) => {
    if (values.transaction_type === "CORRECTION") {
      if (values.quantity_on_hand == null || Number.isNaN(values.quantity_on_hand)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "Quantity is required",
          path: ["quantity_on_hand"],
        });
      }
      return;
    }

    if (!values.quantity_delta || values.quantity_delta === 0) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Adjustment cannot be zero",
        path: ["quantity_delta"],
      });
    }
  });

export function toProductPayload(values) {
  return {
    sku: values.sku,
    name: values.name,
    description: values.description || null,
    status: values.status,
    cost_price: values.cost_price || "0.00",
    selling_price: values.selling_price || "0.00",
    quantity: values.quantity,
    reorder_point:
      values.reorder_point === "" || values.reorder_point == null
        ? null
        : values.reorder_point,
  };
}
