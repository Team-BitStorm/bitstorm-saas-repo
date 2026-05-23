import { Moon, Sun } from "lucide-react";
import { useTranslation } from "react-i18next";

import { useTheme } from "@/lib/theme-context";
import { cn } from "@/lib/utils";

export function ThemeToggle({ compact = false }: { compact?: boolean }) {
  const { t } = useTranslation();
  const { resolvedTheme, toggleTheme } = useTheme();
  const isDark = resolvedTheme === "dark";

  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label={isDark ? t("accessibility.themeLight") : t("accessibility.themeDark")}
      className={cn(
        "inline-flex items-center justify-center rounded-full border-2 border-input bg-card font-semibold",
        compact ? "min-h-12 min-w-12" : "min-h-14 min-w-14",
      )}
    >
      {isDark ? (
        <Sun aria-hidden="true" className="size-5" />
      ) : (
        <Moon aria-hidden="true" className="size-5" />
      )}
    </button>
  );
}
