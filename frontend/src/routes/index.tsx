import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
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
import { discoverProviders, fetchHomeLocation, fetchLanguages, fetchServices } from "@/lib/marketplace-api";

export const Route = createFileRoute("/")({
  component: DiscoverPage,
});

const ALL_FILTER = "all";

function DiscoverPage() {
  const { t } = useTranslation();
  const [service, setService] = useState<string>(ALL_FILTER);
  const [language, setLanguage] = useState<string>(ALL_FILTER);
  const [lat, setLat] = useState("");
  const [lng, setLng] = useState("");

  const servicesQuery = useQuery({ queryKey: ["services"], queryFn: fetchServices });
  const languagesQuery = useQuery({ queryKey: ["languages"], queryFn: fetchLanguages });
  const homeQuery = useQuery({ queryKey: ["home-location"], queryFn: fetchHomeLocation });

  const providersQuery = useQuery({
    queryKey: ["providers", service, language, lat, lng],
    queryFn: () =>
      discoverProviders({
        service: service === ALL_FILTER ? undefined : service,
        language: language === ALL_FILTER ? undefined : language,
        lat: lat || undefined,
        lng: lng || undefined,
      }),
  });

  function useHomeCoords() {
    const home = homeQuery.data;
    if (home?.latitude && home?.longitude) {
      setLat(String(home.latitude));
      setLng(String(home.longitude));
    }
  }

  return (
    <div className="space-y-8">
      <header>
        <h1 className="font-display text-4xl">{t("marketplace.discoverTitle")}</h1>
        <p className="text-muted-foreground mt-2">{t("marketplace.discoverSubtitle")}</p>
      </header>

      {!homeQuery.data ? (
        <div className="rounded-3xl border-2 border-accent/40 bg-accent/10 p-6">
          <p className="mb-4">{t("marketplace.setHomeFirst")}</p>
          <Button asChild className="min-h-14 rounded-full">
            <Link to="/onboarding">{t("customer.startOnboarding")}</Link>
          </Button>
        </div>
      ) : null}

      <section className="rounded-3xl border-2 border-border p-6 space-y-4">
        <h2 className="font-display text-xl">{t("marketplace.filters")}</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label>{t("marketplace.service")}</Label>
            <Select value={service} onValueChange={setService}>
              <SelectTrigger className="min-h-14 rounded-2xl">
                <SelectValue placeholder={t("marketplace.allServices")} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL_FILTER}>{t("marketplace.allServices")}</SelectItem>
                {(servicesQuery.data ?? []).map((s) => (
                  <SelectItem key={s.id} value={s.slug}>
                    {s.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>{t("marketplace.language")}</Label>
            <Select value={language} onValueChange={setLanguage}>
              <SelectTrigger className="min-h-14 rounded-2xl">
                <SelectValue placeholder={t("marketplace.allLanguages")} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL_FILTER}>{t("marketplace.allLanguages")}</SelectItem>
                {(languagesQuery.data ?? []).map((l) => (
                  <SelectItem key={l.id} value={l.code}>
                    {l.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="lat">{t("marketplace.latitude")}</Label>
            <Input id="lat" value={lat} onChange={(e) => setLat(e.target.value)} className="min-h-14 rounded-2xl" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="lng">{t("marketplace.longitude")}</Label>
            <Input id="lng" value={lng} onChange={(e) => setLng(e.target.value)} className="min-h-14 rounded-2xl" />
          </div>
        </div>
        <Button type="button" variant="outline" onClick={useHomeCoords} className="min-h-12 rounded-full border-2">
          {t("marketplace.useHomeLocation")}
        </Button>
      </section>

      <section aria-live="polite" className="space-y-4">
        {providersQuery.isLoading ? <p>{t("common.loading")}</p> : null}
        {providersQuery.error ? (
          <p role="alert" className="text-destructive">{String(providersQuery.error)}</p>
        ) : null}
        {(providersQuery.data ?? []).length === 0 && !providersQuery.isLoading ? (
          <p className="text-muted-foreground">{t("marketplace.noProviders")}</p>
        ) : null}
        {(providersQuery.data ?? []).map((provider) => (
          <article
            key={provider.id}
            className="rounded-3xl border-2 border-border p-6 space-y-3"
          >
            <h3 className="font-display text-2xl">{provider.display_name}</h3>
            <p className="text-muted-foreground">{provider.bio}</p>
            {provider.service_area?.city ? (
              <p className="text-sm">
                {provider.service_area.city}
                {provider.service_area.region ? `, ${provider.service_area.region}` : ""}
              </p>
            ) : null}
            {provider.distance_km ? (
              <p className="text-sm font-semibold">{t("marketplace.distanceKm", { km: provider.distance_km })}</p>
            ) : null}
            <Button asChild className="min-h-14 rounded-full">
              <Link to="/providers/$id" params={{ id: String(provider.id) }}>
                {t("marketplace.viewProvider")}
              </Link>
            </Button>
          </article>
        ))}
      </section>
    </div>
  );
}
