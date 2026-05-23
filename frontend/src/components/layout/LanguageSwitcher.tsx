import * as React from "react";
import { useRouterState } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { Languages, Check } from "lucide-react";
import { SUPPORTED_LANGUAGES, type LanguageCode } from "@/lib/i18n";
import { cn } from "@/lib/utils";

export function LanguageSwitcher({
  compact = false,
  menuPlacement = "bottom",
}: {
  compact?: boolean;
  /** Use "top" when the trigger sits at the bottom of the viewport (sidebar). */
  menuPlacement?: "top" | "bottom";
}) {
  const { t, i18n } = useTranslation();
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const [open, setOpen] = React.useState(false);

  React.useEffect(() => {
    setOpen(false);
  }, [pathname]);
  const current =
    SUPPORTED_LANGUAGES.find((l) => l.code === i18n.resolvedLanguage) ??
    SUPPORTED_LANGUAGES[0];

  const change = (code: LanguageCode) => {
    void i18n.changeLanguage(code);
    if (typeof document !== "undefined") document.documentElement.lang = code;
    setOpen(false);
  };

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-label={t("common.chooseLanguage")}
        aria-haspopup="listbox"
        aria-expanded={open}
        className={cn(
          "inline-flex items-center gap-2 rounded-full border-2 border-input bg-card font-semibold",
          compact ? "min-h-12 px-3 text-sm" : "min-h-14 px-4 text-base",
        )}
      >
        <Languages aria-hidden="true" className="size-5" />
        <span aria-hidden="true" className="text-xl leading-none">
          {current.flag}
        </span>
        <span>{current.label}</span>
      </button>

      {open ? (
        <>
          <button
            type="button"
            aria-hidden="true"
            tabIndex={-1}
            onClick={() => setOpen(false)}
            className="fixed inset-0 z-40 cursor-default"
          />
          <ul
            role="listbox"
            aria-label={t("common.language")}
            className={cn(
              "absolute left-0 z-50 min-w-56 rounded-2xl border-2 border-border bg-card p-2 shadow-xl",
              menuPlacement === "top" ? "bottom-full mb-2" : "top-full mt-2",
            )}
          >
            {SUPPORTED_LANGUAGES.map((l) => {
              const active = l.code === current.code;
              return (
                <li key={l.code}>
                  <button
                    type="button"
                    role="option"
                    aria-selected={active}
                    onClick={() => change(l.code)}
                    className={cn(
                      "w-full flex items-center gap-3 rounded-xl px-3 min-h-12 text-left text-base font-semibold",
                      active ? "bg-primary text-primary-foreground" : "hover:bg-secondary",
                    )}
                  >
                    <span aria-hidden="true" className="text-xl">
                      {l.flag}
                    </span>
                    <span className="flex-1">{l.label}</span>
                    {active ? <Check aria-hidden="true" className="size-5" /> : null}
                  </button>
                </li>
              );
            })}
          </ul>
        </>
      ) : null}
    </div>
  );
}
