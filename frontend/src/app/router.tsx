import { Skeleton } from "ice-ds";
import { lazy, Suspense, type ReactNode } from "react";
import { createBrowserRouter, Outlet, ScrollRestoration } from "react-router-dom";

import { Layout } from "@/components/Layout";

const HomePage = lazy(() => import("@/pages/HomePage"));
const TranscriptPage = lazy(() => import("@/pages/TranscriptPage"));
const NotFoundPage = lazy(() => import("@/pages/NotFoundPage"));

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
      { path: "*", element: page(<NotFoundPage />) },
    ],
  },
]);
