import { Link } from "@tanstack/react-router";
import { PhoneCall } from "lucide-react";
import { useTranslation } from "react-i18next";

export function EmergencyFab() {
  const { t } = useTranslation();
  return (
    <Link
      to="/emergency"
      aria-label={t("emergency.fabAria")}
      className="fixed z-50 bottom-24 right-4 md:bottom-8 md:right-8 inline-flex items-center gap-3 rounded-full bg-destructive text-destructive-foreground px-6 min-h-16 shadow-lg shadow-destructive/30 ring-4 ring-destructive/20 hover:brightness-110 active:scale-[0.98] transition"
    >
      <PhoneCall aria-hidden="true" className="size-7" />
      <span className="text-lg font-bold uppercase tracking-wide">{t("emergency.fab")}</span>
    </Link>
  );
}
