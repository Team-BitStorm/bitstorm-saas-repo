import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { GeoLocationForm } from "@/components/marketplace/GeoLocationForm";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ApiError } from "@/lib/api";
import {
  fetchProviderProfile,
  fetchServiceArea,
  saveServiceArea,
  updateProviderProfile,
  type GeoLocationWrite,
} from "@/lib/marketplace-api";

export const Route = createFileRoute("/provider/onboarding")({
  component: ProviderOnboardingPage,
});

function ProviderOnboardingPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [displayName, setDisplayName] = useState("");
  const [bio, setBio] = useState("");
  const [travelRadius, setTravelRadius] = useState("25");
  const [location, setLocation] = useState<GeoLocationWrite>({
    address_line1: "",
    city: "",
    country: "RO",
  });
  const [error, setError] = useState<string | null>(null);

  useQuery({
    queryKey: ["provider-profile-onboard"],
    queryFn: async () => {
      const profile = await fetchProviderProfile();
      setDisplayName(profile.display_name ?? "");
      setBio(profile.bio ?? "");
      if (profile.travel_radius_km != null) setTravelRadius(String(profile.travel_radius_km));
      return profile;
    },
  });

  useQuery({
    queryKey: ["service-area-init"],
    queryFn: async () => {
      const area = await fetchServiceArea();
      if (area) {
        setLocation({
          label: area.label,
          address_line1: area.address_line1,
          address_line2: area.address_line2,
          city: area.city,
          region: area.region,
          postal_code: area.postal_code,
          country: area.country,
          latitude: area.latitude ?? undefined,
          longitude: area.longitude ?? undefined,
        });
      }
      return area;
    },
  });

  const saveMutation = useMutation({
    mutationFn: async () => {
      await updateProviderProfile({
        display_name: displayName,
        bio,
        travel_radius_km: Number(travelRadius),
      });
      await saveServiceArea(location);
    },
    onSuccess: () => void navigate({ to: "/provider" }),
    onError: (err) => setError(err instanceof ApiError ? err.message : t("errors.generic")),
  });

  return (
    <div className="space-y-8">
      <header>
        <h1 className="font-display text-4xl">{t("provider.onboardingTitle")}</h1>
        <p className="text-muted-foreground mt-2">{t("provider.onboardingSubtitle")}</p>
      </header>

      {error ? (
        <p role="alert" className="rounded-2xl border-2 border-destructive/40 bg-destructive/10 px-4 py-3 text-destructive">
          {error}
        </p>
      ) : null}

      <div className="space-y-2">
        <Label htmlFor="display-name">{t("provider.displayName")}</Label>
        <Input
          id="display-name"
          required
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
          className="min-h-14 text-lg rounded-2xl"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="bio">{t("provider.bio")}</Label>
        <Textarea
          id="bio"
          value={bio}
          onChange={(e) => setBio(e.target.value)}
          className="min-h-24 text-lg rounded-2xl"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="radius">{t("provider.travelRadius")}</Label>
        <Input
          id="radius"
          type="number"
          min={1}
          required
          value={travelRadius}
          onChange={(e) => setTravelRadius(e.target.value)}
          className="min-h-14 text-lg rounded-2xl"
        />
      </div>

      <section className="space-y-4">
        <h2 className="font-display text-2xl">{t("provider.serviceArea")}</h2>
        <GeoLocationForm value={location} onChange={setLocation} idPrefix="service" />
      </section>

      <Button
        type="button"
        disabled={saveMutation.isPending}
        onClick={() => saveMutation.mutate()}
        className="w-full min-h-14 rounded-full text-lg font-semibold"
      >
        {saveMutation.isPending ? t("common.saving") : t("provider.saveAndContinue")}
      </Button>
    </div>
  );
}
