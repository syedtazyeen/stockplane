import { cn } from "@/lib/utils";

function Logo({className}) {
  return <div className={cn("text-lg font-bold italic", className)}>Stockplane</div>;
}

export { Logo };
