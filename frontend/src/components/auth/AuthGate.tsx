import { useNavigate, useRouterState } from "@tanstack/react-router";
import * as React from "react";

import { getRoleHome, isAuthPublicPath, isProviderDashboardPath } from "@/lib/auth";
import { useAuth } from "@/lib/auth-context";

const CUSTOMER_ONBOARDING = "/onboarding";

export function AuthGate({ children }: { children: React.ReactNode }) {
  const { user, isAuthenticated, isLoading } = useAuth();
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
      void navigate({ to: getRoleHome(user!.role) });
      return;
    }

    if (!isAuthenticated || !user) return;

    const isProviderRoute = isProviderDashboardPath(pathname);
    const isCustomerRoute =
      pathname === "/" ||
      pathname.startsWith("/bookings") ||
      pathname.startsWith("/providers") ||
      pathname === CUSTOMER_ONBOARDING;

    if (user.role === "provider" && isCustomerRoute && pathname !== "/profile") {
      void navigate({ to: "/provider" });
      return;
    }

    if (user.role === "customer" && isProviderRoute) {
      void navigate({ to: "/" });
    }
  }, [isAuthenticated, isLoading, pathname, navigate, user]);

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
