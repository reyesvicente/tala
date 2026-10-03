import { Card, CardDescription, CardTitle } from "ice-ds";
import type { ReactNode } from "react";

interface AuthCardProps {
  title: string;
  description?: string;
  children: ReactNode;
  footer?: ReactNode;
}

export function AuthCard({ title, description, children, footer }: AuthCardProps) {
  return (
    <div className="mx-auto max-w-md space-y-4">
      <Card elevation="lg" className="space-y-6 bg-white">
        <div className="space-y-2">
          <CardTitle className="text-3xl">{title}</CardTitle>
          {description && <CardDescription>{description}</CardDescription>}
        </div>
        {children}
      </Card>
      {footer && <div className="text-center text-sm">{footer}</div>}
    </div>
  );
}
