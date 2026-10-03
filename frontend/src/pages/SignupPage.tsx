import { zodResolver } from "@hookform/resolvers/zod";
import { Alert, Button, Field, Input } from "ice-ds";
import { useForm } from "react-hook-form";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { useRegister } from "@/features/auth/api";
import { AuthCard } from "@/features/auth/components/AuthCard";
import { signupSchema, type SignupValues } from "@/features/auth/schema";
import { safeNext } from "@/lib/redirect";

export default function SignupPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const registerUser = useRegister();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SignupValues>({ resolver: zodResolver(signupSchema) });

  const onSubmit = handleSubmit(({ email, password }) =>
    registerUser.mutate({ email, password }, { onSuccess: () => navigate(safeNext(params.get("next"))) }),
  );

  return (
    <AuthCard
      title="Create an account"
      description="Optional. It keeps a list of your transcripts. Still no credit card."
      footer={
        <>
          Already have one?{" "}
          <Link to="/login" className="font-bold underline">
            Log in
          </Link>
        </>
      }
    >
      <form onSubmit={onSubmit} className="space-y-4" noValidate>
        <Field label="Email" htmlFor="email" error={errors.email?.message}>
          <Input id="email" type="email" autoComplete="email" {...register("email")} />
        </Field>
        <Field label="Password" htmlFor="password" hint="At least 8 characters." error={errors.password?.message}>
          <Input id="password" type="password" autoComplete="new-password" {...register("password")} />
        </Field>
        <Field label="Confirm password" htmlFor="confirmPassword" error={errors.confirmPassword?.message}>
          <Input id="confirmPassword" type="password" autoComplete="new-password" {...register("confirmPassword")} />
        </Field>
        {registerUser.isError && <Alert intent="error" title={registerUser.error.message} />}
        <Button type="submit" fullWidth size="lg" loading={registerUser.isPending}>
          Create account
        </Button>
      </form>
    </AuthCard>
  );
}
