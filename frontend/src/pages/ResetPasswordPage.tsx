import { zodResolver } from "@hookform/resolvers/zod";
import { Alert, Button, Field, Input } from "ice-ds";
import { useForm } from "react-hook-form";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { useResetPassword } from "@/features/auth/api";
import { AuthCard } from "@/features/auth/components/AuthCard";
import { resetPasswordSchema, type ResetPasswordValues } from "@/features/auth/schema";

export default function ResetPasswordPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const token = params.get("token") ?? "";
  const reset = useResetPassword();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetPasswordValues>({ resolver: zodResolver(resetPasswordSchema) });

  if (!token) {
    return (
      <AuthCard title="Reset link missing">
        <Alert intent="warning" title="Open the link from your email, or request a new one." />
        <Link to="/forgot-password">
          <Button type="button" fullWidth>
            Request a new link
          </Button>
        </Link>
      </AuthCard>
    );
  }

  const onSubmit = handleSubmit(({ password }) =>
    reset.mutate({ token, password }, { onSuccess: () => navigate("/history") }),
  );

  return (
    <AuthCard
      title="Set a new password"
      description="You'll be logged out everywhere else once it's changed."
    >
      <form onSubmit={onSubmit} className="space-y-4" noValidate>
        <Field label="New password" htmlFor="password" hint="At least 8 characters." error={errors.password?.message}>
          <Input id="password" type="password" autoComplete="new-password" {...register("password")} />
        </Field>
        <Field label="Confirm new password" htmlFor="confirmPassword" error={errors.confirmPassword?.message}>
          <Input id="confirmPassword" type="password" autoComplete="new-password" {...register("confirmPassword")} />
        </Field>
        {reset.isError && (
          <Alert intent="error" title={reset.error.message}>
            <Link to="/forgot-password" className="underline">
              Request a new link
            </Link>
          </Alert>
        )}
        <Button type="submit" fullWidth size="lg" loading={reset.isPending}>
          Update password
        </Button>
      </form>
    </AuthCard>
  );
}
