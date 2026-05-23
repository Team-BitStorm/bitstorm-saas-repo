import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { LogOut, User } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { Button } from "@/components/ui/button";
import { logout } from "@/lib/auth";
import { useAuth } from "@/lib/auth-context";
import { usePatient } from "@/lib/patient-context";

export const Route = createFileRoute("/profile")({
  component: ProfilePage,
});

function ProfilePage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { patient: p } = usePatient();
  const { signOut } = useAuth();
  const [isSigningOut, setIsSigningOut] = useState(false);

  async function handleSignOut() {
    setIsSigningOut(true);
    try {
      await logout();
      signOut();
      await navigate({ to: "/login" });
    } finally {
      setIsSigningOut(false);
    }
  }

  return (
    <div className="space-y-8">
      <header className="flex items-center gap-4">
        <div className="flex size-20 items-center justify-center rounded-full bg-primary text-primary-foreground">
          <User aria-hidden="true" className="size-10" />
        </div>
        <div>
          <h1 className="font-display text-4xl">
            {p.firstName} {p.lastName}
          </h1>
          <p className="text-base text-muted-foreground">
            {t("profile.born", { dob: p.dob, blood: p.bloodType })}
          </p>
        </div>
      </header>

      <section aria-labelledby="allergies-h">
        <h2 id="allergies-h" className="font-display text-2xl mb-3">
          {t("profile.allergies")}
        </h2>
        <div className="flex flex-wrap gap-2">
          {p.allergies.map((a) => (
            <span
              key={a}
              className="inline-flex items-center rounded-full bg-destructive/15 border-2 border-destructive/40 px-4 py-2 text-base font-bold text-destructive"
            >
              ⚠ {a}
            </span>
          ))}
        </div>
      </section>

      <div className="rounded-3xl border-2 border-dashed border-border p-6 text-center text-muted-foreground">
        {t("profile.comingNext")}
      </div>

      <Button
        type="button"
        variant="outline"
        disabled={isSigningOut}
        onClick={() => void handleSignOut()}
        className="w-full min-h-14 rounded-full text-lg font-semibold border-2"
      >
        <LogOut aria-hidden="true" className="size-5" />
        {isSigningOut ? t("profile.signingOut") : t("profile.signOut")}
      </Button>
    </div>
  );
}
