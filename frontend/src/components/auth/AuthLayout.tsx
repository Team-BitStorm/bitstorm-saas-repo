import type { ReactNode } from "react";
import { Link } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";

import { LanguageSwitcher } from "@/components/layout/LanguageSwitcher";

export function AuthLayout({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
}) {
  const { t } = useTranslation();

  return (
    <div className="min-h-dvh bg-background text-foreground flex flex-col">
      <header className="flex items-center justify-between gap-3 px-4 py-4 md:px-8">
        <Link to="/login" className="font-display text-2xl text-primary truncate min-w-0">
          {t("app.name")}
        </Link>
        <LanguageSwitcher compact />
      </header>

      <main className="flex flex-1 items-center justify-center px-4 pb-10">
        <div className="w-full max-w-md space-y-8">
          <div className="text-center space-y-2">
            <h1 className="font-display text-4xl">{title}</h1>
            <p className="text-base text-muted-foreground">{subtitle}</p>
          </div>

          <div className="rounded-3xl border-2 border-border bg-card p-6 md:p-8 shadow-sm">
            {children}
          </div>
        </div>
      </main>
    </div>
  );
}
