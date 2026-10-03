import { Skeleton } from "ice-ds";
import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { useMe } from "../api";

export function RequireAuth({ children }: { children: ReactNode }) {
  const { data: user, isPending } = useMe();
  const location = useLocation();

  if (isPending) return <Skeleton className="h-64 w-full" />;
  if (!user) return <Navigate to={`/login?next=${encodeURIComponent(location.pathname)}`} replace />;
  return <>{children}</>;
}
