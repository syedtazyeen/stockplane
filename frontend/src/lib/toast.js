import { toast } from "sonner";

import { getApiErrorMessage } from "@/lib/api-client";

export function toastSuccess(message) {
  toast.success(message);
}

export function toastError(error, fallback = "Something went wrong.") {
  toast.error(getApiErrorMessage(error, fallback));
}
