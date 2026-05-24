import { Mic, MicOff } from "lucide-react";
import { useTranslation } from "react-i18next";

import { useSpeechRecognition } from "@/hooks/use-speech-recognition";
import { cn } from "@/lib/utils";

export function VoiceInputButton({
  onTranscript,
  className,
}: {
  onTranscript: (text: string) => void;
  className?: string;
}) {
  const { t } = useTranslation();
  const { supported, isListening, start, stop } = useSpeechRecognition(onTranscript);

  if (!supported) {
    return (
      <button
        type="button"
        disabled
        title={t("accessibility.voiceUnsupported")}
        aria-label={t("accessibility.voiceUnsupported")}
        className={cn(
          "inline-flex items-center justify-center rounded-full border-2 border-input opacity-40 cursor-not-allowed",
          className ?? "min-h-14 min-w-14",
        )}
      >
        <MicOff aria-hidden="true" className="size-5" />
      </button>
    );
  }

  return (
    <button
      type="button"
      onClick={() => (isListening ? stop() : start())}
      aria-label={
        isListening ? t("accessibility.stopVoice") : t("accessibility.startVoice")
      }
      aria-pressed={isListening}
      className={cn(
        "inline-flex items-center justify-center rounded-full border-2 border-input bg-card font-semibold",
        isListening && "border-primary bg-primary/10 text-primary",
        className ?? "min-h-14 min-w-14",
      )}
    >
      <Mic aria-hidden="true" className="size-5" />
    </button>
  );
}
