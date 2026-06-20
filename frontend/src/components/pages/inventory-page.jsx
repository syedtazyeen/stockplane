import { zodResolver } from "@hookform/resolvers/zod";
import { useParams } from "@tanstack/react-router";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";

import { inventoryQueryOptions } from "@/api/inventory";
import { productsQueryOptions } from "@/api/products";
import { ListPagination } from "@/components/shared/list-pagination";
import { ListPage, ListStickyHeader, ListToolbar, ListTableScroll } from "@/components/shared/list-page";
import { ListResultsPanel } from "@/components/shared/list-results-panel";
import { PageHeader } from "@/components/shared/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
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
import {
  useAdjustInventoryMutation,
  useSetInventoryMutation,
} from "@/hooks/use-inventory";
import { useListUrlState } from "@/hooks/use-list-url-state";
import { hasNextPage, toInventoryApiParams } from "@/lib/list-search";
import { isLowStock } from "@/lib/inventory";
import {
  inventoryManualAdjustSchema,
  inventoryRestockSchema,
} from "@/lib/schemas/product";

const inventoryRoutePath = "/_main/$businessId/inventory";

function InventoryPage() {
  const { businessId } = useParams({ strict: false });
  const { searchParams, page, updateSearch, setPage } =
    useListUrlState(inventoryRoutePath);
  const [restockTarget, setRestockTarget] = useState(null);
  const [adjustTarget, setAdjustTarget] = useState(null);

  const apiParams = toInventoryApiParams(searchParams);

  const {
    data: inventory = [],
    isLoading,
    isFetching,
    isError,
    error,
    refetch,
  } = useQuery({
    ...inventoryQueryOptions(businessId, apiParams),
    placeholderData: keepPreviousData,
  });
  const { data: products = [] } = useQuery(
    productsQueryOptions(businessId, {}),
  );

  const productMap = useMemo(
    () => new Map(products.map((product) => [product.id, product])),
    [products],
  );

  const rows = useMemo(
    () =>
      inventory.map((item) => ({
        ...item,
        product: productMap.get(item.product_id),
      })),
    [inventory, productMap],
  );

  const showNextPage = hasNextPage(inventory.length);
  const lowStockOnly = searchParams.lowStock ?? false;

  return (
    <ListPage>
      <ListStickyHeader>
        <PageHeader title="Inventory" />

        <ListToolbar>
          <label className="flex h-9 items-center gap-2 rounded-lg border border-border bg-muted/50 px-3 text-sm">
            <input
              type="checkbox"
              className="size-4 rounded border-input"
              checked={lowStockOnly}
              onChange={(event) =>
                updateSearch(
                  { lowStock: event.target.checked ? "true" : undefined },
                  { resetPage: true },
                )
              }
            />
            Low stock only
          </label>
        </ListToolbar>
      </ListStickyHeader>

      <ListResultsPanel
        isLoading={isLoading}
        isFetching={isFetching}
        isError={isError}
        error={error}
        onRetry={() => refetch()}
        isEmpty={rows.length === 0}
        emptyState={
          <div className="px-6 py-16 text-center">
            <p className="text-sm font-medium">No inventory records found</p>
            <p className="mt-1 text-sm text-muted-foreground">
              {lowStockOnly
                ? "No out-of-stock or low-stock products right now."
                : "Add products to start tracking inventory."}
            </p>
          </div>
        }
      >
        <ListTableScroll>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Product</TableHead>
                <TableHead>SKU</TableHead>
                <TableHead>On hand</TableHead>
                <TableHead>Reserved</TableHead>
                <TableHead>Available</TableHead>
                <TableHead>Reorder point</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <span className="font-medium">
                        {item.product?.name ?? "Unknown product"}
                      </span>
                      {isLowStock(item) ? (
                        <Badge variant="warning">Low stock</Badge>
                      ) : null}
                    </div>
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {item.product?.sku ?? "—"}
                  </TableCell>
                  <TableCell>
                    {item.quantity_on_hand === 0 ? (
                      <span className="font-medium text-destructive">
                        {item.quantity_on_hand} in stock
                      </span>
                    ) : (
                      `${item.quantity_on_hand} in stock`
                    )}
                  </TableCell>
                  <TableCell>{item.reserved_quantity}</TableCell>
                  <TableCell>{item.available_quantity}</TableCell>
                  <TableCell>{item.reorder_point ?? "—"}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setRestockTarget(item)}
                      >
                        Restock
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setAdjustTarget(item)}
                      >
                        Adjust
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </ListTableScroll>
      </ListResultsPanel>

      <ListPagination
        page={page}
        hasNextPage={showNextPage}
        onPageChange={setPage}
      />

      <RestockInventoryDialog
        businessId={businessId}
        item={restockTarget}
        onClose={() => setRestockTarget(null)}
      />
      <AdjustInventoryDialog
        businessId={businessId}
        item={adjustTarget}
        onClose={() => setAdjustTarget(null)}
      />
    </ListPage>
  );
}

