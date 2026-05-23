import { createFileRoute } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";

export const Route = createFileRoute("/caregiver")({
  component: CaregiverPage,
});

function CaregiverPage() {
  const { t } = useTranslation();
  return (
    <div className="space-y-4">
      <h1 className="font-display text-4xl">{t("caregiver.title")}</h1>
      <p className="text-lg text-muted-foreground">{t("caregiver.subtitle")}</p>
    </div>
  );
}
