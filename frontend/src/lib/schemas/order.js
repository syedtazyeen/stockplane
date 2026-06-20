import { z } from "zod";

const orderLineSchema = z.object({
  product_id: z.string().trim().min(1, "Product is required"),
  quantity: z.coerce.number().int().min(1, "Must be at least 1"),
});

export const orderFormSchema = z
  .object({
    customer_id: z.string().trim().min(1, "Customer is required"),
    lines: z.array(orderLineSchema).min(1, "Add at least one line item"),
    notes: z.string().trim().optional(),
  })
  .superRefine((values, ctx) => {
    const productIds = values.lines.map((line) => line.product_id);
    if (new Set(productIds).size !== productIds.length) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Each product can only appear once",
        path: ["lines"],
      });
    }
  });

export function createOrderFormSchema(productMap) {
  return orderFormSchema.superRefine((values, ctx) => {
    values.lines.forEach((line, index) => {
      const product = productMap.get(line.product_id);
      if (!product || !line.quantity) return;

      const stock = Number(product.quantity);
      if (line.quantity > stock) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message:
            stock === 0
              ? "This product is out of stock"
              : `Only ${stock} in stock`,
          path: ["lines", index, "quantity"],
        });
      }
    });
  });
}

export const orderNotesSchema = z.object({
  notes: z.string().trim().optional(),
});

export function toOrderPayload(values, { saveAsDraft = false } = {}) {
  return {
    customer_id: values.customer_id,
    lines: values.lines.map((line) => ({
      product_id: line.product_id,
      quantity: line.quantity,
    })),
    notes: values.notes || null,
    save_as_draft: saveAsDraft,
  };
}
