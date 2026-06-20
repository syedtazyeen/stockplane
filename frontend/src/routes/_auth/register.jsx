import { createFileRoute } from "@tanstack/react-router";

import { AuthLayout } from "@/components/auth/auth-layout";
import { RegisterForm } from "@/components/auth/register-form";

export const Route = createFileRoute("/_auth/register")({
  component: RegisterRoute,
});

function RegisterRoute() {
  return (
    <AuthLayout
      title="Create your account"
      description="Register to set up your business on Stockplane."
    >
      <RegisterForm />
    </AuthLayout>
  );
}
