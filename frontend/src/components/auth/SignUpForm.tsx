import { Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { VoiceInputButton } from "@/components/accessibility/VoiceInputButton";
import { ApiError } from "@/lib/api";
import { getRoleHome, register, type UserRole } from "@/lib/auth";
import { useAuth } from "@/lib/auth-context";

export function SignUpForm() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { setUser } = useAuth();

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [role, setRole] = useState<UserRole>("customer");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError(t("auth.errors.passwordMismatch"));
      return;
    }
    if (password.length < 8) {
      setError(t("auth.errors.passwordTooShort"));
      return;
    }

    setIsSubmitting(true);
    try {
      const user = await register({
        email: email.trim(),
        password,
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        role,
      });
      setUser(user);
      await navigate({ to: user.role === "customer" ? "/onboarding" : "/provider/onboarding" });
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

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="firstName" className="text-base">
            {t("auth.firstName")}
          </Label>
          <div className="flex gap-2">
            <Input
              id="firstName"
              autoComplete="given-name"
              required
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              className="min-h-14 text-lg rounded-2xl flex-1"
            />
            <VoiceInputButton onTranscript={setFirstName} />
          </div>
        </div>
        <div className="space-y-2">
          <Label htmlFor="lastName" className="text-base">
            {t("auth.lastName")}
          </Label>
          <Input
            id="lastName"
            autoComplete="family-name"
            required
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            className="min-h-14 text-lg rounded-2xl"
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="signup-email" className="text-base">
          {t("auth.email")}
        </Label>
        <Input
          id="signup-email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="min-h-14 text-lg rounded-2xl"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="role" className="text-base">
          {t("auth.role")}
        </Label>
        <Select value={role} onValueChange={(v) => setRole(v as UserRole)}>
          <SelectTrigger id="role" className="min-h-14 text-lg rounded-2xl">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="customer">{t("auth.rolePatient")}</SelectItem>
            <SelectItem value="provider">{t("auth.roleCaregiver")}</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="signup-password" className="text-base">
          {t("auth.password")}
        </Label>
        <Input
          id="signup-password"
          type="password"
          autoComplete="new-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="min-h-14 text-lg rounded-2xl"
        />
        <p className="text-sm text-muted-foreground">{t("auth.passwordHint")}</p>
      </div>

      <div className="space-y-2">
        <Label htmlFor="confirm-password" className="text-base">
          {t("auth.confirmPassword")}
        </Label>
        <Input
          id="confirm-password"
          type="password"
          autoComplete="new-password"
          required
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          className="min-h-14 text-lg rounded-2xl"
        />
      </div>

      <Button
        type="submit"
        disabled={isSubmitting}
        className="w-full min-h-14 rounded-full text-lg font-semibold"
      >
        {isSubmitting ? t("auth.creatingAccount") : t("auth.createAccount")}
      </Button>

      <p className="text-center text-muted-foreground">
        {t("auth.haveAccount")}{" "}
        <Link to="/login" className="font-semibold text-primary underline-offset-4 hover:underline">
          {t("auth.signIn")}
        </Link>
      </p>
    </form>
  );
}
