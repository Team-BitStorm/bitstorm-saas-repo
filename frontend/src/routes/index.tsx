import { createFileRoute } from "@tanstack/react-router";
import { Pill, CalendarDays, HeartPulse, User, PhoneCall, BellRing } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Tile } from "@/components/ui/Tile";
import { AlertBanner } from "@/components/ui/AlertBanner";
import { usePatient } from "@/lib/patient-context";

export const Route = createFileRoute("/")({
  component: DashboardPage,
});

function DashboardPage() {
  const { t, i18n } = useTranslation();
  const { patient, medications, appointments } = usePatient();
  const now = new Date();
  const h = now.getHours();
  const greeting =
    h < 12 ? t("dashboard.greetingMorning") : h < 18 ? t("dashboard.greetingAfternoon") : t("dashboard.greetingEvening");
  const dateLabel = now.toLocaleDateString(i18n.resolvedLanguage, {
    weekday: "long",
    month: "long",
    day: "numeric",
  });

  const pendingMed = medications.find((m) => !m.taken);
  const nextAppt = appointments[0];

  return (
    <div className="space-y-8">
      <header>
        <p className="text-base text-muted-foreground font-semibold">{dateLabel}</p>
        <h1 className="font-display text-4xl md:text-5xl mt-1">
          {greeting}, {patient.firstName}.
        </h1>
      </header>

      {pendingMed ? (
        <AlertBanner
          icon={BellRing}
          title={t("dashboard.medDueTitle", { name: pendingMed.name, time: pendingMed.time })}
          detail={t("dashboard.medDueDetail")}
        />
      ) : null}

      <section aria-labelledby="quick-actions">
        <h2 id="quick-actions" className="font-display text-2xl mb-4">
          {t("dashboard.whatToDo")}
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Tile
            to="/medications"
            label={t("dashboard.medsTile")}
            icon={Pill}
            tone="primary"
            description={t("dashboard.medsToday", { count: medications.length })}
          />
          <Tile
            to="/calendar"
            label={t("dashboard.apptsTile")}
            icon={CalendarDays}
            tone="info"
            description={nextAppt ? t("dashboard.nextWith", { doctor: nextAppt.doctor }) : undefined}
          />
          <Tile to="/how-i-feel" label={t("dashboard.feelTile")} icon={HeartPulse} tone="accent" />
          <Tile
            to="/emergency"
            label={t("dashboard.emergencyTile")}
            icon={PhoneCall}
            tone="primary"
            description={t("dashboard.emergencyTileDesc")}
          />
          <Tile to="/profile" label={t("dashboard.profileTile")} icon={User} tone="success" />
        </div>
      </section>
    </div>
  );
}
