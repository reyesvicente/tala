import { Skeleton } from "ice-ds";
import { lazy, Suspense, type ReactNode } from "react";
import { createBrowserRouter, Outlet, ScrollRestoration } from "react-router-dom";

import { Layout } from "@/components/Layout";
import { RequireAuth } from "@/features/auth/components/RequireAuth";

const HomePage = lazy(() => import("@/pages/HomePage"));
const TranscriptPage = lazy(() => import("@/pages/TranscriptPage"));
const NotFoundPage = lazy(() => import("@/pages/NotFoundPage"));
const LoginPage = lazy(() => import("@/pages/LoginPage"));
const SignupPage = lazy(() => import("@/pages/SignupPage"));
const ForgotPasswordPage = lazy(() => import("@/pages/ForgotPasswordPage"));
const ResetPasswordPage = lazy(() => import("@/pages/ResetPasswordPage"));
const HistoryPage = lazy(() => import("@/pages/HistoryPage"));

const page = (element: ReactNode) => <Suspense fallback={<Skeleton className="h-64 w-full" />}>{element}</Suspense>;

export const router = createBrowserRouter([
  {
    element: (
      <Layout>
        <Outlet />
        <ScrollRestoration />
      </Layout>
    ),
    children: [
      { path: "/", element: page(<HomePage />) },
      { path: "/t/:slug", element: page(<TranscriptPage />) },
      { path: "/login", element: page(<LoginPage />) },
      { path: "/signup", element: page(<SignupPage />) },
      { path: "/forgot-password", element: page(<ForgotPasswordPage />) },
      { path: "/reset-password", element: page(<ResetPasswordPage />) },
      {
        path: "/history",
        element: page(
          <RequireAuth>
            <HistoryPage />
          </RequireAuth>,
        ),
      },
      { path: "*", element: page(<NotFoundPage />) },
    ],
  },
]);
