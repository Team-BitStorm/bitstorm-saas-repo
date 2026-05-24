import { Volume2 } from "lucide-react";
import { useTranslation } from "react-i18next";

import { Button } from "@/components/ui/button";
import { extractMainContentText, useSpeechSynthesis } from "@/hooks/use-speech-synthesis";
import { useAccessibility } from "@/lib/accessibility-context";

export function ReadAloudButton({ className }: { className?: string }) {
  const { t } = useTranslation();
  const { ttsEnabled } = useAccessibility();
  const { supported, isSpeaking, speak, stop } = useSpeechSynthesis();

  if (!supported || !ttsEnabled) return null;

  return (
    <Button
      type="button"
      variant="outline"
      onClick={() => (isSpeaking ? stop() : speak(extractMainContentText()))}
      className={className ?? "min-h-14 rounded-full text-base font-semibold border-2"}
      aria-pressed={isSpeaking}
    >
      <Volume2 aria-hidden="true" className="size-5" />
      {isSpeaking ? t("accessibility.stopReading") : t("accessibility.readPage")}
    </Button>
  );
}
