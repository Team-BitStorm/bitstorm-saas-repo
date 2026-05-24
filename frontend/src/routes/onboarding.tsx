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
  fetchCustomerProfile,
  fetchHomeLocation,
  saveHomeLocation,
  updateCustomerProfile,
  type GeoLocationWrite,
} from "@/lib/marketplace-api";

export const Route = createFileRoute("/onboarding")({
  component: CustomerOnboardingPage,
});

function CustomerOnboardingPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [bio, setBio] = useState("");
  const [location, setLocation] = useState<GeoLocationWrite>({
    address_line1: "",
    city: "",
    country: "RO",
  });
  const [error, setError] = useState<string | null>(null);

  useQuery({
    queryKey: ["customer-profile"],
    queryFn: async () => {
      const profile = await fetchCustomerProfile();
      setBio(profile.bio ?? "");
      return profile;
    },
  });

  useQuery({
    queryKey: ["home-location-init"],
    queryFn: async () => {
      const home = await fetchHomeLocation();
      if (home) {
        setLocation({
          label: home.label,
          address_line1: home.address_line1,
          address_line2: home.address_line2,
          city: home.city,
          region: home.region,
          postal_code: home.postal_code,
          country: home.country,
          latitude: home.latitude ?? undefined,
          longitude: home.longitude ?? undefined,
        });
      }
      return home;
    },
  });

  const saveMutation = useMutation({
    mutationFn: async () => {
      await updateCustomerProfile({ bio });
      await saveHomeLocation(location);
    },
    onSuccess: () => void navigate({ to: "/" }),
    onError: (err) => setError(err instanceof ApiError ? err.message : t("errors.generic")),
  });

  return (
    <div className="space-y-8">
      <header>
        <h1 className="font-display text-4xl">{t("customer.onboardingTitle")}</h1>
        <p className="text-muted-foreground mt-2">{t("customer.onboardingSubtitle")}</p>
      </header>

      {error ? (
        <p role="alert" className="rounded-2xl border-2 border-destructive/40 bg-destructive/10 px-4 py-3 text-destructive">
          {error}
        </p>
      ) : null}

      <div className="space-y-2">
        <Label htmlFor="bio">{t("customer.bio")}</Label>
        <Textarea
          id="bio"
          value={bio}
          onChange={(e) => setBio(e.target.value)}
          className="min-h-24 text-lg rounded-2xl"
        />
      </div>

      <section className="space-y-4">
        <h2 className="font-display text-2xl">{t("customer.homeLocation")}</h2>
        <p className="text-sm text-muted-foreground">{t("customer.homePrivacy")}</p>
        <GeoLocationForm value={location} onChange={setLocation} idPrefix="home" />
      </section>

      <Button
        type="button"
        disabled={saveMutation.isPending}
        onClick={() => saveMutation.mutate()}
        className="w-full min-h-14 rounded-full text-lg font-semibold"
      >
        {saveMutation.isPending ? t("common.saving") : t("customer.saveAndContinue")}
      </Button>
    </div>
  );
}
