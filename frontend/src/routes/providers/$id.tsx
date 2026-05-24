import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  fetchHomeLocation,
  fetchMarketplaceProviderSlots,
  fetchProviderDetail,
  type ServiceOffering,
} from "@/lib/marketplace-api";

export const Route = createFileRoute("/providers/$id")({
  component: ProviderDetailPage,
});

function ProviderDetailPage() {
  const { t } = useTranslation();
  const { id } = Route.useParams();
  const [selectedSlotId, setSelectedSlotId] = useState<number | null>(null);
  // Used when the selected slot has no linked service — customer picks one
  const [selectedOfferingId, setSelectedOfferingId] = useState<string>("");

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

  const selectedSlot = slotsQuery.data?.find((s) => s.id === selectedSlotId) ?? null;
  // Resolved service ID: prefer the one embedded in the slot; fall back to user selection
  const resolvedServiceId: string = selectedSlot?.service?.id
    ? String(selectedSlot.service.id)
    : selectedOfferingId;

  const selectedOffering: ServiceOffering | undefined = provider?.offerings.find(
    (o) => String(o.service.id) === resolvedServiceId,
  );

  const canBook = selectedSlotId !== null && resolvedServiceId !== "";

  return (
    <div className="space-y-8">
      {providerQuery.isLoading ? <p>{t("common.loading")}</p> : null}
      {providerQuery.error ? (
        <p role="alert" className="text-destructive">
          {String(providerQuery.error)}
        </p>
      ) : null}
      {provider ? (
        <>
          <header>
            <h1 className="font-display text-4xl">{provider.display_name}</h1>
            <p className="text-muted-foreground mt-2">{provider.bio}</p>
            {provider.service_area?.city ? (
              <p className="text-sm text-muted-foreground mt-1">
                {provider.service_area.city}
                {provider.service_area.region ? `, ${provider.service_area.region}` : ""}
              </p>
            ) : null}
            {provider.distance_km ? (
              <p className="mt-2 font-semibold">
                {t("marketplace.distanceKm", { km: provider.distance_km })}
              </p>
            ) : null}
          </header>

          <section className="space-y-3">
            <h2 className="font-display text-2xl">{t("marketplace.servicesOffered")}</h2>
            {provider.offerings.map((o) => (
              <div key={o.id} className="rounded-2xl border-2 border-border p-4">
                <p className="font-semibold">{o.service.name}</p>
                <p className="text-muted-foreground">{o.provider_price} RON</p>
                {o.duration_minutes ? (
                  <p className="text-sm text-muted-foreground">{o.duration_minutes} min</p>
                ) : null}
              </div>
            ))}
          </section>

          <section className="space-y-3">
            <h2 className="font-display text-2xl">{t("marketplace.openSlots")}</h2>
            {slotsQuery.isLoading ? <p>{t("common.loading")}</p> : null}
            {(slotsQuery.data ?? []).length === 0 && !slotsQuery.isLoading ? (
              <p className="text-muted-foreground">{t("marketplace.noSlots")}</p>
            ) : null}
            {(slotsQuery.data ?? []).map((slot) => (
              <button
                key={slot.id}
                type="button"
                onClick={() => {
                  setSelectedSlotId(slot.id);
                  // If slot has a service, clear any manual offering selection
                  if (slot.service?.id) setSelectedOfferingId("");
                }}
                className={`w-full text-left rounded-2xl border-2 p-4 min-h-14 transition-colors ${
                  selectedSlotId === slot.id
                    ? "border-primary bg-primary/10"
                    : "border-border hover:border-primary/50"
                }`}
              >
                <p className="font-semibold">
                  {new Date(slot.starts_at).toLocaleString()}
                </p>
                <p className="text-sm text-muted-foreground">
                  {slot.service?.name ?? t("marketplace.anyService")}
                </p>
              </button>
            ))}
          </section>

          {/* Service selector — only shown when slot has no linked service */}
          {selectedSlotId !== null && !selectedSlot?.service?.id ? (
            <div className="space-y-2">
              <p className="font-semibold">{t("marketplace.selectService")}</p>
              <Select value={selectedOfferingId} onValueChange={setSelectedOfferingId}>
                <SelectTrigger className="min-h-14 rounded-2xl">
                  <SelectValue placeholder={t("marketplace.chooseService")} />
                </SelectTrigger>
                <SelectContent>
                  {provider.offerings.map((o) => (
                    <SelectItem key={o.id} value={String(o.service.id)}>
                      {o.service.name} — {o.provider_price} RON
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          ) : null}

          {/* Booking summary */}
          {canBook && selectedOffering ? (
            <div className="rounded-2xl border-2 border-accent/40 bg-accent/10 p-4 space-y-1">
              <p className="font-semibold">{selectedOffering.service.name}</p>
              <p>{selectedOffering.provider_price} RON</p>
              {selectedSlot ? (
                <p className="text-sm text-muted-foreground">
                  {new Date(selectedSlot.starts_at).toLocaleString()}
                </p>
              ) : null}
            </div>
          ) : null}

          {canBook ? (
            <Button asChild className="w-full min-h-14 rounded-full" disabled={!resolvedServiceId}>
              <Link
                to="/bookings/new"
                search={{
                  providerId: id,
                  slotId: String(selectedSlotId),
                  serviceId: resolvedServiceId,
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
