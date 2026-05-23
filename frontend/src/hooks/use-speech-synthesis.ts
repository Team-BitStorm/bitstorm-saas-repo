import * as React from "react";
import { useTranslation } from "react-i18next";

const LANG_MAP: Record<string, string> = {
  ro: "ro-RO",
  en: "en-US",
  hu: "hu-HU",
  de: "de-DE",
};

export function useSpeechSynthesis() {
  const { i18n } = useTranslation();
  const [isSpeaking, setIsSpeaking] = React.useState(false);
  const utteranceRef = React.useRef<SpeechSynthesisUtterance | null>(null);

  const supported = typeof window !== "undefined" && "speechSynthesis" in window;

  const stop = React.useCallback(() => {
    if (!supported) return;
    window.speechSynthesis.cancel();
    setIsSpeaking(false);
  }, [supported]);

  const speak = React.useCallback(
    (text: string) => {
      if (!supported || !text.trim()) return;
      stop();
      const utterance = new SpeechSynthesisUtterance(text.trim());
      utterance.lang = LANG_MAP[i18n.resolvedLanguage ?? "en"] ?? "en-US";
      utterance.rate = 0.95;
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);
      utteranceRef.current = utterance;
      setIsSpeaking(true);
      window.speechSynthesis.speak(utterance);
    },
    [supported, stop, i18n.resolvedLanguage],
  );

  React.useEffect(() => () => stop(), [stop]);

  return { supported, isSpeaking, speak, stop };
}

export function extractMainContentText(): string {
  if (typeof document === "undefined") return "";
  const main = document.getElementById("main");
  if (!main) return "";
  const heading = main.querySelector("h1");
  const alerts = Array.from(main.querySelectorAll('[role="alert"]'))
    .map((el) => el.textContent?.trim())
    .filter(Boolean);
  const body = main.innerText.replace(/\s+/g, " ").trim();
  const parts = [heading?.textContent?.trim(), ...alerts, body].filter(Boolean);
  return [...new Set(parts)].join(". ");
}
