import { cn } from "@/lib/utils";

function Field({ className, ...props }) {
  return (
    <div
      data-slot="field"
      className={cn("flex flex-col gap-1.5", className)}
      {...props}
    />
  );
}

function FieldError({ className, ...props }) {
  return (
    <p
      data-slot="field-error"
      className={cn("text-sm text-destructive", className)}
      {...props}
    />
  );
}

export { Field, FieldError };
