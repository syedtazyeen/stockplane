const currencyFormatter = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
});

export function formatCurrency(value) {
  const amount = Number(value);
  if (Number.isNaN(amount)) return "—";
  return currencyFormatter.format(amount);
}

export function formatStatus(status) {
  if (!status) return "";
  return status
    .toLowerCase()
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export function formatDate(value) {
  if (!value) return "—";
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function orderStatusVariant(status) {
  if (status === "PENDING") return "warning";
  if (status === "CONFIRMED") return "info";
  if (status === "SHIPPED") return "default";
  if (status === "DELIVERED") return "success";
  if (status === "CANCELLED") return "destructive";
  if (status === "DRAFT") return "secondary";
  return "outline";
}
