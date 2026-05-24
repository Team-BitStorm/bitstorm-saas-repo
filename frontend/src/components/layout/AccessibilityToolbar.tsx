import { Volume2, VolumeX } from "lucide-react";
import { useTranslation } from "react-i18next";

import { ThemeToggle } from "@/components/layout/ThemeToggle";
import { useAccessibility } from "@/lib/accessibility-context";
import { cn } from "@/lib/utils";

export function AccessibilityToolbar({ compact = false }: { compact?: boolean }) {
  const { t } = useTranslation();
  const { ttsEnabled, toggleTts } = useAccessibility();

  return (
    <div className={cn("flex items-center gap-2", compact ? "gap-1" : "gap-2")}>
      <button
        type="button"
        onClick={toggleTts}
        aria-label={ttsEnabled ? t("accessibility.ttsOff") : t("accessibility.ttsOn")}
        aria-pressed={ttsEnabled}
        className={cn(
          "inline-flex items-center justify-center rounded-full border-2 border-input bg-card font-semibold",
          compact ? "min-h-12 min-w-12" : "min-h-14 min-w-14",
          ttsEnabled && "border-primary bg-primary/10 text-primary",
        )}
      >
        {ttsEnabled ? (
          <Volume2 aria-hidden="true" className="size-5" />
        ) : (
          <VolumeX aria-hidden="true" className="size-5" />
        )}
      </button>
      <ThemeToggle compact={compact} />
    </div>
  );
}
