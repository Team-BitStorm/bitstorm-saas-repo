import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { LogOut, User } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { SecuritySettings } from "@/components/auth/SecuritySettings";
import { Button } from "@/components/ui/button";
import { getRoleHome, logout } from "@/lib/auth";
import { useAuth } from "@/lib/auth-context";

export const Route = createFileRoute("/profile")({
  component: ProfilePage,
});

function ProfilePage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { user, signOut } = useAuth();
  const [isSigningOut, setIsSigningOut] = useState(false);

  if (!user) return null;

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
            {user.first_name} {user.last_name}
          </h1>
          <p className="text-base text-muted-foreground">{user.email}</p>
          <p className="text-sm text-muted-foreground capitalize">{user.role}</p>
        </div>
      </header>

      {user.role === "customer" ? (
        <Button
          type="button"
          variant="outline"
          onClick={() => void navigate({ to: "/onboarding" })}
          className="min-h-14 rounded-full border-2 w-full"
        >
          {t("customer.editProfile")}
        </Button>
      ) : (
        <Button
          type="button"
          variant="outline"
          onClick={() => void navigate({ to: "/provider/onboarding" })}
          className="min-h-14 rounded-full border-2 w-full"
        >
          {t("provider.editProfile")}
        </Button>
      )}

      <SecuritySettings />

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

      <Button
        type="button"
        variant="ghost"
        onClick={() => void navigate({ to: getRoleHome(user.role) })}
        className="w-full min-h-12"
      >
        {t("common.backHome")}
      </Button>
    </div>
  );
}
