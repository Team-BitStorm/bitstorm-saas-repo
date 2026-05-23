import * as React from "react";
import { Link, useRouterState } from "@tanstack/react-router";
import {
  Home,
  User,
  CalendarDays,
  Briefcase,
  Clock,
  Search,
  BookOpen,
} from "lucide-react";
import { useTranslation } from "react-i18next";

import { ReadAloudButton } from "@/components/accessibility/ReadAloudButton";
import { AccessibilityToolbar } from "@/components/layout/AccessibilityToolbar";
import { LanguageSwitcher } from "@/components/layout/LanguageSwitcher";
import { useAuth } from "@/lib/auth-context";
import { cn } from "@/lib/utils";

type NavItem = {
  to: string;
  label: string;
  icon: React.ComponentType<{ className?: string; strokeWidth?: number }>;
};

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const { t } = useTranslation();
  const { user } = useAuth();

  const tabs: NavItem[] =
    user?.role === "provider"
      ? [
          { to: "/provider", label: t("nav.providerHome"), icon: Home },
          { to: "/provider/services", label: t("nav.services"), icon: Briefcase },
          { to: "/provider/schedule", label: t("nav.schedule"), icon: CalendarDays },
          { to: "/provider/bookings", label: t("nav.bookings"), icon: Clock },
          { to: "/profile", label: t("nav.profile"), icon: User },
        ]
      : [
          { to: "/", label: t("nav.discover"), icon: Search },
          { to: "/bookings", label: t("nav.myBookings"), icon: BookOpen },
          { to: "/profile", label: t("nav.profile"), icon: User },
        ];

  return (
    <div className="min-h-dvh bg-background text-foreground">
      <aside
        aria-label="Primary navigation"
        className="hidden md:flex fixed inset-y-0 left-0 w-64 flex-col border-r bg-card px-4 py-6 gap-2"
      >
        <div className="px-2 pb-4">
          <p className="font-display text-2xl text-primary">{t("app.name")}</p>
          <p className="text-sm text-muted-foreground">{t("app.tagline")}</p>
        </div>
        <nav className="flex flex-col gap-2">
          {tabs.map((tab) => {
            const active = isActive(pathname, tab.to);
            const Icon = tab.icon;
            return (
              <Link
                key={tab.to}
                to={tab.to}
                aria-label={tab.label}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "flex items-center gap-4 rounded-2xl px-4 min-h-14 text-lg font-medium transition-colors",
                  active
                    ? "bg-primary text-primary-foreground"
                    : "text-foreground hover:bg-secondary",
                )}
              >
                <Icon aria-hidden="true" className="size-7 shrink-0" />
                <span>{tab.label}</span>
              </Link>
            );
          })}
        </nav>
        <div className="mt-auto pt-4 space-y-3">
          <ReadAloudButton className="w-full min-h-12 rounded-full text-sm font-semibold border-2" />
          <div className="flex items-center gap-2">
            <AccessibilityToolbar />
            <LanguageSwitcher menuPlacement="top" compact />
          </div>
        </div>
      </aside>

      <div className="md:hidden sticky top-0 z-30 flex items-center justify-between bg-background/90 backdrop-blur px-4 py-2 border-b gap-2">
        <p className="font-display text-xl text-primary truncate">{t("app.name")}</p>
        <div className="flex items-center gap-2 shrink-0">
          <AccessibilityToolbar compact />
          <LanguageSwitcher compact />
        </div>
      </div>

      <main id="main" className="md:pl-64 pb-28 md:pb-10 min-h-dvh">
        <div className="mx-auto max-w-3xl px-4 pt-6 md:pt-10 space-y-4">
          <div className="md:hidden">
            <ReadAloudButton className="w-full min-h-12 rounded-full text-sm font-semibold border-2" />
          </div>
          {children}
        </div>
      </main>

      <nav
        aria-label="Primary navigation"
        className="md:hidden fixed bottom-0 inset-x-0 z-40 border-t bg-card"
        style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
      >
        <ul className={cn("grid", tabs.length === 3 ? "grid-cols-3" : "grid-cols-5")}>
          {tabs.map((tab) => {
            const active = isActive(pathname, tab.to);
            const Icon = tab.icon;
            return (
              <li key={tab.to}>
                <Link
                  to={tab.to}
                  aria-label={tab.label}
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    "flex flex-col items-center justify-center gap-1 min-h-16 px-1",
                    active ? "text-primary" : "text-muted-foreground",
                  )}
                >
                  <Icon aria-hidden="true" className="size-6" strokeWidth={active ? 2.5 : 2} />
                  <span className="text-[10px] font-semibold text-center leading-tight">
                    {tab.label}
                  </span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
    </div>
  );
}

function isActive(pathname: string, to: string) {
  if (to === "/" || to === "/provider") {
    return pathname === to;
  }
  return pathname === to || pathname.startsWith(to + "/");
}
