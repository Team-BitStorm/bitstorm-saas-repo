import * as React from "react";
import { Link, useRouterState } from "@tanstack/react-router";
import { Home, Pill, HeartPulse, User, CalendarDays } from "lucide-react";
import { useTranslation } from "react-i18next";
import { cn } from "@/lib/utils";
import { EmergencyFab } from "./EmergencyFab";
import { LanguageSwitcher } from "./LanguageSwitcher";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const { t } = useTranslation();

  const tabs = [
    { to: "/", label: t("nav.home"), icon: Home },
    { to: "/medications", label: t("nav.meds"), icon: Pill },
    { to: "/how-i-feel", label: t("nav.feel"), icon: HeartPulse },
    { to: "/calendar", label: t("nav.calendar"), icon: CalendarDays },
    { to: "/profile", label: t("nav.profile"), icon: User },
  ] as const;

  return (
    <div className="min-h-dvh bg-background text-foreground">
      {/* Sidebar (tablet+) */}
      <aside
        aria-label="Primary navigation"
        className="hidden md:flex fixed inset-y-0 left-0 w-64 flex-col border-r bg-card px-4 py-6 gap-2"
      >
        <div className="px-2 pb-4">
          <p className="font-display text-2xl text-primary">{t("app.name")}</p>
          <p className="text-sm text-muted-foreground">{t("app.tagline")}</p>
        </div>
        <nav className="flex flex-col gap-2">
          {tabs.map((t) => {
            const active = isActive(pathname, t.to);
            const Icon = t.icon;
            return (
              <Link
                key={t.to}
                to={t.to}
                aria-label={t.label}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "flex items-center gap-4 rounded-2xl px-4 min-h-14 text-lg font-medium transition-colors",
                  active
                    ? "bg-primary text-primary-foreground"
                    : "text-foreground hover:bg-secondary",
                )}
              >
                <Icon aria-hidden="true" className="size-7 shrink-0" />
                <span>{t.label}</span>
              </Link>
            );
          })}
        </nav>
        <div className="mt-auto pt-4">
          <LanguageSwitcher menuPlacement="top" />
        </div>
      </aside>

      {/* Top bar (mobile) — holds language switcher */}
      <div className="md:hidden sticky top-0 z-30 flex items-center justify-between bg-background/90 backdrop-blur px-4 py-2 border-b">
        <p className="font-display text-xl text-primary">{t("app.name")}</p>
        <LanguageSwitcher compact />
      </div>

      {/* Main content */}
      <main
        id="main"
        className="md:pl-64 pb-28 md:pb-10 min-h-dvh"
      >
        <div className="mx-auto max-w-3xl px-4 pt-6 md:pt-10">{children}</div>
      </main>

      {/* Persistent emergency FAB */}
      <EmergencyFab />

      {/* Bottom nav (mobile) */}
      <nav
        aria-label="Primary navigation"
        className="md:hidden fixed bottom-0 inset-x-0 z-40 border-t bg-card"
        style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
      >
        <ul className="grid grid-cols-5">
          {tabs.map((t) => {
            const active = isActive(pathname, t.to);
            const Icon = t.icon;
            return (
              <li key={t.to}>
                <Link
                  to={t.to}
                  aria-label={t.label}
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    "flex flex-col items-center justify-center gap-1 min-h-16 px-2",
                    active ? "text-primary" : "text-muted-foreground",
                  )}
                >
                  <Icon aria-hidden="true" className="size-7" strokeWidth={active ? 2.5 : 2} />
                  <span className="text-xs font-semibold">{t.label}</span>
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
  if (to === "/") return pathname === "/";
  return pathname === to || pathname.startsWith(to + "/");
}
