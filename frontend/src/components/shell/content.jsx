import { ScrollArea } from "@/components/ui/scroll-area";

export function Content({ children }) {
  return (
    <ScrollArea className="h-0 min-h-0 flex-1">
      <div className="p-4 md:p-6">{children}</div>
    </ScrollArea>
  );
}
