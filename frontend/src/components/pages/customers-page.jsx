import { zodResolver } from "@hookform/resolvers/zod";
import { useParams } from "@tanstack/react-router";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { MagnifyingGlassIcon, PlusIcon } from "@phosphor-icons/react";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";

import { customersQueryOptions } from "@/api/customers";
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
import {
  useCreateCustomerMutation,
  useDeleteCustomerMutation,
  useUpdateCustomerMutation,
} from "@/hooks/use-customers";
import {
  useDebouncedListSearch,
  useListUrlState,
} from "@/hooks/use-list-url-state";
import { formatDate, formatStatus } from "@/lib/format";
import { hasNextPage, toCustomersApiParams } from "@/lib/list-search";
import { INDIAN_COUNTRY_CODE, formatIndianPhone, parseIndianPhone } from "@/lib/phone";
import { customerFormSchema, toCustomerPayload } from "@/lib/schemas/customer";

const customersRoutePath = "/_main/$businessId/customers";

function customerStatusVariant(status) {
  if (status === "ACTIVE") return "success";
  if (status === "SUSPENDED") return "destructive";
  return "secondary";
}

const defaultFormValues = {
  name: "",
  email: "",
  country_code: INDIAN_COUNTRY_CODE,
  phone_number: "",
  status: "ACTIVE",
};

