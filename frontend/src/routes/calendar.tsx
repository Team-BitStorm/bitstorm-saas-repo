import { createFileRoute } from "@tanstack/react-router";
import { CalendarDays, MapPin, Video } from "lucide-react";
import { useTranslation } from "react-i18next";
import { usePatient } from "@/lib/patient-context";

export const Route = createFileRoute("/calendar")({
  component: CalendarPage,
});

function CalendarPage() {
  const { t, i18n } = useTranslation();
  const { appointments } = usePatient();
  return (
    <div className="space-y-8">
      <header>
        <h1 className="font-display text-4xl">{t("calendar.title")}</h1>
        <p className="text-base text-muted-foreground mt-1">{t("calendar.subtitle")}</p>
      </header>

      <ul className="space-y-3">
        {appointments.map((a) => {
          const d = new Date(a.date);
          return (
            <li key={a.id} className="rounded-3xl border-2 border-border bg-card p-5 flex items-start gap-4">
              <div className="flex size-16 shrink-0 flex-col items-center justify-center rounded-2xl bg-info/15 text-info">
                <CalendarDays aria-hidden="true" className="size-7" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-display text-2xl leading-tight">{a.doctor}</p>
                <p className="text-base text-muted-foreground">{a.type}</p>
                <p className="mt-1 text-base font-semibold">
                  {d.toLocaleDateString(i18n.resolvedLanguage, { weekday: "long", month: "short", day: "numeric" })} ·{" "}
                  {d.toLocaleTimeString(i18n.resolvedLanguage, { hour: "2-digit", minute: "2-digit" })}
                </p>
                <p className="mt-1 inline-flex items-center gap-1.5 text-base">
                  {a.isVideo ? <Video aria-hidden="true" className="size-5" /> : <MapPin aria-hidden="true" className="size-5" />}
                  <span>{a.location}</span>
                </p>
              </div>
            </li>
          );
        })}
      </ul>

      <div className="rounded-3xl border-2 border-dashed border-border p-6 text-center text-muted-foreground">
        {t("calendar.comingNext")}
      </div>
    </div>
  );
}
