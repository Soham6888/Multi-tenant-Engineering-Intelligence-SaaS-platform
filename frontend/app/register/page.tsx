import { AuthForm } from "@/components/auth-form";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Create an account · Engineering Intelligence",
  robots: { index: false, follow: false },
};
export default function RegisterPage() {
  return <AuthForm mode="register" />;
}