function CustomerFormDialog({ open, customer, businessId, onClose }) {
  const isEdit = Boolean(customer);
  const createMutation = useCreateCustomerMutation(businessId);
  const updateMutation = useUpdateCustomerMutation(businessId);
  const mutation = isEdit ? updateMutation : createMutation;

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(customerFormSchema),
    defaultValues: defaultFormValues,
  });

  useEffect(() => {
    if (!open) return;

    if (customer) {
      const { nationalNumber } = parseIndianPhone(customer.phone);
      reset({
        name: customer.name,
        email: customer.email,
        country_code: INDIAN_COUNTRY_CODE,
        phone_number: nationalNumber,
        status: customer.status,
      });
      return;
    }

    reset(defaultFormValues);
  }, [open, customer, reset]);

  const onSubmit = handleSubmit(async (values) => {
    const payload = isEdit
      ? toCustomerPayload(values)
      : { ...toCustomerPayload(values), status: "ACTIVE" };

    if (isEdit) {
      await updateMutation.mutateAsync({
        customerId: customer.id,
        payload,
      });
    } else {
      await createMutation.mutateAsync(payload);
    }

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
          <DialogTitle>{isEdit ? "Edit customer" : "Add customer"}</DialogTitle>
          <DialogDescription>
            {isEdit
              ? "Update customer contact details and status."
              : "Add a new customer to your business."}
          </DialogDescription>
        </DialogHeader>

        <form className="space-y-4" onSubmit={onSubmit}>
          <Field>
            <Label htmlFor="customer_name">Name</Label>
            <Input
              id="customer_name"
              aria-invalid={Boolean(errors.name)}
              {...register("name")}
            />
            {errors.name ? (
              <FieldError>{errors.name.message}</FieldError>
            ) : null}
          </Field>

          <Field>
            <Label htmlFor="customer_email">Email</Label>
            <Input
              id="customer_email"
              type="email"
              aria-invalid={Boolean(errors.email)}
              {...register("email")}
            />
            {errors.email ? (
              <FieldError>{errors.email.message}</FieldError>
            ) : null}
          </Field>

          <Field>
            <Label htmlFor="customer_phone">Phone</Label>
            <div className="flex gap-2">
              <Select
                id="customer_country_code"
                className="w-20 shrink-0"
                disabled
                {...register("country_code")}
              >
                <option value={INDIAN_COUNTRY_CODE}>+91</option>
              </Select>
              <Input
                id="customer_phone"
                className="min-w-0 flex-1"
                inputMode="numeric"
                autoComplete="tel-national"
                aria-invalid={Boolean(errors.phone_number)}
                {...register("phone_number")}
              />
            </div>
            {errors.phone_number ? (
              <FieldError>{errors.phone_number.message}</FieldError>
            ) : null}
          </Field>

          {isEdit ? (
            <Field>
              <Label htmlFor="customer_status">Status</Label>
              <Select id="customer_status" {...register("status")}>
                <option value="ACTIVE">Active</option>
                <option value="INACTIVE">Inactive</option>
                <option value="SUSPENDED">Suspended</option>
              </Select>
            </Field>
          ) : null}

          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              type="submit"
              loading={isSubmitting || mutation.isPending}
              disabled={isSubmitting || mutation.isPending}
            >
              {isEdit ? "Save changes" : "Add customer"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function CustomersPage() {
  const { businessId } = useParams({ strict: false });
  const { searchParams, page, updateSearch, setPage } =
    useListUrlState(customersRoutePath);
  const { inputValue: search, setInputValue: setSearch } =
    useDebouncedListSearch(customersRoutePath);
  const [formOpen, setFormOpen] = useState(false);
  const [editTarget, setEditTarget] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);

  const apiParams = toCustomersApiParams(searchParams);

  const {
    data: customers = [],
    isLoading,
    isFetching,
    isError,
    error,
    refetch,
  } = useQuery({
    ...customersQueryOptions(businessId, apiParams),
    placeholderData: keepPreviousData,
  });

  const deleteMutation = useDeleteCustomerMutation(businessId);
  const showNextPage = hasNextPage(customers.length);

  return (
    <ListPage>
      <ListStickyHeader>
        <PageHeader
          title="Customers"
          actions={
            <Button
              onClick={() => {
                setEditTarget(null);
                setFormOpen(true);
              }}
            >
              <PlusIcon />
              Add customer
            </Button>
          }
        />

        <ListToolbar>
          <div className="relative min-w-0 flex-1">
            <MagnifyingGlassIcon className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              className="h-9 border-0 bg-muted/50 pl-9 shadow-none focus-visible:ring-0"
              placeholder="Search customers"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </div>
          <Select
            className="h-9 w-full border-0 bg-muted/50 shadow-none sm:w-40"
            value={searchParams.status ?? ""}
            onChange={(event) =>
              updateSearch(
                { status: event.target.value || undefined },
                { resetPage: true },
              )
            }
          >
            <option value="">All statuses</option>
            <option value="ACTIVE">Active</option>
            <option value="INACTIVE">Inactive</option>
            <option value="SUSPENDED">Suspended</option>
          </Select>
        </ListToolbar>
      </ListStickyHeader>

      <ListResultsPanel
        isLoading={isLoading}
        isFetching={isFetching}
        isError={isError}
        error={error}
        onRetry={() => refetch()}
        isEmpty={customers.length === 0}
        emptyState={
          <div className="px-6 py-16 text-center">
            <p className="text-sm font-medium">No customers found</p>
            <p className="mt-1 text-sm text-muted-foreground">
              {searchParams.search || searchParams.status
                ? "Try adjusting your search or filters."
                : "Add your first customer to get started."}
            </p>
            {!searchParams.search && !searchParams.status && page === 1 ? (
              <Button
                className="mt-4"
                onClick={() => {
                  setEditTarget(null);
                  setFormOpen(true);
                }}
              >
                <PlusIcon />
                Add customer
              </Button>
            ) : null}
          </div>
        }
      >
        <ListTableScroll>
          <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Phone</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Updated</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {customers.map((customer) => (
              <TableRow key={customer.id}>
                <TableCell className="font-medium">{customer.name}</TableCell>
                <TableCell className="text-muted-foreground">
                  {customer.email}
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {formatIndianPhone(customer.phone)}
                </TableCell>
                <TableCell>
                  <Badge variant={customerStatusVariant(customer.status)}>
                    {formatStatus(customer.status)}
                  </Badge>
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {formatDate(customer.updated_at)}
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setEditTarget(customer);
                        setFormOpen(true);
                      }}
                    >
                      Edit
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-destructive hover:text-destructive"
                      onClick={() => setDeleteTarget(customer)}
                    >
                      Delete
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

      <CustomerFormDialog
        open={formOpen}
        customer={editTarget}
        businessId={businessId}
        onClose={() => {
          setFormOpen(false);
          setEditTarget(null);
        }}
      />

      <Dialog
        open={Boolean(deleteTarget)}
        onOpenChange={(open) => {
          if (!open) setDeleteTarget(null);
        }}
      >
        <DialogContent showClose={false}>
          <DialogHeader>
            <DialogTitle>Delete customer</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete &ldquo;{deleteTarget?.name}
              &rdquo;? This will remove the customer from active use.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteTarget(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              loading={deleteMutation.isPending}
              onClick={async () => {
                await deleteMutation.mutateAsync(deleteTarget.id);
                setDeleteTarget(null);
              }}
            >
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </ListPage>
  );
}

export { CustomersPage };
