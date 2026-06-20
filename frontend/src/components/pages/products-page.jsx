import { Link, useParams } from "@tanstack/react-router";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { ImageIcon, MagnifyingGlassIcon, PlusIcon } from "@phosphor-icons/react";
import { useState } from "react";

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
import { Input } from "@/components/ui/input";
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
  useDebouncedListSearch,
  useListUrlState,
} from "@/hooks/use-list-url-state";
import { useDeleteProductMutation } from "@/hooks/use-products";
import { formatCurrency, formatStatus } from "@/lib/format";
import { hasNextPage, toProductsApiParams } from "@/lib/list-search";

const productsRoutePath = "/_main/$businessId/products/";

function productStatusVariant(status) {
  if (status === "ACTIVE") return "success";
  if (status === "DRAFT") return "info";
  return "outline";
}

function StockCell({ quantity }) {
  const label = `${quantity} in stock`;

  if (quantity === 0) {
    return <span className="font-medium text-destructive">{label}</span>;
  }

  return <span className="text-foreground">{label}</span>;
}

function ProductsPage() {
  const { businessId } = useParams({ strict: false });
  const { searchParams, page, updateSearch, setPage } =
    useListUrlState(productsRoutePath);
  const { inputValue: search, setInputValue: setSearch } =
    useDebouncedListSearch(productsRoutePath);
  const [deleteTarget, setDeleteTarget] = useState(null);

  const apiParams = toProductsApiParams(searchParams);

  const {
    data: products = [],
    isLoading,
    isFetching,
    isError,
    error,
    refetch,
  } = useQuery({
    ...productsQueryOptions(businessId, apiParams),
    placeholderData: keepPreviousData,
  });

  const deleteMutation = useDeleteProductMutation(businessId);
  const showNextPage = hasNextPage(products.length);

  return (
    <ListPage>
      <ListStickyHeader>
        <PageHeader
          title="Products"
          actions={
            <Button
              render={
                <Link
                  to="/$businessId/products/new"
                  params={{ businessId }}
                />
              }
            >
              <PlusIcon />
              Add product
            </Button>
          }
        />

        <ListToolbar>
          <div className="relative min-w-0 flex-1">
            <MagnifyingGlassIcon className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              className="h-9 border-0 bg-muted/50 pl-9 shadow-none focus-visible:ring-0"
              placeholder="Search products"
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
            <option value="DRAFT">Draft</option>
            <option value="ACTIVE">Active</option>
            <option value="ARCHIVED">Archived</option>
          </Select>
        </ListToolbar>
      </ListStickyHeader>

      <ListResultsPanel
        isLoading={isLoading}
        isFetching={isFetching}
        isError={isError}
        error={error}
        onRetry={() => refetch()}
        isEmpty={products.length === 0}
        emptyState={
          <div className="px-6 py-16 text-center">
            <p className="text-sm font-medium">No products found</p>
            <p className="mt-1 text-sm text-muted-foreground">
              {searchParams.search || searchParams.status
                ? "Try adjusting your search or filters."
                : "Get started by adding your first product."}
            </p>
            {!searchParams.search && !searchParams.status && page === 1 ? (
              <Button
                className="mt-4"
                render={
                  <Link
                    to="/$businessId/products/new"
                    params={{ businessId }}
                  />
                }
              >
                <PlusIcon />
                Add product
              </Button>
            ) : null}
          </div>
        }
      >
        <ListTableScroll>
          <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[40%]">Product</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Inventory</TableHead>
              <TableHead>Price</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {products.map((product) => (
              <TableRow key={product.id}>
                <TableCell>
                  <div className="flex items-center gap-3">
                    <div className="flex size-10 shrink-0 items-center justify-center rounded-lg border border-border bg-muted/40 text-muted-foreground">
                      <ImageIcon className="size-4" />
                    </div>
                    <div className="min-w-0">
                      <div className="truncate font-medium">{product.name}</div>
                      <div className="truncate text-sm text-muted-foreground">
                        {product.sku}
                      </div>
                    </div>
                  </div>
                </TableCell>
                <TableCell>
                  <Badge variant={productStatusVariant(product.status)}>
                    {formatStatus(product.status)}
                  </Badge>
                </TableCell>
                <TableCell>
                  <StockCell quantity={product.quantity} />
                </TableCell>
                <TableCell>{formatCurrency(product.selling_price)}</TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      render={
                        <Link
                          to="/$businessId/products/$productId"
                          params={{ businessId, productId: product.id }}
                        />
                      }
                    >
                      Edit
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-destructive hover:text-destructive"
                      onClick={() => setDeleteTarget(product)}
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

      <Dialog
        open={Boolean(deleteTarget)}
        onOpenChange={(open) => {
          if (!open) setDeleteTarget(null);
        }}
      >
        <DialogContent showClose={false}>
          <DialogHeader>
            <DialogTitle>Delete product</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete &ldquo;{deleteTarget?.name}
              &rdquo;? This action cannot be undone.
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

export { ProductsPage };
