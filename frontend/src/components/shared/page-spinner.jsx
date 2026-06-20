import { SpinnerIcon } from "@phosphor-icons/react";

import { cn } from "@/lib/utils";

function PageSpinner({ className, size = "default" }) {
  return (
    <div
      className={cn(
        "flex items-center justify-center",
        size === "sm" ? "py-16" : "min-h-[50vh]",
        className,
      )}
    >
      <SpinnerIcon
        className={cn(
          "animate-spin text-muted-foreground",
          size === "sm" ? "size-6" : "size-8",
        )}
      />
    </div>
  );
}

export { PageSpinner };
