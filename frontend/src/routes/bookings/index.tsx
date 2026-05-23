import { createFileRoute, Link } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ApiError } from "@/lib/api";
import {
  cancelBooking,
  customerReviewBooking,
  fetchCustomerBookings,
} from "@/lib/marketplace-api";

export const Route = createFileRoute("/bookings/")({
  component: BookingsPage,
});

function BookingsPage() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [reviewBookingId, setReviewBookingId] = useState<number | null>(null);
  const [rating, setRating] = useState(8);
  const [comment, setComment] = useState("");

  const bookingsQuery = useQuery({
    queryKey: ["customer-bookings"],
    queryFn: fetchCustomerBookings,
  });

  const cancelMutation = useMutation({
    mutationFn: cancelBooking,
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["customer-bookings"] }),
  });

  const reviewMutation = useMutation({
    mutationFn: ({ id, rating, comment }: { id: number; rating: number; comment: string }) =>
      customerReviewBooking(id, rating, comment),
    onSuccess: () => {
      setReviewBookingId(null);
      void queryClient.invalidateQueries({ queryKey: ["customer-bookings"] });
    },
  });

  return (
    <div className="space-y-8">
      <header className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h1 className="font-display text-4xl">{t("bookings.title")}</h1>
          <p className="text-muted-foreground mt-2">{t("bookings.subtitle")}</p>
        </div>
        <Button asChild className="min-h-14 rounded-full">
          <Link to="/">{t("bookings.findProvider")}</Link>
        </Button>
      </header>

      {bookingsQuery.isLoading ? <p>{t("common.loading")}</p> : null}

      {(bookingsQuery.data ?? []).map((booking) => (
        <article key={booking.id} className="rounded-3xl border-2 border-border p-6 space-y-3">
          <div className="flex justify-between gap-2 flex-wrap">
            <h2 className="font-display text-xl">{booking.provider_name}</h2>
            <span className="rounded-full bg-secondary px-3 py-1 text-sm font-semibold capitalize">
              {booking.status}
            </span>
          </div>
          <p>{booking.service.name}</p>
          <p>{new Date(booking.starts_at).toLocaleString()}</p>
          <p className="font-semibold">{booking.price} RON</p>
          {booking.status === "pending" || booking.status === "confirmed" ? (
            <Button
              type="button"
              variant="outline"
              disabled={cancelMutation.isPending}
              onClick={() => cancelMutation.mutate(booking.id)}
              className="min-h-12 rounded-full border-2"
            >
              {t("bookings.cancel")}
            </Button>
          ) : null}
          {booking.status === "completed" && reviewBookingId !== booking.id ? (
            <Button
              type="button"
              onClick={() => setReviewBookingId(booking.id)}
              className="min-h-12 rounded-full"
            >
              {t("bookings.leaveReview")}
            </Button>
          ) : null}
          {reviewBookingId === booking.id ? (
            <div className="space-y-3 border-t pt-4">
              <div className="space-y-2">
                <Label htmlFor={`rating-${booking.id}`}>{t("bookings.rating")}</Label>
                <Input
                  id={`rating-${booking.id}`}
                  type="number"
                  min={1}
                  max={10}
                  value={rating}
                  onChange={(e) => setRating(Number(e.target.value))}
                  className="min-h-14 rounded-2xl"
                />
              </div>
              <Textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder={t("bookings.commentPlaceholder")}
                className="min-h-24 rounded-2xl"
              />
              <Button
                type="button"
                disabled={reviewMutation.isPending}
                onClick={() =>
                  reviewMutation.mutate({ id: booking.id, rating, comment })
                }
                className="min-h-12 rounded-full"
              >
                {t("bookings.submitReview")}
              </Button>
            </div>
          ) : null}
        </article>
      ))}

      {(bookingsQuery.data ?? []).length === 0 && !bookingsQuery.isLoading ? (
        <p className="text-muted-foreground">{t("bookings.empty")}</p>
      ) : null}
    </div>
  );
}
