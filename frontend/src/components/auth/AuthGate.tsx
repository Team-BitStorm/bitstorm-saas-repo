import { useNavigate, useRouterState } from "@tanstack/react-router";
import * as React from "react";

import { isAuthPublicPath } from "@/lib/auth";
import { useAuth } from "@/lib/auth-context";

export function AuthGate({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const navigate = useNavigate();

  React.useEffect(() => {
    if (isLoading) return;

    if (!isAuthenticated && !isAuthPublicPath(pathname)) {
      void navigate({
        to: "/login",
        search: { redirect: pathname },
      });
      return;
    }

    if (isAuthenticated && isAuthPublicPath(pathname)) {
      void navigate({ to: "/" });
    }
  }, [isAuthenticated, isLoading, pathname, navigate]);

  if (isLoading) {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-background">
        <p className="text-lg text-muted-foreground">…</p>
      </div>
    );
  }

  if (!isAuthenticated && !isAuthPublicPath(pathname)) {
    return null;
  }

  if (isAuthenticated && isAuthPublicPath(pathname)) {
    return null;
  }

  return <>{children}</>;
}
