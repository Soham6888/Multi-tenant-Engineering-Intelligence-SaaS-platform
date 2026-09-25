"use client";

import Link from "next/link";

import { useEffect, useRef, useState, type ReactNode } from "react";
import {
  Activity,
  ArrowDownLeft,
  ArrowRight,
  ArrowUpRight,
  Bell,
  BookOpen,
  Box,
  ChartNoAxesCombined,
  Check,
  ChevronDown,
  ChevronRight,
  CircleHelp,
  Clock3,
  Code2,
  Command,
  Download,
  ExternalLink,
  FolderGit2,
  GitBranch,
  Github,
  GitMerge,
  GitPullRequest,
  HeartPulse,
  LayoutDashboard,
  Menu,
  MoreHorizontal,
  Radio,
  Rocket,
  Search,
  Settings,
  ShieldCheck,
  Sparkles,
  Users,
  Workflow,
  X,
  type LucideIcon,
} from "lucide-react";
import { activity, pullRequests, repositories, summarize } from "@/lib/demo";
import { ActivityChart, TrendChart } from "./charts";

const mainNav: [string, LucideIcon][] = [
  ["Overview", LayoutDashboard],
  ["Repositories", FolderGit2],
  ["Pull Requests", GitPullRequest],
  ["Deployments", Rocket],
  ["CI/CD", Workflow],
  ["Engineering Health", HeartPulse],
  ["AI Assistant", Sparkles],
  ["Alerts", Bell],
];
const adminNav: [string, LucideIcon][] = [
  ["Team", Users],
  ["Integrations", Box],
  ["Audit Logs", ShieldCheck],
  ["Settings", Settings],
];
const descriptions: Record<string, string> = {
  Overview: "See what shipped. Find what needs your attention.",
  Repositories: "A closer look at the systems your team is building.",
  "Pull Requests": "Understand review flow and find delivery bottlenecks.",
  Deployments: "Follow every release, from commit to production.",
  "CI/CD": "Understand pipeline reliability across your repositories.",
  "Engineering Health": "Transparent signals about systems and workflows.",
};

function Badge({
  children,
  tone = "green",
}: {
  children: ReactNode;
  tone?: string;
}) {
  return <span className={`badge ${tone}`}>{children}</span>;
}

function Dialog({
  title,
  children,
  onClose,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const dialog = ref.current;
    dialog?.showModal();
    return () => {
      dialog?.close();
    };
  }, []);
  return (
    <dialog
      ref={ref}
      onCancel={onClose}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      aria-labelledby="dialog-title"
    >
      <div className="dialog-top">
        <span className="eyebrow">ENGINEERING INTELLIGENCE</span>
        <button
          className="icon-button"
          aria-label="Close dialog"
          onClick={onClose}
        >
          <X size={18} />
        </button>
      </div>
      <h2 id="dialog-title">{title}</h2>
      {children}
    </dialog>
  );
}

