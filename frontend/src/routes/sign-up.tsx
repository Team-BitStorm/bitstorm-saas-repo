import { createFileRoute } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";

import { AuthLayout } from "@/components/auth/AuthLayout";
import { SignUpForm } from "@/components/auth/SignUpForm";

export const Route = createFileRoute("/sign-up")({
  component: SignUpPage,
});

function SignUpPage() {
  const { t } = useTranslation();

  return (
    <AuthLayout title={t("auth.signUpTitle")} subtitle={t("auth.signUpSubtitle")}>
      <SignUpForm />
    </AuthLayout>
  );
}
