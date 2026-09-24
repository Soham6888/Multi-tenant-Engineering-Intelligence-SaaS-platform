import { AuthForm } from "@/components/auth-form";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Sign in · Engineering Intelligence",
  robots: { index: false, follow: false },
};
export default function LoginPage() {
  return <AuthForm mode="login" />;
}
