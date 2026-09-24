"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import {
  ArrowRight,
  ChartNoAxesCombined,
  Check,
  Eye,
  EyeOff,
  GitBranch,
  LoaderCircle,
  ShieldCheck,
} from "lucide-react";
import { ApiError, authRequest } from "@/lib/auth";
import "@/app/auth.css";

export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const register = mode === "register";
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [visible, setVisible] = useState(false);
  const [error, setError] = useState("");
  const [requestId, setRequestId] = useState<string>();

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    const form = new FormData(event.currentTarget);
    setBusy(true);
    setError("");
    setRequestId(undefined);
    try {
      await authRequest(mode, {
        body: {
          email: form.get("email"),
          password: form.get("password"),
          ...(register ? { name: form.get("name") } : {}),
        },
      });
      router.replace("/account");
    } catch (failure) {
      setError(
        failure instanceof Error
          ? failure.message
          : "Unable to connect. Please try again.",
      );
      if (failure instanceof ApiError) setRequestId(failure.requestId);
      setBusy(false);
    }
  }

  return (
    <main className="auth-layout">
      <section className="auth-story">
        <Link href="/" className="auth-brand">
          <span className="brand-symbol">
            <ChartNoAxesCombined size={24} />
          </span>
          <span>
            engineering
            <br />
            intelligence.
          </span>
        </Link>
        <div className="auth-story-content">
          <span className="auth-eyebrow">BUILT FOR THE BIGGER PICTURE</span>
          <h1>
            Understand the work.
            <br />
            <em>Improve the flow.</em>
          </h1>
          <p>
            A clearer view of your engineering systems, from the first pull
            request to the next release.
          </p>
          <div className="auth-flow" aria-hidden="true">
            <span>
              <GitBranch size={18} />
              Activity
            </span>
            <i />
            <span>
              <ChartNoAxesCombined size={18} />
              Intelligence
            </span>
          </div>
          <div className="auth-principles">
            <span>
              <Check size={15} />
              Evidence before assumptions
            </span>
            <span>
              <Check size={15} />
              Workflow health, never employee scores
            </span>
            <span>
              <Check size={15} />
              Local-first, built with purpose
            </span>
          </div>
        </div>
        <div className="auth-story-footer">
          ENGINEERING INTELLIGENCE PLATFORM <span>01 / FOUNDATION</span>
        </div>
      </section>
      <section className="auth-form-section">
        <div className="auth-top-link">
          {register ? "Already have an account?" : "New to the platform?"}{" "}
          <Link href={register ? "/login" : "/register"}>
            {register ? "Sign in" : "Create an account"}
            <ArrowRight size={13} />
          </Link>
        </div>
        <div className="auth-form-card">
          <span className="auth-form-icon">
            <ShieldCheck size={23} />
          </span>
          <span className="auth-eyebrow">YOUR ENGINEERING WORKSPACE</span>
          <h2>{register ? "Start with a clear view." : "Welcome back."}</h2>
          <p>
            {register
              ? "Create your account. Connect your organization as the platform grows."
              : "Sign in to your Engineering Intelligence account."}
          </p>
          <form
            onSubmit={submit}
            aria-label={register ? "Create account" : "Sign in"}
          >
            {register && (
              <label>
                Full name
                <input
                  name="name"
                  autoComplete="name"
                  placeholder="Your name"
                  required
                  maxLength={100}
                  disabled={busy}
                />
              </label>
            )}
            <label>
              Email address
              <input
                type="email"
                name="email"
                autoComplete="email"
                placeholder="you@company.com"
                required
                maxLength={320}
                disabled={busy}
              />
            </label>
            <label>
              Password
              <div className="password-input">
                <input
                  type={visible ? "text" : "password"}
                  name="password"
                  autoComplete={register ? "new-password" : "current-password"}
                  required
                  minLength={register ? 15 : 1}
                  maxLength={128}
                  disabled={busy}
                  aria-describedby={register ? "password-hint" : undefined}
                />
                <button
                  type="button"
                  aria-label={visible ? "Hide password" : "Show password"}
                  onClick={() => setVisible(!visible)}
                >
                  {visible ? <EyeOff size={17} /> : <Eye size={17} />}
                </button>
              </div>
            </label>
            {register && (
              <small id="password-hint" className="password-hint">
                Use 15–128 characters. A memorable passphrase works well.
              </small>
            )}
            {error && (
              <div className="auth-error" role="alert">
                <strong>{error}</strong>
                {requestId && <small>Reference: {requestId}</small>}
              </div>
            )}
            <button className="auth-submit" disabled={busy} type="submit">
              {busy ? (
                <>
                  <LoaderCircle className="spin" size={17} />
                  Please wait…
                </>
              ) : (
                <>
                  {register ? "Create account" : "Sign in"}
                  <ArrowRight size={17} />
                </>
              )}
            </button>
          </form>
          <div className="auth-security">
            <ShieldCheck size={14} />
            Your session stays in an HttpOnly cookie. Production requires HTTPS.
          </div>
          <div className="auth-preview-link">
            Just exploring?{" "}
            <Link href="/">
              View the demo workspace <ArrowRight size={12} />
            </Link>
          </div>
        </div>
        <footer className="auth-form-footer">
          Account access is live when local services are running.
          <br />
          GitHub connections and organizations are upcoming milestones.
        </footer>
      </section>
    </main>
  );
}
