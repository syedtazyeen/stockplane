import { cn } from "@/lib/utils";

function ListPage({ children, className }) {
  return (
    <div className={cn("flex flex-col gap-4", className)}>{children}</div>
  );
}

function ListStickyHeader({ children, className }) {
  return (
    <div
      className={cn(
        "sticky top-0 z-10 -mx-4 space-y-4 bg-background/95 px-4 py-4 backdrop-blur md:-mx-6 md:px-6",
        className,
      )}
    >
      {children}
    </div>
  );
}

function ListToolbar({ children, className }) {
  return (
    <div
      className={cn(
        "flex flex-col gap-3 rounded-xl border border-border bg-card p-3 sm:flex-row sm:items-center",
        className,
      )}
    >
      {children}
    </div>
  );
}

function ListPanel({ children, className }) {
  return (
    <div
      className={cn(
        "rounded-xl border border-border bg-card",
        className,
      )}
    >
      {children}
    </div>
  );
}

function ListTableScroll({ children, className }) {
  return (
    <div className={cn("overflow-x-auto", className)}>{children}</div>
  );
}

export { ListPage, ListStickyHeader, ListToolbar, ListPanel, ListTableScroll };
