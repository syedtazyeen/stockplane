import { zodResolver } from "@hookform/resolvers/zod";
import { Link, useParams } from "@tanstack/react-router";
import { useSuspenseQuery } from "@tanstack/react-query";
import { ArrowLeftIcon, DotsThreeIcon } from "@phosphor-icons/react";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";

import { orderQueryOptions } from "@/api/orders";
import { ListPage } from "@/components/shared/list-page";
import { PageHeader } from "@/components/shared/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Field, FieldError } from "@/components/ui/field";
import { Label } from "@/components/ui/label";
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
  useCancelOrderMutation,
  useConfirmOrderMutation,
  useDeleteOrderMutation,
  useDeliverOrderMutation,
  useShipOrderMutation,
  useSubmitOrderMutation,
  useUpdateOrderMutation,
} from "@/hooks/use-orders";
import {
  formatCurrency,
  formatDate,
  formatStatus,
  orderStatusVariant,
} from "@/lib/format";
import { orderNotesSchema } from "@/lib/schemas/order";

function OrderNotesDialog({ open, order, businessId, onClose }) {
  const mutation = useUpdateOrderMutation(businessId, order.id);
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(orderNotesSchema),
    defaultValues: { notes: "" },
  });

  useEffect(() => {
    if (!open) return;
    reset({ notes: order.notes ?? "" });
  }, [open, order.notes, reset]);

  const onSubmit = handleSubmit(async (values) => {
    await mutation.mutateAsync({ notes: values.notes || null });
    onClose();
  });

  return (
    <Dialog
      open={open}
      onOpenChange={(nextOpen) => {
        if (!nextOpen) onClose();
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Edit notes</DialogTitle>
          <DialogDescription>
            Update notes for this order. Only draft and pending orders can be
            edited.
          </DialogDescription>
        </DialogHeader>
        <form className="space-y-4" onSubmit={onSubmit}>
          <Field>
            <Label htmlFor="order_notes">Notes</Label>
            <Textarea id="order_notes" rows={3} {...register("notes")} />
            {errors.notes ? (
              <FieldError>{errors.notes.message}</FieldError>
            ) : null}
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
              Save notes
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function OrderDetailHeaderActions({
  order,
  actionPending,
  submitMutation,
  confirmMutation,
  shipMutation,
  deliverMutation,
  onEditNotes,
  onCancel,
  onDelete,
}) {
  const { primary, secondary, more } = useMemo(() => {
    const menuItems = [];

    const addMenuItem = (item) => {
      menuItems.push(item);
    };

    let primaryAction = null;
    let secondaryAction = null;

    if (order.status === "DRAFT") {
      primaryAction = {
        label: "Submit order",
        loading: submitMutation.isPending,
        onClick: () => submitMutation.mutate(),
      };
      secondaryAction = {
        label: "Edit notes",
        onClick: onEditNotes,
      };
      addMenuItem({
        label: "Delete",
        variant: "destructive",
        onClick: onDelete,
      });
    } else if (order.status === "PENDING") {
      primaryAction = {
        label: "Confirm",
        loading: confirmMutation.isPending,
        onClick: () => confirmMutation.mutate(),
      };
      secondaryAction = {
        label: "Cancel order",
        onClick: onCancel,
        destructive: true,
      };
      addMenuItem({ label: "Edit notes", onClick: onEditNotes });
      addMenuItem({
        label: "Delete",
        variant: "destructive",
        onClick: onDelete,
      });
    } else if (order.status === "CONFIRMED") {
      primaryAction = {
        label: "Mark shipped",
        loading: shipMutation.isPending,
        onClick: () => shipMutation.mutate(),
      };
      secondaryAction = {
        label: "Cancel order",
        onClick: onCancel,
        destructive: true,
      };
    } else if (order.status === "SHIPPED") {
      primaryAction = {
        label: "Mark delivered",
        loading: deliverMutation.isPending,
        onClick: () => deliverMutation.mutate(),
      };
    }

    return {
      primary: primaryAction,
      secondary: secondaryAction,
      more: menuItems,
    };
  }, [
    order.status,
    submitMutation,
    confirmMutation,
    shipMutation,
    deliverMutation,
    onEditNotes,
    onCancel,
    onDelete,
  ]);

  return (
    <div className="flex items-center gap-2">
      {primary ? (
        <Button
          loading={primary.loading}
          disabled={actionPending}
          onClick={primary.onClick}
        >
          {primary.label}
        </Button>
      ) : null}

      {secondary ? (
        <Button
          variant="outline"
          className={
            secondary.destructive
              ? "text-destructive hover:text-destructive"
              : undefined
          }
          disabled={actionPending}
          onClick={secondary.onClick}
        >
          {secondary.label}
        </Button>
      ) : null}

      {more.length > 0 ? (
        <DropdownMenu>
          <DropdownMenuTrigger
            render={
              <Button
                variant="outline"
                disabled={actionPending}
                aria-label="More actions"
              />
            }
          >
            <DotsThreeIcon />
            More
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="min-w-40">
            {more.map((item) => (
              <DropdownMenuItem
                key={item.label}
                variant={item.variant}
                onClick={item.onClick}
              >
                {item.label}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      ) : null}
    </div>
  );
}

function OrderDetailPage() {
  const { businessId, orderId } = useParams({ strict: false });
  const { data: order } = useSuspenseQuery(
    orderQueryOptions(businessId, orderId),
  );

  const [notesOpen, setNotesOpen] = useState(false);
  const [cancelOpen, setCancelOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

  const submitMutation = useSubmitOrderMutation(businessId, orderId);
  const confirmMutation = useConfirmOrderMutation(businessId, orderId);
  const shipMutation = useShipOrderMutation(businessId, orderId);
  const deliverMutation = useDeliverOrderMutation(businessId, orderId);
  const cancelMutation = useCancelOrderMutation(businessId, orderId);
  const deleteMutation = useDeleteOrderMutation(businessId);

  const isDraft = order.status === "DRAFT";
  const isPending = order.status === "PENDING";

  const actionPending =
    submitMutation.isPending ||
    confirmMutation.isPending ||
    shipMutation.isPending ||
    deliverMutation.isPending ||
    cancelMutation.isPending ||
    deleteMutation.isPending;

  return (
    <ListPage>
      <PageHeader
        title={`Order #${order.id}`}
        back={
          <Button
            variant="outline"
            size="icon"
            aria-label="Back to orders"
            render={
              <Link
                to="/$businessId/orders"
                params={{ businessId }}
              />
            }
          >
            <ArrowLeftIcon />
          </Button>
        }
        actions={
          <OrderDetailHeaderActions
            order={order}
            actionPending={actionPending}
            submitMutation={submitMutation}
            confirmMutation={confirmMutation}
            shipMutation={shipMutation}
            deliverMutation={deliverMutation}
            onEditNotes={() => setNotesOpen(true)}
            onCancel={() => setCancelOpen(true)}
            onDelete={() => setDeleteOpen(true)}
          />
        }
      />

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
        <Card>
          <CardContent className="pt-6">
            <div className="overflow-hidden rounded-lg border border-border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Product</TableHead>
                    <TableHead>SKU</TableHead>
                    <TableHead>Qty</TableHead>
                    <TableHead>Unit price</TableHead>
                    <TableHead className="text-right">Line total</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {order.lines.map((line) => (
                    <TableRow key={line.id}>
                      <TableCell className="font-medium">
                        {line.product_name}
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {line.product_sku}
                      </TableCell>
                      <TableCell>{line.quantity}</TableCell>
                      <TableCell>{formatCurrency(line.unit_price)}</TableCell>
                      <TableCell className="text-right">
                        {formatCurrency(line.line_total)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            <div className="mt-4 flex justify-end text-sm">
              <span className="text-muted-foreground">Total</span>
              <span className="ml-3 text-base font-semibold">
                {formatCurrency(order.total_amount)}
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="space-y-4 pt-6">
            <div>
              <p className="text-sm text-muted-foreground">Status</p>
              <Badge
                className="mt-1"
                variant={orderStatusVariant(order.status)}
              >
                {formatStatus(order.status)}
              </Badge>
            </div>

            <div>
              <p className="text-sm text-muted-foreground">Customer</p>
              <p className="mt-1 font-medium">{order.customer.name}</p>
              <p className="text-sm text-muted-foreground">
                {order.customer.email}
              </p>
            </div>

            <div>
              <p className="text-sm text-muted-foreground">Created</p>
              <p className="mt-1 text-sm">{formatDate(order.created_at)}</p>
            </div>

            <div>
              <p className="text-sm text-muted-foreground">Updated</p>
              <p className="mt-1 text-sm">{formatDate(order.updated_at)}</p>
            </div>

            <div>
              <p className="text-sm text-muted-foreground">Notes</p>
              <p className="mt-1 text-sm whitespace-pre-wrap">
                {order.notes || "—"}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      <OrderNotesDialog
        open={notesOpen}
        order={order}
        businessId={businessId}
        onClose={() => setNotesOpen(false)}
      />

      <Dialog
        open={cancelOpen}
        onOpenChange={(open) => {
          if (!open) setCancelOpen(false);
        }}
      >
        <DialogContent showClose={false}>
          <DialogHeader>
            <DialogTitle>Cancel order</DialogTitle>
            <DialogDescription>
              Cancel this order and restore inventory for all line items?
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCancelOpen(false)}>
              Keep order
            </Button>
            <Button
              variant="destructive"
              loading={cancelMutation.isPending}
              onClick={async () => {
                await cancelMutation.mutateAsync();
                setCancelOpen(false);
              }}
            >
              Cancel order
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog
        open={deleteOpen}
        onOpenChange={(open) => {
          if (!open) setDeleteOpen(false);
        }}
      >
        <DialogContent showClose={false}>
          <DialogHeader>
            <DialogTitle>Delete order</DialogTitle>
            <DialogDescription>
              Permanently delete this order
              {isPending ? " and restore inventory" : ""}? This action cannot be
              undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteOpen(false)}>
              Keep order
            </Button>
            <Button
              variant="destructive"
              loading={deleteMutation.isPending}
              onClick={async () => {
                await deleteMutation.mutateAsync(orderId);
                setDeleteOpen(false);
              }}
            >
              Delete order
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </ListPage>
  );
}

export { OrderDetailPage };
