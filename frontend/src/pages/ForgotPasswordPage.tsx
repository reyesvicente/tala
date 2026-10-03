import { zodResolver } from "@hookform/resolvers/zod";
import { Alert, Button, Field, Input } from "ice-ds";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";

import { useForgotPassword } from "@/features/auth/api";
import { AuthCard } from "@/features/auth/components/AuthCard";
import { forgotPasswordSchema, type ForgotPasswordValues } from "@/features/auth/schema";

export default function ForgotPasswordPage() {
  const forgot = useForgotPassword();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotPasswordValues>({ resolver: zodResolver(forgotPasswordSchema) });

  return (
    <AuthCard
      title="Forgot your password?"
      description="Enter your email and we'll send you a link to set a new one."
      footer={
        <Link to="/login" className="underline">
          Back to log in
        </Link>
      }
    >
      {forgot.isSuccess ? (
        <Alert intent="success" title="Check your inbox">
          If that email has an account, a reset link is on its way. It works for 60 minutes. Check your spam folder
          too.
        </Alert>
      ) : (
        <form onSubmit={handleSubmit((values) => forgot.mutate(values))} className="space-y-4" noValidate>
          <Field label="Email" htmlFor="email" error={errors.email?.message}>
            <Input id="email" type="email" autoComplete="email" {...register("email")} />
          </Field>
          {forgot.isError && <Alert intent="error" title={forgot.error.message} />}
          <Button type="submit" fullWidth size="lg" loading={forgot.isPending}>
            Send reset link
          </Button>
        </form>
      )}
    </AuthCard>
  );
}
