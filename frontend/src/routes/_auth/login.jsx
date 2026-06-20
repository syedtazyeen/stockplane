import { createFileRoute } from "@tanstack/react-router";

import { AuthLayout } from "@/components/auth/auth-layout";
import { LoginForm } from "@/components/auth/login-form";

export const Route = createFileRoute("/_auth/login")({
  validateSearch: (search) => ({
    redirect: typeof search.redirect === "string" ? search.redirect : undefined,
  }),
  component: LoginRoute,
});

function LoginRoute() {
  const { redirect } = Route.useSearch();

  return (
    <AuthLayout
      title="Sign in"
      description="Enter your credentials to access your workspace."
    >
      <LoginForm redirectTo={redirect} />
    </AuthLayout>
  );
}
