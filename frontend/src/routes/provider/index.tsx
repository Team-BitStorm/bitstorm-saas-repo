import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { Tile } from "@/components/ui/Tile";
import { Briefcase, CalendarDays, Clock, Settings } from "lucide-react";
import { fetchProviderBookings, fetchProviderProfile } from "@/lib/marketplace-api";

export const Route = createFileRoute("/provider/")({
  component: ProviderHomePage,
});

function ProviderHomePage() {
  const { t } = useTranslation();

  const profileQuery = useQuery({
    queryKey: ["provider-profile"],
    queryFn: fetchProviderProfile,
  });

  const bookingsQuery = useQuery({
    queryKey: ["provider-bookings"],
    queryFn: fetchProviderBookings,
  });

  const pending = (bookingsQuery.data ?? []).filter((b) => b.status === "pending").length;

  return (
    <div className="space-y-8">
      <header>
        <h1 className="font-display text-4xl">
          {t("provider.welcome", { name: profileQuery.data?.display_name ?? "…" })}
        </h1>
        <p className="text-muted-foreground mt-2">{t("provider.homeSubtitle")}</p>
      </header>

      {pending > 0 ? (
        <div className="rounded-3xl border-2 border-accent/40 bg-accent/10 p-6">
          <p className="font-semibold">{t("provider.pendingBookings", { count: pending })}</p>
        </div>
      ) : null}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Tile to="/provider/onboarding" label={t("provider.editProfile")} icon={Settings} tone="primary" />
        <Tile to="/provider/services" label={t("nav.services")} icon={Briefcase} tone="info" />
        <Tile to="/provider/schedule" label={t("nav.schedule")} icon={CalendarDays} tone="accent" />
        <Tile
          to="/provider/bookings"
          label={t("nav.bookings")}
          icon={Clock}
          tone="success"
          description={pending ? t("provider.pendingBookings", { count: pending }) : undefined}
        />
      </div>

      {!profileQuery.data?.service_area ? (
        <div className="rounded-3xl border-2 border-dashed border-border p-6 text-center">
          <p className="mb-4">{t("provider.completeOnboarding")}</p>
          <Link to="/provider/onboarding" className="text-primary font-semibold underline">
            {t("provider.startOnboarding")}
          </Link>
        </div>
      ) : null}
    </div>
  );
}
