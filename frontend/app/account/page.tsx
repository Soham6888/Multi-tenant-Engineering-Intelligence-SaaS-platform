"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { type FormEvent, useEffect, useState } from "react";
import {
  ArrowRight,
  Building2,
  ChartNoAxesCombined,
  CirclePlus,
  Clipboard,
  LoaderCircle,
  LogOut,
  ShieldCheck,
  Send,
  Users,
} from "lucide-react";
import {
  ApiError,
  authRequest,
  organizationsRequest,
  type Identity,
  type Organization,
  type Page,
} from "@/lib/auth";
import "@/app/auth.css";

export default function AccountPage() {
  const router = useRouter();
  const [identity, setIdentity] = useState<Identity | null>(null);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [pageBusy, setPageBusy] = useState(false);
  const [name, setName] = useState("");
  const [inviteToken, setInviteToken] = useState("");
  const [acceptMessage, setAcceptMessage] = useState("");
  const [acceptBusy, setAcceptBusy] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError("");
    authRequest("me", { signal: controller.signal })
      .then(async (session) => {
        const page = await organizationsRequest<Page<Organization>>("", {
          signal: controller.signal,
        });
        if (controller.signal.aborted) return;
        setIdentity(session);
        setOrganizations(page.data);
        setNextCursor(page.pagination.next_cursor);
      })
      .catch((failure) => {
        if (controller.signal.aborted) return;
        if (failure instanceof ApiError && failure.status === 401) {
          router.replace("/login");
          return;
        }
        setError(
          "We couldn’t load your workspace. Check that the API and PostgreSQL are running, then try again.",
        );
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [router, retry]);

  async function createOrganization(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!name.trim() || busy) return;
    setBusy(true);
    setError("");
    try {
      await organizationsRequest("", { method: "POST", body: { name } });
      setName("");
      const page = await organizationsRequest<Page<Organization>>();
      setOrganizations(page.data);
      setNextCursor(page.pagination.next_cursor);
    } catch (failure) {
      setError(
        failure instanceof ApiError && failure.status === 409
          ? "That workspace name is already in use. Try another name."
          : "We couldn’t create the workspace. Please try again.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function acceptInvitation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (acceptBusy) return;
    setAcceptBusy(true);
    setAcceptMessage("");
    try {
      const organization = await organizationsRequest<Organization>(
        "/invitations/accept",
        { method: "POST", body: { token: inviteToken.trim() } },
      );
      setOrganizations((current) =>
        current.some((item) => item.id === organization.id)
          ? current
          : [...current, organization],
      );
      setInviteToken("");
      setAcceptMessage(`You joined ${organization.name}.`);
    } catch {
      setAcceptMessage(
        "This invitation is invalid or expired, or it was sent to another email address. Sign in to the invited account and try again.",
      );
    } finally {
      setAcceptBusy(false);
    }
  }

  async function loadMore() {
    if (!nextCursor || pageBusy) return;
    setPageBusy(true);
    try {
      const page = await organizationsRequest<Page<Organization>>(
        `?cursor=${encodeURIComponent(nextCursor)}`,
      );
      setOrganizations((current) => [
        ...current,
        ...page.data.filter(
          (item) => !current.some((old) => old.id === item.id),
        ),
      ]);
      setNextCursor(page.pagination.next_cursor);
    } catch {
      setError("We couldn't load more workspaces. Please try again.");
    } finally {
      setPageBusy(false);
    }
  }

  async function logout() {
    if (!identity || busy) return;
    setBusy(true);
    setError("");
    try {
      await authRequest("logout", { csrf: identity.csrf_token });
      setIdentity(null);
      router.replace("/login");
    } catch (failure) {
      if (failure instanceof ApiError && failure.status === 401) {
        setIdentity(null);
        router.replace("/login");
        return;
      }
      setError(
        "Sign-out failed. Your session may still be active. Please try again.",
      );
      setBusy(false);
    }
  }

  return (
    <main className="account-layout">
      <header>
        <Link href="/" className="account-brand">
          <ChartNoAxesCombined size={23} />
          engineering intelligence.
        </Link>
        {identity && (
          <button className="button" onClick={logout} disabled={busy}>
            <LogOut size={15} />
            {busy ? "Signing out…" : "Sign out"}
          </button>
        )}
      </header>

      {loading && (
        <section className="account-card" role="status">
          <LoaderCircle className="spin" size={18} />
          Loading your secure workspace…
        </section>
      )}
      {!loading && error && (
        <div className="auth-error account-global-error" role="alert">
          {error}
          <button
            className="button"
            onClick={() => setRetry((value) => value + 1)}
          >
            Try again
          </button>
        </div>
      )}

      {identity && !loading && (
        <>
          <section className="account-welcome">
            <span className="auth-eyebrow">SIGNED IN SECURELY</span>
            <h1>Good to have you here, {identity.user.name}.</h1>
            <p>{identity.user.email}</p>
          </section>

          <section className="workspace-panel">
            <div className="workspace-heading">
              <div>
                <span className="auth-eyebrow">YOUR ACCOUNT</span>
                <h2>Workspaces</h2>
                <p>
                  Each workspace keeps its members and engineering data private.
                </p>
              </div>
              <span className="workspace-count">
                <Building2 size={15} /> {organizations.length}{" "}
                {organizations.length === 1 ? "workspace" : "workspaces"}
              </span>
            </div>

            {organizations.length > 0 && (
              <div className="workspace-grid">
                {organizations.map((organization) => (
                  <WorkspaceCard
                    organization={organization}
                    key={organization.id}
                  />
                ))}
              </div>
            )}

            {nextCursor && (
              <button className="button" onClick={loadMore} disabled={pageBusy}>
                {pageBusy ? "Loading..." : "Load more workspaces"}
              </button>
            )}

            {organizations.length === 0 && (
              <div className="workspace-empty">
                <span className="workspace-empty-icon">
                  <Building2 size={23} />
                </span>
                <h3>Your engineering data starts with a workspace.</h3>
                <p>
                  Create one for your organization. Only members you authorize
                  can access its data.
                </p>
              </div>
            )}

            <form className="workspace-accept" onSubmit={acceptInvitation}>
              <div>
                <label htmlFor="invitation-token">Joining a workspace?</label>
                <p>
                  Sign in with the invited email, then paste the private
                  invitation token.
                </p>
              </div>
              <div className="workspace-create-row">
                <input
                  id="invitation-token"
                  value={inviteToken}
                  onChange={(event) => setInviteToken(event.target.value)}
                  minLength={43}
                  maxLength={43}
                  placeholder="One-time invitation token"
                  required
                />
                <button
                  className="button"
                  type="submit"
                  disabled={acceptBusy || inviteToken.length !== 43}
                >
                  {acceptBusy ? "Joining..." : "Accept invitation"}
                </button>
              </div>
              {acceptMessage && (
                <p className="invite-notice" role="status">
                  {acceptMessage}
                </p>
              )}
            </form>

            <form className="workspace-create" onSubmit={createOrganization}>
              <label htmlFor="workspace-name">Create a workspace</label>
              <div className="workspace-create-row">
                <input
                  id="workspace-name"
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  maxLength={120}
                  placeholder="e.g. Northstar Engineering"
                  required
                />
                <button
                  className="button primary"
                  type="submit"
                  disabled={busy || !name.trim()}
                >
                  {busy ? (
                    <LoaderCircle className="spin" size={16} />
                  ) : (
                    <CirclePlus size={16} />
                  )}
                  Create workspace
                </button>
              </div>
            </form>
          </section>

          <aside className="account-demo-note">
            <ShieldCheck size={18} />
            <p>
              The analytics preview contains sample data. It is not connected to
              your workspaces.
            </p>
            <Link href="/">
              Explore preview <ArrowRight size={14} />
            </Link>
          </aside>
        </>
      )}
    </main>
  );
}

function WorkspaceCard({ organization }: { organization: Organization }) {
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("DEVELOPER");
  const [token, setToken] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const canInvite =
    organization.role === "OWNER" || organization.role === "ADMIN";

  async function invite(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setToken("");
    setNotice("");
    try {
      const result = await organizationsRequest<{
        token: string;
        email: string;
        expires_at: string;
      }>(`/${organization.id}/invitations`, {
        method: "POST",
        body: { email, role },
      });
      setToken(result.token);
      setNotice(`Invitation for ${result.email} expires in seven days.`);
      setEmail("");
    } catch (failure) {
      setNotice(
        failure instanceof ApiError && failure.status === 409
          ? "That person is already a member or has an invitation conflict."
          : "We couldn't create the invitation. Check your permissions and try again.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <article className="workspace-card">
      <span className="workspace-icon">
        <Building2 size={19} />
      </span>
      <div className="workspace-card-copy">
        <h3>{organization.name}</h3>
        <p>{organization.slug}</p>
      </div>
      <span className="role-pill">{organization.role}</span>
      <span className="workspace-members">
        <Users size={14} /> Private to members
      </span>
      {canInvite && (
        <details className="workspace-invite">
          <summary>
            <Send size={13} /> Invite a teammate
          </summary>
          <form onSubmit={invite}>
            <label htmlFor={`invite-email-${organization.id}`}>
              Work email
            </label>
            <input
              id={`invite-email-${organization.id}`}
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="teammate@company.com"
            />
            <label htmlFor={`invite-role-${organization.id}`}>
              Workspace role
            </label>
            <select
              id={`invite-role-${organization.id}`}
              value={role}
              onChange={(event) => setRole(event.target.value)}
            >
              {organization.role === "OWNER" && (
                <option value="ADMIN">Administrator</option>
              )}
              <option value="MANAGER">Engineering manager</option>
              <option value="DEVELOPER">Developer</option>
              <option value="VIEWER">Viewer</option>
            </select>
            <button
              className="button primary"
              type="submit"
              disabled={busy || !email}
            >
              {busy ? "Creating..." : "Create invitation"}
            </button>
            {notice && (
              <p role="status" className="invite-notice">
                {notice}
              </p>
            )}
            {token && (
              <div className="invite-token">
                <span>Share this one-time invitation token privately:</span>
                <code>{token}</code>
                <button
                  className="button"
                  type="button"
                  onClick={async () => {
                    try {
                      await navigator.clipboard.writeText(token);
                      setNotice(
                        "Invitation token copied. Share it privately with the invitee.",
                      );
                    } catch {
                      setNotice(
                        "Copy is unavailable. Select and copy the token manually.",
                      );
                    }
                  }}
                >
                  <Clipboard size={13} /> Copy token
                </button>
              </div>
            )}
          </form>
        </details>
      )}
    </article>
  );
}