export function Workspace() {
  const [page, setPage] = useState("Overview");
  const [days, setDays] = useState(30);
  const [repository, setRepository] = useState("all");
  const [search, setSearch] = useState("");
  const [state, setState] = useState("all");
  const [menu, setMenu] = useState(false);
  const [dialog, setDialog] = useState<string | null>(null);
  const [toast, setToast] = useState("");
  const searchRef = useRef<HTMLInputElement>(null);
  const metrics = summarize(days, repository);
  const visibleRepositories = repositories.filter(
    (r) =>
      (repository === "all" || r.name === repository) &&
      `${r.name} ${r.language}`.toLowerCase().includes(search.toLowerCase()),
  );
  const prs = pullRequests.filter(
    (p) =>
      (repository === "all" || p.repo === repository) &&
      (state === "all" || p.state === state) &&
      `${p.title} ${p.repo} ${p.author}`
        .toLowerCase()
        .includes(search.toLowerCase()),
  );
  const events = activity.filter(
    (e) =>
      (repository === "all" || e.repo === repository) &&
      `${e.title} ${e.repo}`.toLowerCase().includes(search.toLowerCase()),
  );
  const reviewQueue = pullRequests.filter(
    (pr) =>
      pr.state === "Awaiting review" &&
      (repository === "all" || pr.repo === repository) &&
      `${pr.title} ${pr.repo} ${pr.author}`
        .toLowerCase()
        .includes(search.toLowerCase()),
  );

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key === "k") {
        event.preventDefault();
        searchRef.current?.focus();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);
  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(""), 4500);
    return () => clearTimeout(timer);
  }, [toast]);

  function navigate(destination: string) {
    setPage(destination);
    setMenu(false);
    setSearch("");
  }
  function exportReport() {
    const csv =
      "date,deployments,opened_prs,merged_prs,workflow_runs,workflow_failures\n" +
      metrics.series
        .map((d) =>
          [
            d.date,
            d.deployments,
            d.opened,
            d.merged,
            d.workflows,
            d.failures,
          ].join(","),
        )
        .join("\n");
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = `demo-engineering-${days}d.csv`;
    link.click();
    URL.revokeObjectURL(url);
    setToast("Sample-data report exported as CSV.");
  }

  function repositoryTable() {
    return (
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Repository</th>
              <th>Deployments</th>
              <th>PR cycle time</th>
              <th>CI success</th>
              <th>Signal</th>
              <th>
                <span className="sr-only">Open</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {visibleRepositories.map((repo) => {
              const metric = summarize(days, repo.name);
              return (
                <tr key={repo.name}>
                  <td>
                    <button
                      className="repo-link"
                      onClick={() => {
                        setRepository(repo.name);
                        navigate("Repositories");
                      }}
                    >
                      <span className="repo-icon">
                        <GitBranch size={17} />
                      </span>
                      <span>
                        <strong>{repo.name}</strong>
                        <small>
                          <i style={{ background: repo.color }} />
                          {repo.language}
                        </small>
                      </span>
                    </button>
                  </td>
                  <td>
                    {metric.deployments}
                    <span className="mini-bars" aria-hidden="true">
                      ▂▅▃▇▅▆▇
                    </span>
                  </td>
                  <td>{repo.cycle}h</td>
                  <td>
                    <span className="success-meter">
                      <i style={{ width: `${Number(metric.success) - 12}%` }} />
                    </span>
                    {metric.success}%
                  </td>
                  <td>
                    <Badge tone={repo.cycle > 7 ? "amber" : "green"}>
                      <span className="status-dot" />
                      {repo.cycle > 7 ? "Review latency" : "Stable CI"}
                    </Badge>
                  </td>
                  <td>
                    <button
                      className="icon-button"
                      aria-label={`View ${repo.name}`}
                      onClick={() => {
                        setRepository(repo.name);
                        navigate("Repositories");
                      }}
                    >
                      <ChevronRight size={16} />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {!visibleRepositories.length && (
          <div className="empty-small">No repositories match your filters.</div>
        )}
      </div>
    );
  }

  function recentActivity() {
    return (
      <div className="activity-list">
        {events.map((event, index) => (
          <button
            className="activity-item"
            key={event.title + event.repo}
            onClick={() => setDialog(`${event.repo}: ${event.title}`)}
          >
            <span className={`activity-icon ${event.kind}`}>
              {event.kind === "deploy" ? (
                <Rocket size={16} />
              ) : event.kind === "merge" ? (
                <GitMerge size={16} />
              ) : (
                <X size={16} />
              )}
            </span>
            <span className="activity-copy">
              <strong>{event.title}</strong>
              <small>
                {event.repo}
                <span>·</span>
                {event.detail}
              </small>
            </span>
            <time>{event.time}</time>
            <span className="sr-only">Sample event {index + 1}</span>
          </button>
        ))}
        {!events.length && (
          <div className="empty-small">
            No sample activity matches your filters.
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      {menu && (
        <button
          className="sidebar-scrim"
          aria-label="Close navigation"
          onClick={() => setMenu(false)}
        />
      )}
      <aside className={`sidebar ${menu ? "is-open" : ""}`}>
        <a
          href="/"
          className="brand"
          aria-label="Engineering Intelligence home"
        >
          <span className="brand-symbol">
            <ChartNoAxesCombined size={23} />
          </span>
          <span>
            engineering
            <span className="brand-second">
              intelligence<span className="brand-dot">.</span>
            </span>
          </span>
        </a>
        <button
          className="workspace-picker"
          onClick={() => setDialog("Your workspace")}
        >
          <span className="workspace-avatar">A</span>
          <span>
            <strong>Acme Engineering</strong>
            <small>Demo workspace</small>
          </span>
          <ChevronDown size={14} />
        </button>
        <span className="nav-label">WORKSPACE</span>
        <nav aria-label="Workspace">
          {mainNav.map(([label, Icon]) => (
            <button
              key={label}
              className={`nav-item ${page === label ? "active" : ""}`}
              aria-current={page === label ? "page" : undefined}
              onClick={() => navigate(label)}
            >
              <Icon size={18} />
              <span>{label}</span>
              {label === "AI Assistant" && <span className="ai-tag">AI</span>}
              {label === "Alerts" && <span className="nav-count">0</span>}
            </button>
          ))}
        </nav>
        <div className="nav-divider" />
        <span className="nav-label">MANAGE</span>
        <nav aria-label="Administration">
          {adminNav.map(([label, Icon]) => (
            <button
              key={label}
              className={`nav-item ${page === label ? "active" : ""}`}
              aria-current={page === label ? "page" : undefined}
              onClick={() => navigate(label)}
            >
              <Icon size={18} />
              <span>{label}</span>
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="local-card">
            <span>
              <span className="status-dot" /> LOCAL-FIRST DEVELOPMENT
            </span>
            <p>
              Big-picture intelligence.
              <br />
              Zero cloud spend.
            </p>
            <button onClick={() => setDialog("Built to run locally")}>
              Explore the architecture <ArrowUpRight size={14} />
            </button>
          </div>
          <button className="profile" onClick={() => setDialog("Demo profile")}>
            <span className="user-avatar">SP</span>
            <span>
              <strong>Soham Patil</strong>
              <small>Demo owner</small>
            </span>
            <MoreHorizontal size={18} />
          </button>
        </div>
      </aside>

      <div className="workspace-main">
        <header className="topbar">
          <div className="breadcrumb">
            <button
              className="icon-button mobile-menu"
              aria-label="Open navigation"
              onClick={() => setMenu(true)}
            >
              <Menu size={20} />
            </button>
            <span>Workspace</span>
            <ChevronRight size={13} />
            <strong>{page}</strong>
          </div>
          <div className="topbar-right">
            <Link className="button" href="/login">
              Sign in
            </Link>
            <label className="global-search">
              <Search size={15} />
              <input
                ref={searchRef}
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search current view..."
                aria-label="Search current view"
              />
              <kbd>
                <Command size={10} /> K
              </kbd>
            </label>
            <button
              className="icon-button help-button"
              aria-label="Help"
              onClick={() => setDialog("A clearer view of engineering")}
            >
              <CircleHelp size={18} />
            </button>
            <button
              className="icon-button notification-button"
              aria-label="Notifications"
              onClick={() => setDialog("You’re all caught up")}
            >
              <Bell size={18} />
            </button>
            <span className="topbar-divider" />
            <button
              className="user-avatar small"
              aria-label="Open profile"
              onClick={() => setDialog("Demo profile")}
            >
              SP
            </button>
          </div>
        </header>

        <main id="main">
          <div className="page-heading">
            <div>
              <div className="eyebrow heading-eyebrow">
                ENGINEERING / DELIVERY INTELLIGENCE
              </div>
              <h1>{page === "Overview" ? "Engineering overview" : page}</h1>
              <p>
                {descriptions[page] ||
                  "One workspace for your engineering organization."}
              </p>
            </div>
            <button
              className="button primary"
              onClick={() =>
                navigate(page === "AI Assistant" ? "Overview" : "AI Assistant")
              }
            >
              <Sparkles size={16} />
              {page === "AI Assistant"
                ? "Back to overview"
                : "Ask AI assistant"}
            </button>
          </div>
          <div className="demo-notice">
            <span>
              <Radio size={14} />
              <strong>Demo workspace</strong>
              <span className="demo-copy">
                You’re exploring sample data. Your GitHub data stays
                disconnected.
              </span>
            </span>
            <button onClick={() => navigate("Integrations")}>
              Connect GitHub <ArrowRight size={14} />
            </button>
          </div>

          {page === "Overview" && (
            <section className="delivery-focus" aria-labelledby="focus-title">
              <div className="focus-intro">
                <span className="focus-kicker">
                  <span className="status-dot" /> SAMPLE REVIEW QUEUE
                </span>
                <h2 id="focus-title">
                  Keep good work <br />
                  moving forward.
                </h2>
                <p>
                  A closer look at the changes waiting for their next review.
                  Explore the sample queue below.
                </p>
                <button
                  className="focus-action"
                  onClick={() => {
                    setState("Awaiting review");
                    navigate("Pull Requests");
                  }}
                >
                  Open review queue <ArrowUpRight size={17} />
                </button>
                <div className="focus-footnote">
                  <GitBranch size={14} /> Repository activity, with context.
                </div>
              </div>
              <div className="focus-queue">
                <div className="focus-queue-heading">
                  <span>
                    <Clock3 size={16} /> Waiting for review
                  </span>
                  <span className="focus-count">{reviewQueue.length}</span>
                </div>
                <p className="queue-caption">
                  Sample snapshot · independent of the chart date range
                </p>
                {reviewQueue.map((pr) => (
                  <button
                    className="focus-row"
                    key={pr.number}
                    onClick={() => {
                      setRepository(pr.repo);
                      setState("Awaiting review");
                      navigate("Pull Requests");
                    }}
                  >
                    <span className="focus-pr-icon">
                      <GitPullRequest size={19} />
                    </span>
                    <span className="focus-row-copy">
                      <strong>{pr.title}</strong>
                      <small>
                        {pr.repo} <span>#{pr.number}</span>
                      </small>
                    </span>
                    <span className="queue-age">
                      {pr.age}
                      <ArrowUpRight size={14} />
                    </span>
                  </button>
                ))}
                {!reviewQueue.length && (
                  <p className="queue-empty">
                    No sample reviews match this view.
                  </p>
                )}
                <div className="queue-footer">
                  <ShieldCheck size={14} /> Sample data. GitHub is not
                  connected.
                </div>
              </div>
            </section>
          )}

          {[
            "Overview",
            "Repositories",
            "Pull Requests",
            "Deployments",
            "CI/CD",
            "Engineering Health",
          ].includes(page) ? (
            <>
              <div className="filterbar">
                <div className="filter-left">
                  <label className="select-control">
                    <FolderGit2 size={15} />
                    <select
                      value={repository}
                      aria-label="Repository"
                      onChange={(e) => setRepository(e.target.value)}
                    >
                      <option value="all">All repositories</option>
                      {repositories.map((r) => (
                        <option key={r.name}>{r.name}</option>
                      ))}
                    </select>
                  </label>
                  <span className="filter-separator" />
                  <span className="snapshot">
                    <span className="status-dot" />
                    Sample snapshot · Aug 31, 2026
                  </span>
                </div>
                <div className="filter-right">
                  <div className="period-control" aria-label="Date range">
                    {[7, 30, 90].map((n) => (
                      <button
                        key={n}
                        className={days === n ? "selected" : ""}
                        aria-pressed={days === n}
                        onClick={() => setDays(n)}
                      >
                        {n} days
                      </button>
                    ))}
                  </div>
                  <button
                    className="button export-button"
                    onClick={exportReport}
                  >
                    <Download size={14} />
                    Export
                  </button>
                </div>
              </div>
              <section
                className="metrics-grid"
                aria-label="Engineering metrics"
              >
                {[
                  {
                    label: "Deployments",
                    value: metrics.deployments.toString(),
                    unit: "",
                    icon: Rocket,
                    note: `${(metrics.deployments / days).toFixed(1)} per day`,
                    green: true,
                    spark: "▂▃▂▄▅▃▅▆▄▇",
                  },
                  {
                    label: "PR cycle time",
                    value: metrics.cycle,
                    unit: "hrs",
                    icon: GitPullRequest,
                    note: "Illustrative repository average",
                    green: false,
                    spark: "▇▆▇▅▆▄▅▃▄▂",
                  },
                  {
                    label: "Time to first review",
                    value: metrics.review,
                    unit: "hrs",
                    icon: Clock3,
                    note: "Illustrative repository average",
                    green: false,
                    spark: "▆▇▅▆▄▅▂▄▃▂",
                  },
                  {
                    label: "CI success rate",
                    value: metrics.success,
                    unit: "%",
                    icon: Workflow,
                    note: `${metrics.workflows.toLocaleString()} workflow runs`,
                    green: true,
                    spark: "▃▄▃▅▄▆▅▇▆▇",
                  },
                ].map(
                  ({ label, value, unit, icon: Icon, note, green, spark }) => (
                    <article className="metric-card" key={label}>
                      <div className="metric-label">
                        {label}
                        <Icon size={17} />
                      </div>
                      <div className="metric-value">
                        {value}
                        <span>{unit}</span>
                        <span className="sparkline" aria-hidden="true">
                          {spark}
                        </span>
                      </div>
                      <div className={`metric-note ${green ? "positive" : ""}`}>
                        {green ? (
                          <ArrowUpRight size={13} />
                        ) : (
                          <ArrowDownLeft size={13} />
                        )}{" "}
                        {note}
                      </div>
                    </article>
                  ),
                )}
              </section>

              {page === "Overview" && (
                <>
                  <div className="charts-grid">
                    <section className="panel">
                      <div className="panel-heading">
                        <div>
                          <h2>Deployment frequency</h2>
                          <p>Releases across your selected repositories</p>
                        </div>
                        <Badge tone="neutral">
                          <span className="status-dot" />
                          Daily
                        </Badge>
                      </div>
                      <div className="chart-summary">
                        <strong>{metrics.deployments}</strong>
                        <span>deployments in {days} days</span>
                        <span className="chart-key">
                          <i />
                          Deployments
                        </span>
                      </div>
                      <TrendChart data={metrics.series} />
                    </section>
                    <section className="panel">
                      <div className="panel-heading">
                        <div>
                          <h2>Pull request activity</h2>
                          <p>From first commit to shipping</p>
                        </div>
                        <GitPullRequest size={18} className="muted" />
                      </div>
                      <div className="chart-summary">
                        <strong>
                          {metrics.series.reduce((s, d) => s + d.merged, 0)}
                        </strong>
                        <span>merged pull requests</span>
                      </div>
                      <ActivityChart data={metrics.series} />
                    </section>
                  </div>
                  <section className="panel repository-panel">
                    <div className="panel-heading">
                      <div className="inline-heading">
                        <h2>Repository health</h2>
                        <span className="count-pill">
                          {visibleRepositories.length}
                        </span>
                      </div>
                      <button
                        className="text-button"
                        onClick={() => navigate("Repositories")}
                      >
                        View repositories <ArrowRight size={14} />
                      </button>
                    </div>
                    {repositoryTable()}
                  </section>
                  <section className="panel">
                    <div className="panel-heading">
                      <div className="inline-heading">
                        <h2>Recent activity</h2>
                        <span className="subtle-label">
                          Latest sample events
                        </span>
                      </div>
                      <button
                        className="text-button"
                        onClick={() => navigate("Deployments")}
                      >
                        View deployments <ArrowRight size={14} />
                      </button>
                    </div>
                    {recentActivity()}
                  </section>
                </>
              )}

              {page === "Repositories" && (
                <>
                  <section className="panel">
                    <div className="panel-heading">
                      <h2>
                        {repository === "all"
                          ? "Your repositories"
                          : repository}
                      </h2>
                      <Badge tone="neutral">Sample data</Badge>
                    </div>
                    {repositoryTable()}
                  </section>
                  {repository !== "all" && (
                    <section className="panel detail-chart">
                      <div className="panel-heading">
                        <h2>Deployment history</h2>
                        <button
                          className="text-button"
                          onClick={() => navigate("Pull Requests")}
                        >
                          Explore pull requests <ArrowRight size={14} />
                        </button>
                      </div>
                      <TrendChart data={metrics.series} />
                    </section>
                  )}
                </>
              )}

              {page === "Pull Requests" && (
                <section className="panel">
                  <div className="panel-heading">
                    <div>
                      <h2>Pull requests</h2>
                      <p>
                        Latest sample records · independent of the aggregate
                        date range
                      </p>
                    </div>
                    <label className="select-control">
                      <select
                        aria-label="PR state"
                        value={state}
                        onChange={(e) => setState(e.target.value)}
                      >
                        <option value="all">All states</option>
                        {["Awaiting review", "In review", "Merged"].map((s) => (
                          <option key={s}>{s}</option>
                        ))}
                      </select>
                    </label>
                  </div>
                  <div className="table-scroll">
                    <table>
                      <thead>
                        <tr>
                          <th>Pull request</th>
                          <th>Author</th>
                          <th>Age</th>
                          <th>Review time</th>
                          <th>State</th>
                        </tr>
                      </thead>
                      <tbody>
                        {prs.map((pr) => (
                          <tr key={pr.number}>
                            <td>
                              <button
                                className="pr-link"
                                onClick={() =>
                                  setDialog(`PR #${pr.number}: ${pr.title}`)
                                }
                              >
                                <strong>{pr.title}</strong>
                                <small>
                                  {pr.repo} · #{pr.number}
                                </small>
                              </button>
                            </td>
                            <td>
                              <span className="author-avatar">
                                {pr.initials}
                              </span>
                              {pr.author}
                            </td>
                            <td>{pr.age}</td>
                            <td>{pr.review}</td>
                            <td>
                              <Badge
                                tone={
                                  pr.state === "Awaiting review"
                                    ? "amber"
                                    : pr.state === "Merged"
                                      ? "purple"
                                      : "green"
                                }
                              >
                                {pr.state}
                              </Badge>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    {!prs.length && (
                      <div className="empty-small">
                        No pull requests match your filters.
                      </div>
                    )}
                  </div>
                </section>
              )}

              {page === "Deployments" && (
                <>
                  <section className="panel detail-chart">
                    <div className="panel-heading">
                      <div>
                        <h2>Release activity</h2>
                        <p>
                          {metrics.deployments - metrics.failedDeployments}{" "}
                          successful · {metrics.failedDeployments} failed ·{" "}
                          {days} days
                        </p>
                      </div>
                      <Badge>
                        {(
                          (1 -
                            metrics.failedDeployments / metrics.deployments) *
                          100
                        ).toFixed(1)}
                        % success
                      </Badge>
                    </div>
                    <TrendChart data={metrics.series} />
                  </section>
                  <section className="panel">
                    <div className="panel-heading">
                      <h2>Recent sample events</h2>
                    </div>
                    {recentActivity()}
                  </section>
                </>
              )}

              {page === "CI/CD" && (
                <section className="panel">
                  <div className="panel-heading">
                    <div>
                      <h2>Pipeline reliability</h2>
                      <p>
                        {metrics.failures} failures across {metrics.workflows}{" "}
                        workflow runs
                      </p>
                    </div>
                    <Workflow size={20} />
                  </div>
                  <div className="reliability-list">
                    {visibleRepositories.map((r) => {
                      const m = summarize(days, r.name);
                      return (
                        <div key={r.name}>
                          <span>
                            <strong>{r.name}</strong>
                            <small>
                              {m.workflows} runs · {m.failures} failures
                            </small>
                          </span>
                          <div className="reliability-track">
                            <i style={{ width: `${m.success}%` }} />
                          </div>
                          <strong>{m.success}%</strong>
                        </div>
                      );
                    })}
                  </div>
                </section>
              )}

              {page === "Engineering Health" && (
                <section className="panel">
                  <div className="panel-heading">
                    <div>
                      <h2>Understand the signals</h2>
                      <p>
                        Workflow indicators, never individual performance
                        scores.
                      </p>
                    </div>
                    <HeartPulse size={20} />
                  </div>
                  <div className="health-explanation">
                    <div>
                      <Badge>CI reliability</Badge>
                      <h3>{metrics.success}% successful runs</h3>
                      <p>
                        Successful runs divided by total runs in the selected
                        sample period. Production metrics will define how
                        cancelled and skipped runs are treated.
                      </p>
                    </div>
                    <div>
                      <Badge tone="amber">Review latency</Badge>
                      <h3>Investigate the waiting queue</h3>
                      <p>
                        Sample repositories with an illustrative cycle time
                        above 7 hours are flagged. This is a demo threshold, not
                        a benchmark or employee rating.
                      </p>
                    </div>
                    <div>
                      <Badge tone="neutral">Data confidence</Badge>
                      <h3>Sample data only</h3>
                      <p>
                        These signals demonstrate the interface. Ingestion
                        coverage, freshness, and metric definitions will
                        accompany live analytics.
                      </p>
                    </div>
                  </div>
                </section>
              )}
            </>
          ) : page === "AI Assistant" ? (
            <section className="assistant-panel">
              <div className="assistant-orbit">
                <Sparkles size={31} />
              </div>
              <Badge tone="neutral">COMING IN THE AI PHASE</Badge>
              <h2>Your data. Better questions.</h2>
              <p>
                Investigate what changed, find bottlenecks, and follow the
                evidence.
                <br />
                The assistant will use permission-checked analytics tools.
              </p>
              <div className="prompt-grid">
                {[
                  "Which repository has the highest CI failure rate?",
                  "Which PRs have waited over 24 hours for review?",
                  "How has deployment frequency changed?",
                  "What changed in payments-api this week?",
                ].map((prompt) => (
                  <button key={prompt} onClick={() => setDialog(prompt)}>
                    <ChartNoAxesCombined size={17} />
                    <span>{prompt}</span>
                    <ArrowUpRight size={16} />
                  </button>
                ))}
              </div>
              <div className="assistant-input">
                <span>
                  Connect real engineering data to start a conversation
                </span>
                <span className="assistant-arrow">
                  <ArrowRight size={18} />
                </span>
              </div>
              <small>
                <ShieldCheck size={13} />
                No LLM connected. No fabricated AI answers.
              </small>
            </section>
          ) : page === "Integrations" ? (
            <section className="panel integration-panel">
              <div className="integration-icon">
                <Github size={32} />
              </div>
              <div>
                <Badge tone="neutral">SOURCE CONTROL</Badge>
                <h2>Connect your GitHub organization</h2>
                <p>
                  Bring repositories, pull requests, workflows, and deployments
                  into one clear view.
                </p>
                <ul>
                  <li>
                    <Check size={15} /> Select the repositories you want to
                    analyze
                  </li>
                  <li>
                    <Check size={15} /> Keep activity up to date with verified
                    webhooks
                  </li>
                  <li>
                    <Check size={15} /> Retain organization-level access
                    controls
                  </li>
                </ul>
                <button
                  className="button primary"
                  onClick={() => setDialog("GitHub connection is coming next")}
                >
                  <Github size={16} />
                  Set up GitHub <ExternalLink size={14} />
                </button>
                <small>
                  Not connected · Authentication and tenant isolation come
                  first.
                </small>
              </div>
            </section>
          ) : (
            <section className="panel empty-state">
              <span className="empty-icon">
                {page === "Team" ? (
                  <Users size={28} />
                ) : page === "Alerts" ? (
                  <Bell size={28} />
                ) : page === "Audit Logs" ? (
                  <ShieldCheck size={28} />
                ) : (
                  <Settings size={28} />
                )}
              </span>
              <Badge tone="neutral">FOUNDATION PREVIEW</Badge>
              <h2>
                {page === "Team"
                  ? "Great engineering starts with a team"
                  : page === "Alerts"
                    ? "Catch the signals that matter"
                    : page === "Audit Logs"
                      ? "A clear record of important changes"
                      : "A workspace that works your way"}
              </h2>
              <p>
                {page === "Team"
                  ? "Organization membership, invitations, and server-enforced roles will arrive in the multi-tenancy phase."
                  : page === "Alerts"
                    ? "Threshold alerts will follow live analytics, with email as the first notification channel."
                    : page === "Audit Logs"
                      ? "Security-sensitive actions will be recorded as authentication and organization management are implemented."
                      : "Organization settings will be available once authenticated workspaces are implemented."}
              </p>
              <button
                className="button"
                onClick={() => setDialog("Development roadmap")}
              >
                <BookOpen size={15} />
                View development roadmap <ArrowRight size={14} />
              </button>
            </section>
          )}
          <footer className="page-footer">
            <span>
              <span className="footer-mark">
                <Code2 size={13} />
              </span>
              Engineering Intelligence Platform
            </span>
            <span>
              Local-first. Built with purpose.
              <span className="footer-version">v0.1 / Foundation</span>
            </span>
          </footer>
        </main>
      </div>
      {toast && (
        <div className="toast" role="status">
          <Check size={16} />
          {toast}
        </div>
      )}
      {dialog && (
        <Dialog title={dialog} onClose={() => setDialog(null)}>
          {dialog === "Development roadmap" ? (
            <ol className="roadmap">
              {[
                "Foundation & design preview — current",
                "Authentication & sessions",
                "Organizations, roles & tenant isolation",
                "GitHub connection & synchronization",
                "Durable event pipeline & workers",
                "Analytics & live dashboards",
                "Controlled AI assistant",
                "Production hardening & AWS adapters",
              ].map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ol>
          ) : dialog === "Your workspace" ? (
            <>
              <p>
                You’re viewing Acme Engineering, an isolated collection of UI
                fixtures. Workspace creation and switching require the upcoming
                authentication and multi-tenancy modules.
              </p>
              <Badge tone="neutral">No real organization connected</Badge>
            </>
          ) : dialog === "You’re all caught up" ? (
            <p>
              No notifications yet. Alerts and notification delivery will become
              available after live analytics.
            </p>
          ) : dialog === "Demo profile" ? (
            <p>
              This is a presentation profile, not an authenticated session. Use
              Sign in to access your real account. Demo roles and sample
              organization data are separate from your account.
            </p>
          ) : dialog === "Built to run locally" ? (
            <p>
              Next.js and FastAPI run alongside PostgreSQL and Redis in Docker
              Compose. Workers, monitoring, and cloud adapters will be
              introduced when their development phases begin. No AWS resources
              are provisioned.
            </p>
          ) : dialog === "GitHub connection is coming next" ? (
            <p>
              GitHub authorization requires secure sessions, an organization,
              and administrator permissions. These foundations will be
              implemented before requesting any GitHub access. No credentials
              are collected in this preview.
            </p>
          ) : dialog.includes("?") ? (
            <p>
              This is a suggested question, not a generated answer. The AI phase
              will retrieve tenant-authorized metrics through controlled tools
              and attach evidence to its response. No provider call has been
              made.
            </p>
          ) : dialog.startsWith("PR #") || dialog.includes(":") ? (
            <p>
              This is a sample record for exploring the interface. Live record
              details, GitHub links, and timestamps will be available after
              synchronization is implemented.
            </p>
          ) : (
            <p>
              Use repository filters, switch date ranges, explore the
              navigation, or export sample analytics. All displayed engineering
              activity is demonstration data. Start with Integrations to see the
              next step toward connecting real data.
            </p>
          )}
          <div className="dialog-actions">
            <button className="button primary" onClick={() => setDialog(null)}>
              Got it <Check size={15} />
            </button>
          </div>
        </Dialog>
      )}
    </div>
  );
}
