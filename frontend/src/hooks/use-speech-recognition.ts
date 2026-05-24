import * as React from "react";
import { useTranslation } from "react-i18next";

const LANG_MAP: Record<string, string> = {
  ro: "ro-RO",
  en: "en-US",
  hu: "hu-HU",
  de: "de-DE",
};

type SpeechRecognitionCtor = new () => SpeechRecognition;

function getSpeechRecognition(): SpeechRecognitionCtor | null {
  if (typeof window === "undefined") return null;
  const w = window as Window & {
    SpeechRecognition?: SpeechRecognitionCtor;
    webkitSpeechRecognition?: SpeechRecognitionCtor;
  };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
}

export function useSpeechRecognition(onResult: (text: string) => void) {
  const { i18n } = useTranslation();
  const [isListening, setIsListening] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const recognitionRef = React.useRef<SpeechRecognition | null>(null);

  const supported = getSpeechRecognition() != null;

  const stop = React.useCallback(() => {
    recognitionRef.current?.stop();
    setIsListening(false);
  }, []);

  const start = React.useCallback(() => {
    const Ctor = getSpeechRecognition();
    if (!Ctor) return;
    setError(null);
    stop();

    const recognition = new Ctor();
    recognition.lang = LANG_MAP[i18n.resolvedLanguage ?? "en"] ?? "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.onresult = (event) => {
      const transcript = event.results[0]?.[0]?.transcript;
      if (transcript) onResult(transcript.trim());
    };
    recognition.onerror = () => {
      setError("recognition_failed");
      setIsListening(false);
    };
    recognition.onend = () => setIsListening(false);
    recognitionRef.current = recognition;
    setIsListening(true);
    recognition.start();
  }, [i18n.resolvedLanguage, onResult, stop]);

  React.useEffect(() => () => stop(), [stop]);

  return { supported, isListening, error, start, stop };
}
