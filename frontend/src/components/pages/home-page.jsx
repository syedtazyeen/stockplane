import { Link, useParams } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import {
  PackageIcon,
  TrayIcon,
  UsersIcon,
  WarningIcon,
} from "@phosphor-icons/react";

import { dashboardQueryOptions } from "@/api/dashboard";
import { ListPage, ListPanel, ListTableScroll } from "@/components/shared/list-page";
import { ListResultsPanel } from "@/components/shared/list-results-panel";
import { PageHeader } from "@/components/shared/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

function StatCard({ label, value, icon: Icon, href }) {
  const content = (
    <Card className="transition-colors hover:bg-muted/30">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {label}
        </CardTitle>
        <Icon className="size-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <p className="text-3xl font-semibold tracking-tight">{value}</p>
      </CardContent>
    </Card>
  );

  if (!href) {
    return content;
  }

  return (
    <Link to={href.to} params={href.params} className="block">
      {content}
    </Link>
  );
}

function HomePage() {
  const { businessId } = useParams({ strict: false });

  const {
    data,
    isLoading,
    isFetching,
    isError,
    error,
    refetch,
  } = useQuery(dashboardQueryOptions(businessId));

  const stats = data ?? {
    productCount: 0,
    customerCount: 0,
    orderCount: 0,
    lowStockCount: 0,
    lowStockItems: [],
  };

  return (
    <ListPage>
      <PageHeader
        title="Dashboard"
        description="Overview of your products, customers, orders, and inventory."
      />

      <ListResultsPanel
        isLoading={isLoading}
        isFetching={isFetching}
        isError={isError}
        error={error}
        onRetry={() => refetch()}
        isEmpty={false}
      >
        <div className="space-y-6 p-6">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <StatCard
              label="Total products"
              value={stats.productCount}
              icon={PackageIcon}
              href={{
                to: "/$businessId/products",
                params: { businessId },
              }}
            />
            <StatCard
              label="Total customers"
              value={stats.customerCount}
              icon={UsersIcon}
              href={{
                to: "/$businessId/customers",
                params: { businessId },
              }}
            />
            <StatCard
              label="Total orders"
              value={stats.orderCount}
              icon={TrayIcon}
              href={{
                to: "/$businessId/orders",
                params: { businessId },
              }}
            />
          </div>

          <div className="space-y-3">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-center gap-2">
                <WarningIcon className="size-5 text-amber-600" />
                <h2 className="text-lg font-semibold tracking-tight">
                  Low stock products
                </h2>
                <Badge variant="warning">{stats.lowStockCount}</Badge>
              </div>
              <Button
                variant="outline"
                size="sm"
                render={
                  <Link
                    to="/$businessId/inventory"
                    params={{ businessId }}
                    search={{ lowStock: "true" }}
                  />
                }
              >
                View all in inventory
              </Button>
            </div>

            {stats.lowStockItems.length === 0 ? (
              <ListPanel>
                <div className="px-6 py-10 text-center">
                  <p className="text-sm font-medium">All stocked up</p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    No products are currently low on stock.
                  </p>
                </div>
              </ListPanel>
            ) : (
              <ListPanel>
                <ListTableScroll>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Product</TableHead>
                        <TableHead>Available</TableHead>
                        <TableHead>On hand</TableHead>
                        <TableHead>Reorder point</TableHead>
                        <TableHead>Status</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {stats.lowStockItems.slice(0, 10).map((item) => (
                        <TableRow key={item.product_id}>
                          <TableCell className="font-medium">
                            {item.product?.name ?? item.product_id}
                          </TableCell>
                          <TableCell>{item.available_quantity}</TableCell>
                          <TableCell>{item.quantity_on_hand}</TableCell>
                          <TableCell className="text-muted-foreground">
                            {item.reorder_point ?? "—"}
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant={
                                item.quantity_on_hand === 0
                                  ? "destructive"
                                  : "warning"
                              }
                            >
                              {item.quantity_on_hand === 0
                                ? "Out of stock"
                                : "Low stock"}
                            </Badge>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </ListTableScroll>
              </ListPanel>
            )}
          </div>
        </div>
      </ListResultsPanel>
    </ListPage>
  );
}

export { HomePage };
