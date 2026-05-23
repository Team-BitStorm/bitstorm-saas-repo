import { Check, Clock, Pill } from "lucide-react";
import { useTranslation } from "react-i18next";
import type { Medication } from "@/data/mock";
import { cn } from "@/lib/utils";

export function MedicationCard({
  med,
  onToggle,
}: {
  med: Medication;
  onToggle: (taken: boolean) => void;
}) {
  const { t } = useTranslation();
  return (
    <div
      className={cn(
        "rounded-3xl bg-card border-2 p-5 flex items-center gap-4 transition",
        med.taken ? "border-success/60 bg-success/10" : "border-border",
      )}
    >
      <div
        aria-hidden="true"
        className="flex size-16 shrink-0 items-center justify-center rounded-2xl bg-primary/10 text-primary"
      >
        <Pill className="size-8" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-display text-2xl leading-tight">{med.name}</p>
        <p className="text-base text-muted-foreground">{med.dosage}</p>
        <p className="mt-1 inline-flex items-center gap-1.5 text-base font-semibold">
          <Clock aria-hidden="true" className="size-5" />
          <span>{med.time}</span>
        </p>
      </div>
      <button
        type="button"
        onClick={() => onToggle(!med.taken)}
        aria-pressed={med.taken}
        aria-label={med.taken ? t("meds.markNotTaken", { name: med.name }) : t("meds.markTaken", { name: med.name })}
        className={cn(
          "inline-flex items-center gap-2 rounded-full min-h-14 px-5 text-lg font-bold transition",
          med.taken
            ? "bg-success text-success-foreground"
            : "bg-primary text-primary-foreground hover:brightness-110",
        )}
      >
        <Check aria-hidden="true" className="size-6" />
        {med.taken ? t("meds.taken") : t("meds.iTookIt")}
      </button>
    </div>
  );
}