function RestockInventoryDialog({ businessId, item, onClose }) {
  const mutation = useAdjustInventoryMutation(businessId);
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(inventoryRestockSchema),
    defaultValues: {
      quantity: "",
      notes: "",
    },
  });

  useEffect(() => {
    if (!item) return;
    reset({
      quantity: "",
      notes: "",
    });
  }, [item, reset]);

  const onSubmit = handleSubmit(async (values) => {
    await mutation.mutateAsync({
      productId: item.product_id,
      payload: {
        quantity_delta: values.quantity,
        transaction_type: "RESTOCK",
        notes: values.notes || null,
      },
    });
    reset();
    onClose();
  });

  return (
    <Dialog
      open={Boolean(item)}
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Restock</DialogTitle>
          <DialogDescription>
            Add stock for {item?.product?.name ?? "this product"}. Currently{" "}
            {item?.quantity_on_hand ?? 0} on hand.
          </DialogDescription>
        </DialogHeader>
        <form className="space-y-4" onSubmit={onSubmit}>
          <Field>
            <Label htmlFor="restock_quantity">Quantity to add</Label>
            <Input
              id="restock_quantity"
              type="number"
              min={1}
              aria-invalid={Boolean(errors.quantity)}
              {...register("quantity")}
            />
            {errors.quantity ? (
              <FieldError>{errors.quantity.message}</FieldError>
            ) : null}
          </Field>

          <Field>
            <Label htmlFor="restock_notes">Notes</Label>
            <Textarea id="restock_notes" rows={2} {...register("notes")} />
          </Field>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              type="submit"
              loading={isSubmitting || mutation.isPending}
              disabled={isSubmitting || mutation.isPending}
            >
              Add stock
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function AdjustInventoryDialog({ businessId, item, onClose }) {
  const adjustMutation = useAdjustInventoryMutation(businessId);
  const setMutation = useSetInventoryMutation(businessId);
  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(inventoryManualAdjustSchema),
    defaultValues: {
      transaction_type: "CORRECTION",
      quantity_on_hand: 0,
      quantity_delta: "",
      notes: "",
    },
  });

  const transactionType = watch("transaction_type");
  const isCorrection = transactionType === "CORRECTION";
  const isPending = adjustMutation.isPending || setMutation.isPending;

  useEffect(() => {
    if (!item) return;
    reset({
      transaction_type: "CORRECTION",
      quantity_on_hand: item.quantity_on_hand,
      quantity_delta: "",
      notes: "",
    });
  }, [item, reset]);

  const onSubmit = handleSubmit(async (values) => {
    if (values.transaction_type === "CORRECTION") {
      await setMutation.mutateAsync({
        productId: item.product_id,
        payload: {
          quantity_on_hand: values.quantity_on_hand,
          transaction_type: "CORRECTION",
          notes: values.notes || null,
        },
      });
    } else {
      await adjustMutation.mutateAsync({
        productId: item.product_id,
        payload: {
          quantity_delta: values.quantity_delta,
          transaction_type: values.transaction_type,
          notes: values.notes || null,
        },
      });
    }
    reset();
    onClose();
  });

  return (
    <Dialog
      open={Boolean(item)}
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Adjust stock</DialogTitle>
          <DialogDescription>
            Correct counts or record other stock changes for{" "}
            {item?.product?.name ?? "this product"}.
          </DialogDescription>
        </DialogHeader>
        <form className="space-y-4" onSubmit={onSubmit}>
          <Field>
            <Label htmlFor="transaction_type">Reason</Label>
            <Select id="transaction_type" {...register("transaction_type")}>
              <option value="CORRECTION">Correction (count)</option>
              <option value="DAMAGE">Damage</option>
              <option value="RETURN">Return</option>
              <option value="SALE">Sale</option>
              <option value="OTHER">Other</option>
            </Select>
          </Field>

          {isCorrection ? (
            <Field>
              <Label htmlFor="quantity_on_hand">Quantity on hand</Label>
              <Input
                id="quantity_on_hand"
                type="number"
                min={0}
                aria-invalid={Boolean(errors.quantity_on_hand)}
                {...register("quantity_on_hand")}
              />
              {errors.quantity_on_hand ? (
                <FieldError>{errors.quantity_on_hand.message}</FieldError>
              ) : null}
            </Field>
          ) : (
            <Field>
              <Label htmlFor="quantity_delta">Quantity change</Label>
              <Input
                id="quantity_delta"
                type="number"
                aria-invalid={Boolean(errors.quantity_delta)}
                {...register("quantity_delta")}
              />
              {errors.quantity_delta ? (
                <FieldError>{errors.quantity_delta.message}</FieldError>
              ) : (
                <p className="text-sm text-muted-foreground">
                  Use a negative value to reduce stock.
                </p>
              )}
            </Field>
          )}

          <Field>
            <Label htmlFor="adjust_notes">Notes</Label>
            <Textarea id="adjust_notes" rows={2} {...register("notes")} />
          </Field>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              type="submit"
              loading={isSubmitting || isPending}
              disabled={isSubmitting || isPending}
            >
              Apply adjustment
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export { InventoryPage };
