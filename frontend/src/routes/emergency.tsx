import * as React from "react";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { PhoneCall, ArrowLeft, Check } from "lucide-react";
import { useTranslation } from "react-i18next";
import { usePatient } from "@/lib/patient-context";

export const Route = createFileRoute("/emergency")({
  component: EmergencyPage,
});

function EmergencyPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { caregivers } = usePatient();
  const [confirmed, setConfirmed] = React.useState(false);
  const primary = caregivers[0];

  React.useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: "instant" });
  }, []);

  if (confirmed) {
    return (
      <div className="space-y-6 text-center py-10">
        <div className="mx-auto flex size-28 items-center justify-center rounded-full bg-success text-success-foreground animate-pulse motion-reduce:animate-none">
          <PhoneCall aria-hidden="true" className="size-14" />
        </div>
        <h1 className="font-display text-4xl">{t("emergency.calling", { name: primary.name })}</h1>
        <p className="text-lg text-muted-foreground">{t("emergency.stayCalm")}</p>
        <a
          href={`tel:${primary.phone.replace(/\s/g, "")}`}
          className="inline-flex items-center justify-center gap-3 rounded-full bg-primary px-8 min-h-16 text-xl font-bold text-primary-foreground"
        >
          <PhoneCall aria-hidden="true" className="size-6" />
          {t("emergency.openDialer")}
        </a>
        <div>
          <button
            onClick={() => navigate({ to: "/" })}
            className="mt-4 inline-flex items-center gap-2 rounded-full border-2 border-input bg-background px-6 min-h-12 text-base font-semibold"
          >
            <ArrowLeft aria-hidden="true" className="size-5" />
            {t("common.backHome")}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <button
        onClick={() => navigate({ to: "/" })}
        aria-label={t("common.back")}
        className="inline-flex items-center gap-2 rounded-full border-2 border-input bg-background px-5 min-h-12 text-base font-semibold"
      >
        <ArrowLeft aria-hidden="true" className="size-5" />
        {t("common.back")}
      </button>

      <div className="rounded-3xl border-4 border-destructive/40 bg-destructive/5 p-6 text-center space-y-4">
        <div className="mx-auto flex size-24 items-center justify-center rounded-full bg-destructive text-destructive-foreground">
          <PhoneCall aria-hidden="true" className="size-12" />
        </div>
        <h1 className="font-display text-4xl">{t("emergency.title")}</h1>
        <p className="text-lg">{t("emergency.subtitle", { name: primary.name })}</p>
        <p className="text-base text-muted-foreground">
          {t("emergency.callerInfo", { relation: primary.relation, phone: primary.phone })}
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <button
          type="button"
          onClick={() => setConfirmed(true)}
          className="inline-flex items-center justify-center gap-3 rounded-full bg-destructive px-8 min-h-16 text-xl font-bold text-destructive-foreground hover:brightness-110"
        >
          <Check aria-hidden="true" className="size-6" />
          {t("emergency.yesCall")}
        </button>
        <button
          type="button"
          onClick={() => navigate({ to: "/" })}
          className="inline-flex items-center justify-center rounded-full border-2 border-input bg-background px-8 min-h-16 text-xl font-bold"
        >
          {t("emergency.no")}
        </button>
      </div>
    </div>
  );
}
