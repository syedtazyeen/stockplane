import { zodResolver } from "@hookform/resolvers/zod";
import { Link, useParams } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeftIcon, PlusIcon, TrashIcon } from "@phosphor-icons/react";
import { useMemo, useRef, useState } from "react";
import { Controller, useFieldArray, useForm, useWatch } from "react-hook-form";

import { customersQueryOptions } from "@/api/customers";
import { productsQueryOptions } from "@/api/products";
import { ListPage, ListTableScroll } from "@/components/shared/list-page";
import { PageHeader } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Field, FieldError } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import { useCreateOrderMutation } from "@/hooks/use-orders";
import { createIdempotencyKey } from "@/lib/idempotency";
import { formatCurrency } from "@/lib/format";
import { createOrderFormSchema } from "@/lib/schemas/order";

const defaultLine = { product_id: "", quantity: 1 };

function getLineProductOptions(products, lines, lineIndex) {
  const selectedInOtherLines = new Set(
    lines
      .map((line, index) => (index !== lineIndex ? line?.product_id : null))
      .filter(Boolean),
  );

  return products.filter(
    (product) =>
      !selectedInOtherLines.has(product.id) ||
      product.id === lines[lineIndex]?.product_id,
  );
}

function OrderFormPage() {
  const { businessId } = useParams({ strict: false });
  const mutation = useCreateOrderMutation(businessId);
  const [pendingAction, setPendingAction] = useState(null);
  const submitLockRef = useRef(false);

  const { data: customers = [] } = useQuery(
    customersQueryOptions(businessId, {}),
  );
  const { data: products = [] } = useQuery(
    productsQueryOptions(businessId, { status: "ACTIVE" }),
  );

  const activeCustomers = useMemo(
    () => customers.filter((customer) => customer.status === "ACTIVE"),
    [customers],
  );

  const productMap = useMemo(
    () => new Map(products.map((product) => [product.id, product])),
    [products],
  );

  const orderSchema = useMemo(
    () => createOrderFormSchema(productMap),
    [productMap],
  );

  const {
    register,
    control,
    handleSubmit,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(orderSchema),
    defaultValues: {
      customer_id: "",
      lines: [defaultLine],
      notes: "",
    },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: "lines",
  });

  const watchedLines = useWatch({ control, name: "lines" }) ?? [];

  const orderTotal = useMemo(() => {
    return watchedLines.reduce((total, line) => {
      const product = productMap.get(line.product_id);
      if (!product || !line.quantity) return total;
      return total + Number(product.selling_price) * Number(line.quantity);
    }, 0);
  }, [watchedLines, productMap]);

  const submitOrder = (saveAsDraft) => {
    if (submitLockRef.current) {
      return;
    }

    submitLockRef.current = true;
    const idempotencyKey = createIdempotencyKey();
    setPendingAction(saveAsDraft ? "draft" : "create");

    const releaseSubmit = () => {
      submitLockRef.current = false;
      setPendingAction(null);
    };

    return handleSubmit(
      async (values) => {
        try {
          await mutation.mutateAsync({ values, saveAsDraft, idempotencyKey });
        } finally {
          releaseSubmit();
        }
      },
      releaseSubmit,
    )();
  };

  const isProcessing = mutation.isPending || pendingAction !== null;
  const isDraftLoading = pendingAction === "draft";
  const isCreateLoading = pendingAction === "create";
  const actionsDisabled =
    isProcessing || activeCustomers.length === 0 || products.length === 0;

  return (
    <ListPage>
      <PageHeader
        title="Create order"
        actions={
          <Button
            variant="outline"
            disabled={isProcessing}
            render={
              <Link
                to="/$businessId/orders"
                params={{ businessId }}
              />
            }
          >
            <ArrowLeftIcon />
            Back to orders
          </Button>
        }
      />

      <Card className="max-w-3xl">
        <CardContent className="pt-6">
          <form
            className="space-y-6"
            onSubmit={(event) => {
              event.preventDefault();
              submitOrder(false);
            }}
          >
            <Field>
              <Label htmlFor="customer_id">Customer</Label>
              <Select
                id="customer_id"
                aria-invalid={Boolean(errors.customer_id)}
                {...register("customer_id")}
              >
                <option value="">Select a customer</option>
                {activeCustomers.map((customer) => (
                  <option key={customer.id} value={customer.id}>
                    {customer.name} ({customer.email})
                  </option>
                ))}
              </Select>
              {errors.customer_id ? (
                <FieldError>{errors.customer_id.message}</FieldError>
              ) : null}
              {activeCustomers.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No active customers. Add a customer before creating an order.
                </p>
              ) : null}
            </Field>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label>Line items</Label>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => append({ ...defaultLine })}
                  disabled={
                    products.length === 0 ||
                    fields.length >= products.length
                  }
                >
                  <PlusIcon />
                  Add line
                </Button>
              </div>

              {products.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No active products available to order.
                </p>
              ) : (
                <div className="overflow-hidden rounded-lg border border-border">
                  <ListTableScroll>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Product</TableHead>
                          <TableHead className="w-28">Quantity</TableHead>
                          <TableHead className="w-24">In stock</TableHead>
                          <TableHead className="w-28">Unit price</TableHead>
                          <TableHead className="w-28">Line total</TableHead>
                          <TableHead className="w-12" />
                        </TableRow>
                      </TableHeader>
                    <TableBody>
                      {fields.map((field, index) => {
                        const line = watchedLines[index];
                        const product = productMap.get(line?.product_id);
                        const lineTotal = product
                          ? Number(product.selling_price) * Number(line?.quantity || 0)
                          : 0;

                        return (
                          <TableRow key={field.id}>
                            <TableCell>
                              <Controller
                                control={control}
                                name={`lines.${index}.product_id`}
                                render={({ field }) => (
                                  <Select
                                    aria-invalid={Boolean(
                                      errors.lines?.[index]?.product_id,
                                    )}
                                    value={field.value}
                                    onChange={field.onChange}
                                    onBlur={field.onBlur}
                                    name={field.name}
                                    ref={field.ref}
                                  >
                                    <option value="">Select product</option>
                                    {getLineProductOptions(
                                      products,
                                      watchedLines,
                                      index,
                                    ).map((item) => (
                                      <option key={item.id} value={item.id}>
                                        {item.name} ({item.sku}) —{" "}
                                        {item.quantity} in stock
                                      </option>
                                    ))}
                                  </Select>
                                )}
                              />
                              {errors.lines?.[index]?.product_id ? (
                                <FieldError>
                                  {errors.lines[index].product_id.message}
                                </FieldError>
                              ) : null}
                            </TableCell>
                            <TableCell>
                              <Controller
                                control={control}
                                name={`lines.${index}.quantity`}
                                render={({ field }) => (
                                  <Input
                                    type="number"
                                    min={1}
                                    aria-invalid={Boolean(
                                      errors.lines?.[index]?.quantity,
                                    )}
                                    value={field.value}
                                    onChange={(event) => {
                                      const nextValue = event.target.value;
                                      field.onChange(
                                        nextValue === ""
                                          ? ""
                                          : Number(nextValue),
                                      );
                                    }}
                                    onBlur={field.onBlur}
                                    name={field.name}
                                    ref={field.ref}
                                  />
                                )}
                              />
                              {errors.lines?.[index]?.quantity ? (
                                <FieldError>
                                  {errors.lines[index].quantity.message}
                                </FieldError>
                              ) : product ? (
                                <p className="text-xs text-muted-foreground">
                                  {Number(product.quantity) === 0
                                    ? "Out of stock"
                                    : `${product.quantity} available`}
                                </p>
                              ) : null}
                            </TableCell>
                            <TableCell className="text-muted-foreground">
                              {product ? product.quantity : "—"}
                            </TableCell>
                            <TableCell className="text-muted-foreground">
                              {product
                                ? formatCurrency(product.selling_price)
                                : "—"}
                            </TableCell>
                            <TableCell>
                              {product ? formatCurrency(lineTotal) : "—"}
                            </TableCell>
                            <TableCell>
                              <Button
                                type="button"
                                variant="ghost"
                                size="sm"
                                className="text-destructive hover:text-destructive"
                                onClick={() => remove(index)}
                                disabled={fields.length === 1}
                              >
                                <TrashIcon />
                              </Button>
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                  </ListTableScroll>
                </div>
              )}

              {errors.lines?.message ? (
                <FieldError>{errors.lines.message}</FieldError>
              ) : null}
            </div>

            <div className="flex justify-end text-sm">
              <span className="text-muted-foreground">Order total</span>
              <span className="ml-3 font-medium">
                {formatCurrency(orderTotal)}
              </span>
            </div>

            <Field>
              <Label htmlFor="notes">Notes</Label>
              <Textarea
                id="notes"
                rows={3}
                placeholder="Optional order notes"
                {...register("notes")}
              />
            </Field>

            <div className="flex justify-end gap-2">
              <Button
                type="button"
                variant="outline"
                disabled={isProcessing}
                render={
                  <Link
                    to="/$businessId/orders"
                    params={{ businessId }}
                  />
                }
              >
                Cancel
              </Button>
              <Button
                type="button"
                variant="outline"
                loading={isDraftLoading}
                disabled={actionsDisabled}
                onClick={() => submitOrder(true)}
              >
                Save as draft
              </Button>
              <Button
                type="submit"
                loading={isCreateLoading}
                disabled={actionsDisabled}
              >
                Create order
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </ListPage>
  );
}

export { OrderFormPage };
