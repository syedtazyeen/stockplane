import { Button } from "@/components/ui/button";

function ListPagination({ page, hasNextPage, onPageChange }) {
  if (page <= 1 && !hasNextPage) {
    return null;
  }

  return (
    <div className="flex items-center justify-between gap-4 px-1 py-2">
      <p className="text-sm text-muted-foreground">Page {page}</p>
      <div className="flex gap-2">
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          Previous
        </Button>
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={!hasNextPage}
          onClick={() => onPageChange(page + 1)}
        >
          Next
        </Button>
      </div>
    </div>
  );
}

export { ListPagination };
