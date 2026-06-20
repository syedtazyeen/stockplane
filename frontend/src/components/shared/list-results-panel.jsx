import { PageSpinner } from "@/components/shared/page-spinner";
import { Button } from "@/components/ui/button";
import { getApiErrorMessage } from "@/lib/api-client";
import { cn } from "@/lib/utils";

import { ListPanel } from "./list-page";

function ListResultsPanel({
  isLoading,
  isFetching,
  isError,
  error,
  onRetry,
  isEmpty,
  emptyState,
  children,
  className,
}) {
  if (isLoading) {
    return (
      <ListPanel className={className}>
        <PageSpinner size="sm" />
      </ListPanel>
    );
  }

  if (isError) {
    return (
      <ListPanel className={className}>
        <div className="px-6 py-16 text-center">
          <p className="text-sm font-medium">Could not load data</p>
          <p className="mt-1 text-sm text-muted-foreground">
            {getApiErrorMessage(error, "Something went wrong. Please try again.")}
          </p>
          {onRetry ? (
            <Button className="mt-4" variant="outline" onClick={onRetry}>
              Try again
            </Button>
          ) : null}
        </div>
      </ListPanel>
    );
  }

  const content = isEmpty ? emptyState : children;

  return (
    <ListPanel className={cn("relative", className)}>
      {isFetching ? (
        <div
          data-slot="list-loading-bar-track"
          className="absolute inset-x-0 top-0 z-10 h-0.5 overflow-hidden bg-muted"
        >
          <div
            data-slot="list-loading-bar"
            className="h-full w-1/3 bg-primary"
          />
        </div>
      ) : null}
      <div
        className={cn(
          "transition-opacity duration-150",
          isFetching && "opacity-60",
        )}
      >
        {content}
      </div>
    </ListPanel>
  );
}

export { ListResultsPanel };
