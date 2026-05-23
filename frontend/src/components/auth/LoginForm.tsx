import { Link, useNavigate, useSearch } from "@tanstack/react-router";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { VoiceInputButton } from "@/components/accessibility/VoiceInputButton";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  InputOTP,
  InputOTPGroup,
  InputOTPSlot,
} from "@/components/ui/input-otp";
import { ApiError } from "@/lib/api";
import {
  getRoleHome,
  login,
  startTwoFactorChallenge,
  verifyTwoFactorLogin,
} from "@/lib/auth";
import { useAuth } from "@/lib/auth-context";

type Step = "credentials" | "method" | "code";

export function LoginForm() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const search = useSearch({ from: "/login" });
  const { setUser } = useAuth();

  const [step, setStep] = useState<Step>("credentials");
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [preAuthToken, setPreAuthToken] = useState("");
  const [methods, setMethods] = useState<string[]>([]);
  const [selectedMethod, setSelectedMethod] = useState<"sms" | "totp" | null>(null);
  const [code, setCode] = useState("");
  const [devOtp, setDevOtp] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleCredentials(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const data = await login(identifier.trim(), password);
      if (data.requires_2fa) {
        setPreAuthToken(data.pre_auth_token);
        setMethods(data.available_2fa_methods);
        if (data.available_2fa_methods.length === 1) {
          const method = data.available_2fa_methods[0] as "sms" | "totp";
          await pickMethod(method, data.pre_auth_token);
        } else {
          setStep("method");
        }
        return;
      }
      setUser(data.user);
      const redirect =
        typeof search.redirect === "string" && search.redirect.startsWith("/")
          ? search.redirect
          : getRoleHome(data.user.role);
      await navigate({ to: redirect });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("auth.errors.generic"));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function pickMethod(method: "sms" | "totp", token = preAuthToken) {
    setError(null);
    setIsSubmitting(true);
    try {
      setSelectedMethod(method);
      const challenge = await startTwoFactorChallenge(token, method);
      if (challenge.otp_code) setDevOtp(challenge.otp_code);
      setStep("code");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("auth.errors.generic"));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleVerify(event: React.FormEvent) {
    event.preventDefault();
    if (!selectedMethod) return;
    setError(null);
    setIsSubmitting(true);
    try {
      const user = await verifyTwoFactorLogin(preAuthToken, selectedMethod, code);
      setUser(user);
      const redirect =
        typeof search.redirect === "string" && search.redirect.startsWith("/")
          ? search.redirect
          : getRoleHome(user.role);
      await navigate({ to: redirect });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("auth.errors.generic"));
    } finally {
      setIsSubmitting(false);
    }
  }

  if (step === "method") {
    return (
      <div className="space-y-5">
        {error ? (
          <p role="alert" className="rounded-2xl border-2 border-destructive/40 bg-destructive/10 px-4 py-3 text-destructive">
            {error}
          </p>
        ) : null}
        <h2 className="font-display text-2xl">{t("auth.choose2fa")}</h2>
        <div className="grid gap-3">
          {methods.includes("sms") ? (
            <Button
              type="button"
              disabled={isSubmitting}
              onClick={() => void pickMethod("sms")}
              className="min-h-14 rounded-full text-lg"
            >
              {t("auth.useSms")}
            </Button>
          ) : null}
          {methods.includes("totp") ? (
            <Button
              type="button"
              variant="outline"
              disabled={isSubmitting}
              onClick={() => void pickMethod("totp")}
              className="min-h-14 rounded-full text-lg border-2"
            >
              {t("auth.useTotp")}
            </Button>
          ) : null}
        </div>
      </div>
    );
  }

  if (step === "code") {
    return (
      <form onSubmit={handleVerify} className="space-y-5">
        {error ? (
          <p role="alert" className="rounded-2xl border-2 border-destructive/40 bg-destructive/10 px-4 py-3 text-destructive">
            {error}
          </p>
        ) : null}
        <h2 className="font-display text-2xl">{t("auth.enterCode")}</h2>
        {devOtp ? (
          <p className="text-sm text-muted-foreground">{t("auth.devOtp", { code: devOtp })}</p>
        ) : null}
        <InputOTP maxLength={6} value={code} onChange={setCode}>
          <InputOTPGroup>
            {[0, 1, 2, 3, 4, 5].map((i) => (
              <InputOTPSlot key={i} index={i} className="min-h-14 min-w-12 text-xl rounded-xl" />
            ))}
          </InputOTPGroup>
        </InputOTP>
        <Button
          type="submit"
          disabled={isSubmitting || code.length !== 6}
          className="w-full min-h-14 rounded-full text-lg font-semibold"
        >
          {isSubmitting ? t("auth.verifying") : t("auth.verify")}
        </Button>
      </form>
    );
  }

  return (
    <form onSubmit={handleCredentials} className="space-y-5">
      {error ? (
        <p role="alert" className="rounded-2xl border-2 border-destructive/40 bg-destructive/10 px-4 py-3 text-destructive">
          {error}
        </p>
      ) : null}

      <div className="space-y-2">
        <Label htmlFor="identifier" className="text-base">
          {t("auth.identifier")}
        </Label>
        <div className="flex gap-2">
          <Input
            id="identifier"
            type="text"
            autoComplete="username"
            required
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
            className="min-h-14 text-lg rounded-2xl flex-1"
          />
          <VoiceInputButton onTranscript={setIdentifier} />
        </div>
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
        <Link to="/forgot-password" className="font-semibold text-primary underline-offset-4 hover:underline">
          {t("auth.forgotPassword")}
        </Link>
      </p>

      <p className="text-center text-muted-foreground">
        {t("auth.noAccount")}{" "}
        <Link to="/sign-up" className="font-semibold text-primary underline-offset-4 hover:underline">
          {t("auth.createAccount")}
        </Link>
      </p>
    </form>
  );
}
