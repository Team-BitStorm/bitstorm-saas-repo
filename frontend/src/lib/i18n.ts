import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import LanguageDetector from "i18next-browser-languagedetector";

import ro from "@/locales/ro.json";
import en from "@/locales/en.json";
import hu from "@/locales/hu.json";
import de from "@/locales/de.json";

export const SUPPORTED_LANGUAGES = [
  { code: "ro", label: "Română", flag: "🇷🇴" },
  { code: "en", label: "English", flag: "🇬🇧" },
  { code: "hu", label: "Magyar", flag: "🇭🇺" },
  { code: "de", label: "Deutsch", flag: "🇩🇪" },
] as const;

export type LanguageCode = (typeof SUPPORTED_LANGUAGES)[number]["code"];

if (!i18n.isInitialized) {
  i18n
    .use(LanguageDetector)
    .use(initReactI18next)
    .init({
      lng: "ro",
      resources: {
        ro: { translation: ro },
        en: { translation: en },
        hu: { translation: hu },
        de: { translation: de },
      },
      fallbackLng: "ro",
      supportedLngs: ["ro", "en", "hu", "de"],
      interpolation: { escapeValue: false },
      detection: {
        order: ["localStorage"],
        lookupLocalStorage: "bithealth-lang",
        caches: ["localStorage"],
      },
      react: { useSuspense: false },
    });
}

export default i18n;
