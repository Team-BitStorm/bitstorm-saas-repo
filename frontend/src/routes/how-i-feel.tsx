import * as React from "react";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { Check } from "lucide-react";
import { useTranslation } from "react-i18next";
import { SymptomPicker, type SymptomId } from "@/components/feel/SymptomPicker";
import { PainSlider } from "@/components/feel/PainSlider";

export const Route = createFileRoute("/how-i-feel")({
  component: HowIFeelPage,
});

function HowIFeelPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [symptoms, setSymptoms] = React.useState<SymptomId[]>([]);
  const [pain, setPain] = React.useState(3);
  const [submitted, setSubmitted] = React.useState(false);

  if (submitted) {
    return (
      <div className="space-y-6 text-center py-10">
        <div className="mx-auto flex size-24 items-center justify-center rounded-full bg-success text-success-foreground">
          <Check aria-hidden="true" className="size-12" />
        </div>
        <h1 className="font-display text-4xl">{t("feel.thanks")}</h1>
        <p className="text-lg text-muted-foreground">{t("feel.notified")}</p>
        <button
          onClick={() => navigate({ to: "/" })}
          className="inline-flex items-center justify-center rounded-full bg-primary px-8 min-h-14 text-lg font-bold text-primary-foreground"
        >
          {t("common.backHome")}
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-10">
      <header>
        <h1 className="font-display text-4xl">{t("feel.title")}</h1>
        <p className="text-base text-muted-foreground mt-1">{t("feel.subtitle")}</p>
      </header>

      <section aria-labelledby="symptoms-h">
        <h2 id="symptoms-h" className="font-display text-2xl mb-4">
          {t("feel.symptomsHeading")}
        </h2>
        <SymptomPicker selected={symptoms} onChange={setSymptoms} />
      </section>

      <section aria-labelledby="pain-h">
        <h2 id="pain-h" className="font-display text-2xl mb-4">
          {t("feel.painHeading")}
        </h2>
        <PainSlider value={pain} onChange={setPain} />
      </section>

      <button
        type="button"
        onClick={() => setSubmitted(true)}
        className="w-full inline-flex items-center justify-center gap-2 rounded-full bg-primary px-8 min-h-16 text-xl font-bold text-primary-foreground hover:brightness-110"
      >
        {t("feel.send")}
      </button>
    </div>
  );
}
