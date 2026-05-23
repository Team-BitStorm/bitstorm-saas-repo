import { useTranslation } from "react-i18next";
import { cn } from "@/lib/utils";

const symptoms = [
  { id: "okay", emoji: "🙂" },
  { id: "happy", emoji: "😊" },
  { id: "tired", emoji: "😴" },
  { id: "pain", emoji: "🤕" },
  { id: "dizzy", emoji: "😵‍💫" },
  { id: "nauseous", emoji: "🤢" },
  { id: "sad", emoji: "😢" },
  { id: "confused", emoji: "😕" },
] as const;

export type SymptomId = (typeof symptoms)[number]["id"];

export function SymptomPicker({
  selected,
  onChange,
}: {
  selected: SymptomId[];
  onChange: (next: SymptomId[]) => void;
}) {
  const { t } = useTranslation();
  const toggle = (id: SymptomId) => {
    onChange(selected.includes(id) ? selected.filter((s) => s !== id) : [...selected, id]);
  };

  return (
    <div role="group" aria-label={t("feel.groupAria")} className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      {symptoms.map((s) => {
        const active = selected.includes(s.id);
        const label = t(`feel.symptoms.${s.id}`);
        return (
          <button
            key={s.id}
            type="button"
            onClick={() => toggle(s.id)}
            aria-pressed={active}
            aria-label={label}
            className={cn(
              "flex flex-col items-center justify-center gap-2 rounded-3xl min-h-28 p-4 border-2 text-lg font-semibold transition",
              active
                ? "border-primary bg-primary text-primary-foreground"
                : "border-border bg-card hover:border-primary/50",
            )}
          >
            <span aria-hidden="true" className="text-4xl">{s.emoji}</span>
            <span>{label}</span>
          </button>
        );
      })}
    </div>
  );
}
