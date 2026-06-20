import { Logo } from "@/components/shared/logo";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

function AuthLayout({ title, description, children }) {
  return (
    <div className="grid min-h-svh bg-background lg:grid-cols-1">
      <div className="flex items-center justify-center p-6 md:p-10">
        <div className="w-full max-w-sm space-y-6 ">
          <Logo className="lg:hidden" />
          <Card className="border-border/80 shadow-md">
            <CardHeader>
              <CardTitle>{title}</CardTitle>
              {description ? (
                <CardDescription>{description}</CardDescription>
              ) : null}
            </CardHeader>
            <CardContent>{children}</CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

export { AuthLayout };
