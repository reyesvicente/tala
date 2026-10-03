import { z } from "zod";

const email = z.email("Enter a valid email address.");
const password = z
  .string()
  .min(8, "Use at least 8 characters.")
  .max(128, "Keep it under 128 characters.");

export const loginSchema = z.object({
  email,
  password: z.string().min(1, "Enter your password."),
});

export const signupSchema = z
  .object({ email, password, confirmPassword: z.string() })
  .refine((values) => values.password === values.confirmPassword, {
    message: "Passwords don't match.",
    path: ["confirmPassword"],
  });

export const forgotPasswordSchema = z.object({ email });

export const resetPasswordSchema = z
  .object({ password, confirmPassword: z.string() })
  .refine((values) => values.password === values.confirmPassword, {
    message: "Passwords don't match.",
    path: ["confirmPassword"],
  });

export type LoginValues = z.infer<typeof loginSchema>;
export type SignupValues = z.infer<typeof signupSchema>;
export type ForgotPasswordValues = z.infer<typeof forgotPasswordSchema>;
export type ResetPasswordValues = z.infer<typeof resetPasswordSchema>;
