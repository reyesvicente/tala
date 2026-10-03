import { zodResolver } from "@hookform/resolvers/zod";
import { Alert, Button, Field, Input } from "ice-ds";
import { useForm } from "react-hook-form";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { useLogin } from "@/features/auth/api";
import { AuthCard } from "@/features/auth/components/AuthCard";
import { loginSchema, type LoginValues } from "@/features/auth/schema";
import { safeNext } from "@/lib/redirect";

export default function LoginPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const login = useLogin();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginValues>({ resolver: zodResolver(loginSchema) });

  const onSubmit = handleSubmit((values) =>
    login.mutate(values, { onSuccess: () => navigate(safeNext(params.get("next"))) }),
  );

  return (
    <AuthCard
      title="Log in"
      description="See your transcripts on any device. You don't need an account to transcribe."
      footer={
        <>
          New here?{" "}
          <Link to="/signup" className="font-bold underline">
            Create an account
          </Link>
        </>
      }
    >
      <form onSubmit={onSubmit} className="space-y-4" noValidate>
        <Field label="Email" htmlFor="email" error={errors.email?.message}>
          <Input id="email" type="email" autoComplete="email" {...register("email")} />
        </Field>
        <Field label="Password" htmlFor="password" error={errors.password?.message}>
          <Input id="password" type="password" autoComplete="current-password" {...register("password")} />
        </Field>
        <div className="text-right text-sm">
          <Link to="/forgot-password" className="underline">
            Forgot password?
          </Link>
        </div>
        {login.isError && <Alert intent="error" title={login.error.message} />}
        <Button type="submit" fullWidth size="lg" loading={login.isPending}>
          Log in
        </Button>
      </form>
    </AuthCard>
  );
}
