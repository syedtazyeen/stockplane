import { Link, useParams } from "@tanstack/react-router";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { PlusIcon } from "@phosphor-icons/react";

import { ordersQueryOptions } from "@/api/orders";
import { ListPagination } from "@/components/shared/list-pagination";
import { ListPage, ListStickyHeader, ListToolbar, ListTableScroll } from "@/components/shared/list-page";
import { ListResultsPanel } from "@/components/shared/list-results-panel";
import { PageHeader } from "@/components/shared/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useListUrlState } from "@/hooks/use-list-url-state";
import {
  formatCurrency,
  formatDate,
  formatStatus,
  orderStatusVariant,
} from "@/lib/format";
import { hasNextPage, toOrdersApiParams } from "@/lib/list-search";

function OrdersPage({
  title = "Orders",
  routePath = "/_main/$businessId/orders/",
  fixedStatus,
  emptyTitle = "No orders found",
  emptyDescription,
  showCreateAction = true,
}) {
  const { businessId } = useParams({ strict: false });
  const { searchParams, page, updateSearch, setPage } =
    useListUrlState(routePath);

  const apiParams = toOrdersApiParams(searchParams, { fixedStatus });

  const {
    data: orders = [],
    isLoading,
    isFetching,
    isError,
    error,
    refetch,
  } = useQuery({
    ...ordersQueryOptions(businessId, apiParams),
    placeholderData: keepPreviousData,
  });

  const activeStatus = fixedStatus ?? searchParams.status ?? "";
  const showNextPage = hasNextPage(orders.length);

  const resolvedEmptyDescription =
    emptyDescription ??
    (activeStatus
      ? "Try adjusting your filters."
      : "Get started by creating your first order.");

  return (
    <ListPage>
      <ListStickyHeader>
        <PageHeader
          title={title}
          actions={
            showCreateAction ? (
              <Button
                render={
                  <Link
                    to="/$businessId/orders/new"
                    params={{ businessId }}
                  />
                }
              >
                <PlusIcon />
                Create order
              </Button>
            ) : null
          }
        />

        {!fixedStatus ? (
          <ListToolbar>
            <Select
              className="h-9 w-full border-0 bg-muted/50 shadow-none sm:w-48"
              value={searchParams.status ?? ""}
              onChange={(event) =>
                updateSearch(
                  { status: event.target.value || undefined },
                  { resetPage: true },
                )
              }
            >
              <option value="">All statuses</option>
              <option value="PENDING">Pending</option>
              <option value="CONFIRMED">Confirmed</option>
              <option value="SHIPPED">Shipped</option>
              <option value="DELIVERED">Delivered</option>
              <option value="CANCELLED">Cancelled</option>
            </Select>
          </ListToolbar>
        ) : null}
      </ListStickyHeader>

      <ListResultsPanel
        isLoading={isLoading}
        isFetching={isFetching}
        isError={isError}
        error={error}
        onRetry={() => refetch()}
        isEmpty={orders.length === 0}
        emptyState={
          <div className="px-6 py-16 text-center">
            <p className="text-sm font-medium">{emptyTitle}</p>
            <p className="mt-1 text-sm text-muted-foreground">
              {resolvedEmptyDescription}
            </p>
            {showCreateAction && !activeStatus && page === 1 ? (
              <Button
                className="mt-4"
                render={
                  <Link
                    to="/$businessId/orders/new"
                    params={{ businessId }}
                  />
                }
              >
                <PlusIcon />
                Create order
              </Button>
            ) : null}
          </div>
        }
      >
        <ListTableScroll>
          <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Customer</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Items</TableHead>
              <TableHead>Total</TableHead>
              <TableHead>Created</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {orders.map((order) => (
              <TableRow key={order.id}>
                <TableCell>
                  <div className="min-w-0">
                    <div className="truncate font-medium">
                      {order.customer?.name ?? "Unknown customer"}
                    </div>
                    <div className="truncate text-sm text-muted-foreground">
                      {order.customer?.email ?? "—"}
                    </div>
                  </div>
                </TableCell>
                <TableCell>
                  <Badge variant={orderStatusVariant(order.status)}>
                    {formatStatus(order.status)}
                  </Badge>
                </TableCell>
                <TableCell>{order.lines.length}</TableCell>
                <TableCell>{formatCurrency(order.total_amount)}</TableCell>
                <TableCell className="text-muted-foreground">
                  {formatDate(order.created_at)}
                </TableCell>
                <TableCell className="text-right">
                  <Button
                    variant="ghost"
                    size="sm"
                    render={
                      <Link
                        to="/$businessId/orders/$orderId"
                        params={{ businessId, orderId: order.id }}
                      />
                    }
                  >
                    View
                  </Button>
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
    </ListPage>
  );
}

export { OrdersPage };
