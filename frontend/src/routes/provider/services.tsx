import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ApiError } from "@/lib/api";
import {
  createOffering,
  deleteOffering,
  fetchOfferings,
  fetchServices,
} from "@/lib/marketplace-api";

export const Route = createFileRoute("/provider/services")({
  component: ProviderServicesPage,
});

function ProviderServicesPage() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [serviceId, setServiceId] = useState("");
  const [price, setPrice] = useState("");
  const [error, setError] = useState<string | null>(null);

  const servicesQuery = useQuery({ queryKey: ["services"], queryFn: fetchServices });
  const offeringsQuery = useQuery({ queryKey: ["offerings"], queryFn: fetchOfferings });

  const createMutation = useMutation({
    mutationFn: () =>
      createOffering({
        service_id: Number(serviceId),
        provider_price: price,
      }),
    onSuccess: () => {
      setServiceId("");
      setPrice("");
      void queryClient.invalidateQueries({ queryKey: ["offerings"] });
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : t("errors.generic")),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteOffering,
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["offerings"] }),
  });

  return (
    <div className="space-y-8">
      <header>
        <h1 className="font-display text-4xl">{t("provider.servicesTitle")}</h1>
        <p className="text-muted-foreground mt-2">{t("provider.servicesSubtitle")}</p>
      </header>

      {error ? (
        <p role="alert" className="rounded-2xl border-2 border-destructive/40 bg-destructive/10 px-4 py-3 text-destructive">
          {error}
        </p>
      ) : null}

      <section className="rounded-3xl border-2 border-border p-6 space-y-4">
        <h2 className="font-display text-xl">{t("provider.addOffering")}</h2>
        <div className="space-y-2">
          <Label>{t("marketplace.service")}</Label>
          <Select value={serviceId} onValueChange={setServiceId}>
            <SelectTrigger className="min-h-14 rounded-2xl">
              <SelectValue placeholder={t("provider.pickService")} />
            </SelectTrigger>
            <SelectContent>
              {(servicesQuery.data ?? []).map((s) => (
                <SelectItem key={s.id} value={String(s.id)}>
                  {s.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label htmlFor="price">{t("provider.yourPrice")}</Label>
          <Input
            id="price"
            type="number"
            step="0.01"
            value={price}
            onChange={(e) => setPrice(e.target.value)}
            className="min-h-14 rounded-2xl"
          />
        </div>
        <Button
          type="button"
          disabled={!serviceId || !price || createMutation.isPending}
          onClick={() => createMutation.mutate()}
          className="min-h-14 rounded-full"
        >
          {t("provider.addService")}
        </Button>
      </section>

      <section className="space-y-3">
        <h2 className="font-display text-xl">{t("provider.currentOfferings")}</h2>
        {(offeringsQuery.data ?? []).map((o) => (
          <div key={o.id} className="flex items-center justify-between gap-4 rounded-2xl border-2 border-border p-4">
            <div>
              <p className="font-semibold">{o.service.name}</p>
              <p className="text-muted-foreground">{o.provider_price} RON</p>
            </div>
            <Button
              type="button"
              variant="outline"
              disabled={deleteMutation.isPending}
              onClick={() => deleteMutation.mutate(o.id)}
              className="min-h-12 rounded-full border-2"
            >
              {t("common.remove")}
            </Button>
          </div>
        ))}
      </section>
    </div>
  );
}
