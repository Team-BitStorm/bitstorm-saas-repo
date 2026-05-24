import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { QRCodeSVG } from "qrcode.react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

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
  confirmTotpSetup,
  disableTwoFactor,
  fetchTwoFactorStatus,
  setTwoFactorMethod,
  setupTotp,
} from "@/lib/auth";

export function SecuritySettings() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [totpCode, setTotpCode] = useState("");
  const [disablePassword, setDisablePassword] = useState("");
  const [setupUri, setSetupUri] = useState<string | null>(null);
  const [setupSecret, setSetupSecret] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const statusQuery = useQuery({
    queryKey: ["2fa-status"],
    queryFn: fetchTwoFactorStatus,
  });

  const smsMutation = useMutation({
    mutationFn: (enabled: boolean) => setTwoFactorMethod("sms", enabled),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["2fa-status"] });
      setMessage(t("security.smsUpdated"));
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : t("errors.generic")),
  });

  const totpSetupMutation = useMutation({
    mutationFn: setupTotp,
    onSuccess: (data) => {
      setSetupUri(data.provisioning_uri);
      setSetupSecret(data.secret);
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : t("errors.generic")),
  });

  const totpConfirmMutation = useMutation({
    mutationFn: async () => {
      await confirmTotpSetup(totpCode);
      await setTwoFactorMethod("totp", true);
    },
    onSuccess: () => {
      setTotpCode("");
      setSetupUri(null);
      setSetupSecret(null);
      void queryClient.invalidateQueries({ queryKey: ["2fa-status"] });
      setMessage(t("security.totpEnabled"));
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : t("errors.generic")),
  });

  const disableMutation = useMutation({
    mutationFn: () => disableTwoFactor(disablePassword),
    onSuccess: () => {
      setDisablePassword("");
      void queryClient.invalidateQueries({ queryKey: ["2fa-status"] });
      setMessage(t("security.disabled"));
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : t("errors.generic")),
  });

  const status = statusQuery.data;

  return (
    <section aria-labelledby="security-heading" className="space-y-6">
      <h2 id="security-heading" className="font-display text-2xl">
        {t("security.title")}
      </h2>

      {message ? (
        <p role="status" className="rounded-2xl border-2 border-success/40 bg-success/10 px-4 py-3">
          {message}
        </p>
      ) : null}
      {error ? (
        <p role="alert" className="rounded-2xl border-2 border-destructive/40 bg-destructive/10 px-4 py-3 text-destructive">
          {error}
        </p>
      ) : null}

      <div className="rounded-3xl border-2 border-border p-6 space-y-4">
        <h3 className="font-display text-xl">{t("security.smsTitle")}</h3>
        <p className="text-muted-foreground">{t("security.smsDesc")}</p>
        <Button
          type="button"
          disabled={smsMutation.isPending}
          onClick={() => smsMutation.mutate(!status?.sms_2fa_enabled)}
          className="min-h-14 rounded-full"
        >
          {status?.sms_2fa_enabled ? t("security.disableSms") : t("security.enableSms")}
        </Button>
      </div>

      <div className="rounded-3xl border-2 border-border p-6 space-y-4">
        <h3 className="font-display text-xl">{t("security.totpTitle")}</h3>
        <p className="text-muted-foreground">{t("security.totpDesc")}</p>
        {!setupUri ? (
          <Button
            type="button"
            disabled={totpSetupMutation.isPending}
            onClick={() => totpSetupMutation.mutate()}
            className="min-h-14 rounded-full"
          >
            {t("security.startTotp")}
          </Button>
        ) : (
          <div className="space-y-4">
            <div className="flex justify-center rounded-2xl bg-card p-4">
              <QRCodeSVG value={setupUri} size={180} />
            </div>
            {setupSecret ? (
              <p className="text-sm break-all">
                {t("security.manualSecret")}: <strong>{setupSecret}</strong>
              </p>
            ) : null}
            <div className="space-y-2">
              <Label>{t("security.enterCode")}</Label>
              <InputOTP maxLength={6} value={totpCode} onChange={setTotpCode}>
                <InputOTPGroup>
                  {[0, 1, 2, 3, 4, 5].map((i) => (
                    <InputOTPSlot key={i} index={i} className="min-h-14 min-w-12 text-xl rounded-xl" />
                  ))}
                </InputOTPGroup>
              </InputOTP>
            </div>
            <Button
              type="button"
              disabled={totpCode.length !== 6 || totpConfirmMutation.isPending}
              onClick={() => totpConfirmMutation.mutate()}
              className="min-h-14 rounded-full"
            >
              {t("security.confirmTotp")}
            </Button>
          </div>
        )}
      </div>

      <div className="rounded-3xl border-2 border-border p-6 space-y-4">
        <h3 className="font-display text-xl">{t("security.disableTitle")}</h3>
        <div className="space-y-2">
          <Label htmlFor="disable-password">{t("auth.password")}</Label>
          <Input
            id="disable-password"
            type="password"
            value={disablePassword}
            onChange={(e) => setDisablePassword(e.target.value)}
            className="min-h-14 text-lg rounded-2xl"
          />
        </div>
        <Button
          type="button"
          variant="outline"
          disabled={!disablePassword || disableMutation.isPending}
          onClick={() => disableMutation.mutate()}
          className="min-h-14 rounded-full border-2"
        >
          {t("security.disableAll")}
        </Button>
      </div>
    </section>
  );
}
