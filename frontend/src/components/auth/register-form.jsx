import { zodResolver } from "@hookform/resolvers/zod";
import { Link } from "@tanstack/react-router";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Field, FieldError } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useRegisterMutation } from "@/hooks/use-auth";
import { registerSchema } from "@/lib/schemas/auth";

function RegisterForm() {
  const registerMutation = useRegisterMutation();
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      email: "",
      password: "",
      full_name: "",
      business_name: "",
    },
  });

  const onSubmit = handleSubmit(async (values) => {
    const payload = {
      email: values.email,
      password: values.password,
      business_name: values.business_name,
      ...(values.full_name ? { full_name: values.full_name } : {}),
    };

    await registerMutation.mutateAsync(payload);
  });

  return (
    <form className="space-y-4" onSubmit={onSubmit}>
      <Field>
        <Label htmlFor="full_name">Full name</Label>
        <Input
          id="full_name"
          autoComplete="name"
          aria-invalid={Boolean(errors.full_name)}
          {...register("full_name")}
        />
        {errors.full_name ? (
          <FieldError>{errors.full_name.message}</FieldError>
        ) : null}
      </Field>

      <Field>
        <Label htmlFor="business_name">Business name</Label>
        <Input
          id="business_name"
          autoComplete="company"
          aria-invalid={Boolean(errors.business_name)}
          {...register("business_name")}
        />
        {errors.business_name ? (
          <FieldError>{errors.business_name.message}</FieldError>
        ) : null}
      </Field>

      <Field>
        <Label htmlFor="email">Email</Label>
        <Input
          id="email"
          type="email"
          autoComplete="email"
          aria-invalid={Boolean(errors.email)}
          {...register("email")}
        />
        {errors.email ? <FieldError>{errors.email.message}</FieldError> : null}
      </Field>

      <Field>
        <Label htmlFor="password">Password</Label>
        <Input
          id="password"
          type="password"
          autoComplete="new-password"
          aria-invalid={Boolean(errors.password)}
          {...register("password")}
        />
        {errors.password ? (
          <FieldError>{errors.password.message}</FieldError>
        ) : null}
      </Field>

      <Button
        type="submit"
        className="w-full"
        size="lg"
        loading={isSubmitting || registerMutation.isPending}
        disabled={isSubmitting || registerMutation.isPending}
      >
        Create account
      </Button>

      <p className="text-center text-sm text-muted-foreground">
        Already have an account?{" "}
        <Link
          to="/login"
          className="font-medium text-primary underline-offset-4 hover:underline"
        >
          Sign in
        </Link>
      </p>
    </form>
  );
}

export { RegisterForm };
