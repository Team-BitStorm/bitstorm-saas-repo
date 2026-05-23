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
  createAvailabilityRule,
  createProviderSlot,
  deleteAvailabilityRule,
  fetchAvailabilityRules,
  fetchMyAvailabilitySlots,
  generateSlots,
  setSlotStatus,
} from "@/lib/marketplace-api";

const WEEKDAYS = [
  { value: 0, label: "Monday" },
  { value: 1, label: "Tuesday" },
  { value: 2, label: "Wednesday" },
  { value: 3, label: "Thursday" },
  { value: 4, label: "Friday" },
  { value: 5, label: "Saturday" },
  { value: 6, label: "Sunday" },
];

export const Route = createFileRoute("/provider/schedule")({
  component: ProviderSchedulePage,
});

function ProviderSchedulePage() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [weekday, setWeekday] = useState("0");
  const [startTime, setStartTime] = useState("09:00");
  const [endTime, setEndTime] = useState("17:00");
  const [slotStart, setSlotStart] = useState("");
  const [slotEnd, setSlotEnd] = useState("");
  const [error, setError] = useState<string | null>(null);

  const rulesQuery = useQuery({ queryKey: ["availability-rules"], queryFn: fetchAvailabilityRules });
  const slotsQuery = useQuery({
    queryKey: ["provider-slots-list"],
    queryFn: () => fetchMyAvailabilitySlots({ status: "open" }),
  });

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: ["availability-rules"] });
    void queryClient.invalidateQueries({ queryKey: ["provider-slots-list"] });
  };

  const ruleMutation = useMutation({
    mutationFn: () =>
      createAvailabilityRule({
        weekday: Number(weekday),
        start_time: startTime,
        end_time: endTime,
        timezone: "Europe/Bucharest",
        is_active: true,
        valid_from: null,
        valid_until: null,
      }),
    onSuccess: invalidate,
    onError: (err) => setError(err instanceof ApiError ? err.message : t("errors.generic")),
  });

  const generateMutation = useMutation({
    mutationFn: () => generateSlots(4),
    onSuccess: invalidate,
  });

  const slotMutation = useMutation({
    mutationFn: () =>
      createProviderSlot({
        starts_at: new Date(slotStart).toISOString(),
        ends_at: new Date(slotEnd).toISOString(),
      }),
    onSuccess: () => {
      setSlotStart("");
      setSlotEnd("");
      invalidate();
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : t("errors.generic")),
  });

  const blockMutation = useMutation({
    mutationFn: (id: number) => setSlotStatus(id, "blocked"),
    onSuccess: invalidate,
  });

  const deleteRuleMutation = useMutation({
    mutationFn: deleteAvailabilityRule,
    onSuccess: invalidate,
  });

  return (
    <div className="space-y-8">
      <header>
        <h1 className="font-display text-4xl">{t("provider.scheduleTitle")}</h1>
        <p className="text-muted-foreground mt-2">{t("provider.scheduleSubtitle")}</p>
      </header>

      {error ? (
        <p role="alert" className="rounded-2xl border-2 border-destructive/40 bg-destructive/10 px-4 py-3 text-destructive">
          {error}
        </p>
      ) : null}

      <section className="rounded-3xl border-2 border-border p-6 space-y-4">
        <h2 className="font-display text-xl">{t("provider.recurringRules")}</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="space-y-2">
            <Label>{t("provider.weekday")}</Label>
            <Select value={weekday} onValueChange={setWeekday}>
              <SelectTrigger className="min-h-14 rounded-2xl">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {WEEKDAYS.map((d) => (
                  <SelectItem key={d.value} value={String(d.value)}>
                    {d.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="start">{t("provider.startTime")}</Label>
            <Input id="start" type="time" value={startTime} onChange={(e) => setStartTime(e.target.value)} className="min-h-14 rounded-2xl" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="end">{t("provider.endTime")}</Label>
            <Input id="end" type="time" value={endTime} onChange={(e) => setEndTime(e.target.value)} className="min-h-14 rounded-2xl" />
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button type="button" onClick={() => ruleMutation.mutate()} className="min-h-12 rounded-full">
            {t("provider.addRule")}
          </Button>
          <Button
            type="button"
            variant="outline"
            disabled={generateMutation.isPending}
            onClick={() => generateMutation.mutate()}
            className="min-h-12 rounded-full border-2"
          >
            {t("provider.generateSlots")}
          </Button>
        </div>
        {(rulesQuery.data ?? []).map((rule) => (
          <div key={rule.id} className="flex justify-between items-center rounded-2xl border p-4">
            <span>
              {WEEKDAYS.find((d) => d.value === rule.weekday)?.label} {rule.start_time}–{rule.end_time}
            </span>
            <Button
              type="button"
              variant="outline"
              onClick={() => deleteRuleMutation.mutate(rule.id)}
              className="min-h-10 rounded-full border-2"
            >
              {t("common.remove")}
            </Button>
          </div>
        ))}
      </section>

      <section className="rounded-3xl border-2 border-border p-6 space-y-4">
        <h2 className="font-display text-xl">{t("provider.oneOffSlot")}</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="slot-start">{t("provider.slotStart")}</Label>
            <Input id="slot-start" type="datetime-local" value={slotStart} onChange={(e) => setSlotStart(e.target.value)} className="min-h-14 rounded-2xl" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="slot-end">{t("provider.slotEnd")}</Label>
            <Input id="slot-end" type="datetime-local" value={slotEnd} onChange={(e) => setSlotEnd(e.target.value)} className="min-h-14 rounded-2xl" />
          </div>
        </div>
        <Button type="button" disabled={!slotStart || !slotEnd} onClick={() => slotMutation.mutate()} className="min-h-12 rounded-full">
          {t("provider.addSlot")}
        </Button>
      </section>

      <section className="space-y-3">
        <h2 className="font-display text-xl">{t("provider.openSlots")}</h2>
        {(slotsQuery.data ?? []).map((slot) => (
          <div key={slot.id} className="flex justify-between items-center rounded-2xl border-2 border-border p-4 gap-2 flex-wrap">
            <span>{new Date(slot.starts_at).toLocaleString()} – {slot.status}</span>
            <Button
              type="button"
              variant="outline"
              onClick={() => blockMutation.mutate(slot.id)}
              className="min-h-10 rounded-full border-2"
            >
              {t("provider.blockSlot")}
            </Button>
          </div>
        ))}
      </section>
    </div>
  );
}
