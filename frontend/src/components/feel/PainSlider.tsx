import { useTranslation } from "react-i18next";
import { cn } from "@/lib/utils";

const anchors = ["😀", "🙂", "😐", "😕", "😣", "😖", "😫", "😩", "😭", "🤯"];

export function PainSlider({
  value,
  onChange,
}: {
  value: number;
  onChange: (n: number) => void;
}) {
  const { t } = useTranslation();
  return (
    <div>
      <div className="flex justify-between text-sm font-semibold text-muted-foreground mb-2 px-1">
        <span>{t("feel.noPain")}</span>
        <span>{t("feel.worstPain")}</span>
      </div>

      <input
        type="range"
        min={1}
        max={10}
        step={1}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        aria-label={t("feel.painLevelAria")}
        aria-valuemin={1}
        aria-valuemax={10}
        aria-valuenow={value}
        className="w-full h-3 accent-primary cursor-pointer"
      />

      <div className="mt-4 grid grid-cols-10 gap-1">
        {anchors.map((emoji, i) => {
          const n = i + 1;
          const active = n === value;
          return (
            <button
              key={n}
              type="button"
              onClick={() => onChange(n)}
              aria-label={t("feel.painLevelN", { n })}
              aria-pressed={active}
              className={cn(
                "flex flex-col items-center justify-center rounded-xl min-h-14 border-2 text-sm font-bold transition",
                active
                  ? "border-primary bg-primary text-primary-foreground"
                  : "border-border bg-card",
              )}
            >
              <span aria-hidden="true" className="text-lg leading-none">{emoji}</span>
              <span>{n}</span>
            </button>
          );
        })}
      </div>

      <p className="mt-4 text-center text-2xl font-display">
        {t("feel.painLevel", { value })}
      </p>
    </div>
  );
}
