import { createFileRoute } from "@tanstack/react-router";
import { Sun, CloudSun, Moon } from "lucide-react";
import { useTranslation } from "react-i18next";
import { MedicationCard } from "@/components/meds/MedicationCard";
import { usePatient } from "@/lib/patient-context";
import type { Medication } from "@/data/mock";

export const Route = createFileRoute("/medications")({
  component: MedicationsPage,
});

function MedicationsPage() {
  const { t } = useTranslation();
  const { medications, markMedicationTaken } = usePatient();

  const blocks = [
    { id: "morning" as const, label: t("meds.morning"), icon: Sun },
    { id: "afternoon" as const, label: t("meds.afternoon"), icon: CloudSun },
    { id: "night" as const, label: t("meds.night"), icon: Moon },
  ];

  return (
    <div className="space-y-8">
      <header>
        <h1 className="font-display text-4xl">{t("meds.title")}</h1>
        <p className="text-base text-muted-foreground mt-1">{t("meds.subtitle")}</p>
      </header>

      {blocks.map((b) => {
        const items = medications.filter((m: Medication) => m.block === b.id);
        if (items.length === 0) return null;
        const Icon = b.icon;
        return (
          <section key={b.id} aria-labelledby={`block-${b.id}`} className="space-y-3">
            <h2 id={`block-${b.id}`} className="flex items-center gap-3 font-display text-2xl">
              <Icon aria-hidden="true" className="size-7 text-accent" />
              {b.label}
            </h2>
            <div className="space-y-3">
              {items.map((m) => (
                <MedicationCard
                  key={m.id}
                  med={m}
                  onToggle={(taken) => markMedicationTaken(m.id, taken)}
                />
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}
