import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { AuthLayout } from "@/components/auth/AuthLayout";
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
import { confirmPasswordReset, requestPasswordReset } from "@/lib/auth";

export const Route = createFileRoute("/forgot-password")({
  component: ForgotPasswordPage,
});

type Step = "phone" | "otp" | "done";

function ForgotPasswordPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [step, setStep] = useState<Step>("phone");
  const [phone, setPhone] = useState("");
  const [otp, setOtp] = useState("");
  const [password, setPassword] = useState("");
  const [devOtp, setDevOtp] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handlePhone(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const res = await requestPasswordReset(phone.trim());
      if (res.otp_code) setDevOtp(res.otp_code);
      setStep("otp");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("auth.errors.generic"));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleReset(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await confirmPasswordReset(phone.trim(), otp, password);
      setStep("done");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("auth.errors.generic"));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <AuthLayout title={t("auth.forgotPassword")} subtitle={t("auth.forgotSubtitle")}>
      {step === "done" ? (
        <div className="space-y-5 text-center">
          <p>{t("auth.passwordUpdated")}</p>
          <Button onClick={() => void navigate({ to: "/login" })} className="min-h-14 rounded-full w-full">
            {t("auth.signIn")}
          </Button>
        </div>
      ) : step === "otp" ? (
        <form onSubmit={handleReset} className="space-y-5">
          {error ? (
            <p role="alert" className="rounded-2xl border-2 border-destructive/40 bg-destructive/10 px-4 py-3 text-destructive">
              {error}
            </p>
          ) : null}
          {devOtp ? (
            <p className="text-sm text-muted-foreground">{t("auth.devOtp", { code: devOtp })}</p>
          ) : null}
          <div className="space-y-2">
            <Label>{t("auth.enterCode")}</Label>
            <InputOTP maxLength={6} value={otp} onChange={setOtp}>
              <InputOTPGroup>
                {[0, 1, 2, 3, 4, 5].map((i) => (
                  <InputOTPSlot key={i} index={i} className="min-h-14 min-w-12 text-xl rounded-xl" />
                ))}
              </InputOTPGroup>
            </InputOTP>
          </div>
          <div className="space-y-2">
            <Label htmlFor="new-password">{t("auth.newPassword")}</Label>
            <Input
              id="new-password"
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="min-h-14 text-lg rounded-2xl"
            />
          </div>
          <Button type="submit" disabled={isSubmitting || otp.length !== 6} className="w-full min-h-14 rounded-full">
            {t("auth.resetPassword")}
          </Button>
        </form>
      ) : (
        <form onSubmit={handlePhone} className="space-y-5">
          {error ? (
            <p role="alert" className="rounded-2xl border-2 border-destructive/40 bg-destructive/10 px-4 py-3 text-destructive">
              {error}
            </p>
          ) : null}
          <div className="space-y-2">
            <Label htmlFor="phone">{t("auth.phone")}</Label>
            <div className="flex gap-2">
              <Input
                id="phone"
                type="tel"
                required
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className="min-h-14 text-lg rounded-2xl flex-1"
              />
              <VoiceInputButton onTranscript={setPhone} />
            </div>
          </div>
          <Button type="submit" disabled={isSubmitting} className="w-full min-h-14 rounded-full">
            {t("auth.sendCode")}
          </Button>
          <p className="text-center">
            <Link to="/login" className="text-primary font-semibold hover:underline">
              {t("auth.backToLogin")}
            </Link>
          </p>
        </form>
      )}
    </AuthLayout>
  );
}
