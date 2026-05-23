import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { Button } from "@/components/ui/button";
import {
  fetchHomeLocation,
  fetchMarketplaceProviderSlots,
  fetchProviderDetail,
} from "@/lib/marketplace-api";

export const Route = createFileRoute("/providers/$id")({
  component: ProviderDetailPage,
});

function ProviderDetailPage() {
  const { t } = useTranslation();
  const { id } = Route.useParams();
  const [selectedSlotId, setSelectedSlotId] = useState<number | null>(null);

  const homeQuery = useQuery({ queryKey: ["home-location"], queryFn: fetchHomeLocation });
  const providerQuery = useQuery({
    queryKey: ["provider", id],
    queryFn: () =>
      fetchProviderDetail(Number(id), {
        lat: homeQuery.data?.latitude ? String(homeQuery.data.latitude) : undefined,
        lng: homeQuery.data?.longitude ? String(homeQuery.data.longitude) : undefined,
      }),
    enabled: Boolean(id),
  });

  const slotsQuery = useQuery({
    queryKey: ["provider-slots", id],
    queryFn: () => fetchMarketplaceProviderSlots(Number(id)),
    enabled: Boolean(id),
  });

  const provider = providerQuery.data;

  return (
    <div className="space-y-8">
      {providerQuery.isLoading ? <p>{t("common.loading")}</p> : null}
      {provider ? (
        <>
          <header>
            <h1 className="font-display text-4xl">{provider.display_name}</h1>
            <p className="text-muted-foreground mt-2">{provider.bio}</p>
            {provider.distance_km ? (
              <p className="mt-2 font-semibold">{t("marketplace.distanceKm", { km: provider.distance_km })}</p>
            ) : null}
          </header>

          <section className="space-y-3">
            <h2 className="font-display text-2xl">{t("marketplace.servicesOffered")}</h2>
            {provider.offerings.map((o) => (
              <div key={o.id} className="rounded-2xl border-2 border-border p-4">
                <p className="font-semibold">{o.service.name}</p>
                <p className="text-muted-foreground">{o.provider_price} RON</p>
              </div>
            ))}
          </section>

          <section className="space-y-3">
            <h2 className="font-display text-2xl">{t("marketplace.openSlots")}</h2>
            {slotsQuery.isLoading ? <p>{t("common.loading")}</p> : null}
            {(slotsQuery.data ?? []).length === 0 ? (
              <p className="text-muted-foreground">{t("marketplace.noSlots")}</p>
            ) : null}
            {(slotsQuery.data ?? []).map((slot) => (
              <button
                key={slot.id}
                type="button"
                onClick={() => setSelectedSlotId(slot.id)}
                className={`w-full text-left rounded-2xl border-2 p-4 min-h-14 ${
                  selectedSlotId === slot.id ? "border-primary bg-primary/10" : "border-border"
                }`}
              >
                <p className="font-semibold">
                  {new Date(slot.starts_at).toLocaleString()} – {slot.service?.name ?? t("marketplace.anyService")}
                </p>
              </button>
            ))}
          </section>

          {selectedSlotId ? (
            <Button asChild className="w-full min-h-14 rounded-full">
              <Link
                to="/bookings/new"
                search={{
                  providerId: id,
                  slotId: String(selectedSlotId),
                  serviceId: String(
                    slotsQuery.data?.find((s) => s.id === selectedSlotId)?.service?.id ?? "",
                  ),
                }}
              >
                {t("marketplace.bookSlot")}
              </Link>
            </Button>
          ) : null}
        </>
      ) : null}
    </div>
  );
}
