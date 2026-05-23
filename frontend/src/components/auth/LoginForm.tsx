import { Link, useNavigate, useSearch } from "@tanstack/react-router";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError } from "@/lib/api";
import { login } from "@/lib/auth";
import { useAuth } from "@/lib/auth-context";

export function LoginForm() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const search = useSearch({ from: "/login" });
  const { setUser } = useAuth();

  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const user = await login(identifier.trim(), password);
      setUser(user);
      const redirect =
        typeof search.redirect === "string" && search.redirect.startsWith("/")
          ? search.redirect
          : "/";
      await navigate({ to: redirect });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("auth.errors.generic"));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {error ? (
        <p
          role="alert"
          className="rounded-2xl border-2 border-destructive/40 bg-destructive/10 px-4 py-3 text-base text-destructive"
        >
          {error}
        </p>
      ) : null}

      <div className="space-y-2">
        <Label htmlFor="identifier" className="text-base">
          {t("auth.identifier", {
            defaultValue: "Email, phone, or CNP",
          })}
        </Label>
        <Input
          id="identifier"
          type="text"
          autoComplete="username"
          required
          value={identifier}
          onChange={(e) => setIdentifier(e.target.value)}
          className="min-h-14 text-lg rounded-2xl"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="password" className="text-base">
          {t("auth.password")}
        </Label>
        <Input
          id="password"
          type="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="min-h-14 text-lg rounded-2xl"
        />
      </div>

      <Button
        type="submit"
        disabled={isSubmitting}
        className="w-full min-h-14 rounded-full text-lg font-semibold"
      >
        {isSubmitting ? t("auth.signingIn") : t("auth.signIn")}
      </Button>

      <p className="text-center text-muted-foreground">
        {t("auth.noAccount")}{" "}
        <Link to="/sign-up" className="font-semibold text-primary underline-offset-4 hover:underline">
          {t("auth.createAccount")}
        </Link>
      </p>
    </form>
  );
}
