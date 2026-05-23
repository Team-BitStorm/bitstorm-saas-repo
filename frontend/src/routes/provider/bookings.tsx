import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { Button } from "@/components/ui/button";
import { providerBookingAction, fetchProviderBookings } from "@/lib/marketplace-api";

export const Route = createFileRoute("/provider/bookings")({
  component: ProviderBookingsPage,
});

function ProviderBookingsPage() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();

  const bookingsQuery = useQuery({
    queryKey: ["provider-bookings"],
    queryFn: fetchProviderBookings,
  });

  const actionMutation = useMutation({
    mutationFn: ({ id, action }: { id: number; action: "confirm" | "decline" | "complete" }) =>
      providerBookingAction(id, action),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["provider-bookings"] }),
  });

  return (
    <div className="space-y-8">
      <header>
        <h1 className="font-display text-4xl">{t("provider.bookingsTitle")}</h1>
        <p className="text-muted-foreground mt-2">{t("provider.bookingsSubtitle")}</p>
      </header>

      {bookingsQuery.isLoading ? <p>{t("common.loading")}</p> : null}

      {(bookingsQuery.data ?? []).map((booking) => (
        <article key={booking.id} className="rounded-3xl border-2 border-border p-6 space-y-3">
          <div className="flex justify-between gap-2 flex-wrap">
            <h2 className="font-display text-xl">{booking.customer_name ?? booking.customer_email}</h2>
            <span className="rounded-full bg-secondary px-3 py-1 text-sm font-semibold capitalize">
              {booking.status}
            </span>
          </div>
          <p>{booking.service.name}</p>
          <p>{new Date(booking.starts_at).toLocaleString()}</p>
          {booking.visit_location?.address_line1 ? (
            <p className="text-sm">
              {booking.visit_location.address_line1}, {booking.visit_location.city}
            </p>
          ) : null}
          <div className="flex flex-wrap gap-2">
            {booking.status === "pending" ? (
              <>
                <Button
                  type="button"
                  disabled={actionMutation.isPending}
                  onClick={() => actionMutation.mutate({ id: booking.id, action: "confirm" })}
                  className="min-h-12 rounded-full"
                >
                  {t("provider.confirm")}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  disabled={actionMutation.isPending}
                  onClick={() => actionMutation.mutate({ id: booking.id, action: "decline" })}
                  className="min-h-12 rounded-full border-2"
                >
                  {t("provider.decline")}
                </Button>
              </>
            ) : null}
            {booking.status === "confirmed" ? (
              <Button
                type="button"
                disabled={actionMutation.isPending}
                onClick={() => actionMutation.mutate({ id: booking.id, action: "complete" })}
                className="min-h-12 rounded-full"
              >
                {t("provider.complete")}
              </Button>
            ) : null}
          </div>
        </article>
      ))}

      {(bookingsQuery.data ?? []).length === 0 && !bookingsQuery.isLoading ? (
        <p className="text-muted-foreground">{t("provider.noBookings")}</p>
      ) : null}
    </div>
  );
}
