import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { z } from "zod";

import { VoiceInputButton } from "@/components/accessibility/VoiceInputButton";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ApiError } from "@/lib/api";
import { createBooking } from "@/lib/marketplace-api";

const searchSchema = z.object({
  providerId: z.string().optional(),
  slotId: z.string().optional(),
  serviceId: z.string().optional(),
});

export const Route = createFileRoute("/bookings/new")({
  validateSearch: searchSchema,
  component: NewBookingPage,
});

function NewBookingPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { providerId, slotId, serviceId } = Route.useSearch();
  const [notes, setNotes] = useState("");
  const [error, setError] = useState<string | null>(null);

  const bookingMutation = useMutation({
    mutationFn: () =>
      createBooking({
        provider_id: Number(providerId),
        service_id: Number(serviceId),
        provider_availability_id: Number(slotId),
        notes,
      }),
    onSuccess: () => void navigate({ to: "/bookings" }),
    onError: (err) => setError(err instanceof ApiError ? err.message : t("errors.generic")),
  });

  if (!providerId || !slotId || !serviceId) {
    return (
      <div className="space-y-4">
        <p role="alert">{t("bookings.missingParams")}</p>
        <Button onClick={() => void navigate({ to: "/" })} className="min-h-14 rounded-full">
          {t("common.backHome")}
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <header>
        <h1 className="font-display text-4xl">{t("bookings.confirmTitle")}</h1>
        <p className="text-muted-foreground mt-2">{t("bookings.confirmSubtitle")}</p>
      </header>

      {error ? (
        <p role="alert" className="rounded-2xl border-2 border-destructive/40 bg-destructive/10 px-4 py-3 text-destructive">
          {error}
        </p>
      ) : null}

      <div className="space-y-2">
        <Label htmlFor="notes">{t("bookings.notes")}</Label>
        <div className="flex gap-2">
          <Textarea
            id="notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="min-h-24 text-lg rounded-2xl flex-1"
          />
          <VoiceInputButton onTranscript={(text) => setNotes((n) => (n ? `${n} ${text}` : text))} />
        </div>
      </div>

      <Button
        type="button"
        disabled={bookingMutation.isPending}
        onClick={() => bookingMutation.mutate()}
        className="w-full min-h-14 rounded-full text-lg font-semibold"
      >
        {bookingMutation.isPending ? t("bookings.booking") : t("bookings.confirmBooking")}
      </Button>
    </div>
  );
}
