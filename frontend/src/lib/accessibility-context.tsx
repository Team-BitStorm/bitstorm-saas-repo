import * as React from "react";

const STORAGE_KEY = "bithealth_tts_enabled";

function isBrowser(): boolean {
  return typeof window !== "undefined";
}

type AccessibilityContextValue = {
  ttsEnabled: boolean;
  setTtsEnabled: (enabled: boolean) => void;
  toggleTts: () => void;
};

const AccessibilityContext = React.createContext<AccessibilityContextValue | null>(null);

export function AccessibilityProvider({ children }: { children: React.ReactNode }) {
  const [ttsEnabled, setTtsEnabledState] = React.useState(() => {
    if (!isBrowser()) return false;
    return localStorage.getItem(STORAGE_KEY) === "true";
  });

  const setTtsEnabled = React.useCallback((enabled: boolean) => {
    setTtsEnabledState(enabled);
    if (isBrowser()) localStorage.setItem(STORAGE_KEY, String(enabled));
  }, []);

  const toggleTts = React.useCallback(() => {
    setTtsEnabled(!ttsEnabled);
  }, [setTtsEnabled, ttsEnabled]);

  const value = React.useMemo(
    () => ({ ttsEnabled, setTtsEnabled, toggleTts }),
    [ttsEnabled, setTtsEnabled, toggleTts],
  );

  return (
    <AccessibilityContext.Provider value={value}>{children}</AccessibilityContext.Provider>
  );
}

export function useAccessibility() {
  const ctx = React.useContext(AccessibilityContext);
  if (!ctx) throw new Error("useAccessibility must be used within AccessibilityProvider");
  return ctx;
}
