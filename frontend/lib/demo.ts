// Deterministic fixtures for the explicitly labeled demo workspace. Never API data.
export const repositories = [
  {
    name: "payments-api",
    language: "Python",
    color: "#d6af52",
    description: "Payment processing & billing",
    cycle: 5.4,
    review: 1.8,
  },
  {
    name: "web-platform",
    language: "TypeScript",
    color: "#629cdf",
    description: "Customer-facing web experience",
    cycle: 7.1,
    review: 3.2,
  },
  {
    name: "auth-service",
    language: "Go",
    color: "#61bac0",
    description: "Identity & access management",
    cycle: 3.2,
    review: 1.1,
  },
  {
    name: "data-pipeline",
    language: "Python",
    color: "#d6af52",
    description: "Event ingestion & processing",
    cycle: 8.6,
    review: 3.5,
  },
];

export const daily = Array.from({ length: 90 }, (_, day) => ({
  date: new Date(Date.UTC(2026, 5, 3 + day)).toISOString().slice(0, 10),
  repositories: repositories.map((repo, index) => ({
    name: repo.name,
    deployments: ((day * 7 + index * 3) % 5) + 1,
    failedDeployments: (day + index * 7) % 19 === 0 ? 1 : 0,
    opened: ((day * 3 + index) % 7) + 1,
    merged: ((day * 3 + index) % 5) + 1,
    workflows: 12 + ((day + index) % 9),
    failures: (day + index * 2) % 4 === 0 ? 2 : 0,
  })),
}));

export const pullRequests = [
  {
    number: 284,
    title: "Add idempotency keys to payment requests",
    repo: "payments-api",
    author: "Alex Morgan",
    initials: "AM",
    state: "Awaiting review",
    age: "26h",
    review: "—",
  },
  {
    number: 192,
    title: "Improve dashboard loading performance",
    repo: "web-platform",
    author: "Jamie Chen",
    initials: "JC",
    state: "In review",
    age: "8h",
    review: "2.1h",
  },
  {
    number: 87,
    title: "Rotate session signing keys",
    repo: "auth-service",
    author: "Sam Rivera",
    initials: "SR",
    state: "Merged",
    age: "3h",
    review: "0.8h",
  },
  {
    number: 146,
    title: "Handle retries for delayed events",
    repo: "data-pipeline",
    author: "Taylor Kim",
    initials: "TK",
    state: "Awaiting review",
    age: "31h",
    review: "—",
  },
  {
    number: 283,
    title: "Fix currency rounding in refunds",
    repo: "payments-api",
    author: "Jamie Chen",
    initials: "JC",
    state: "Merged",
    age: "5h",
    review: "1.2h",
  },
];

export const activity = [
  {
    kind: "deploy",
    title: "Successfully deployed to production",
    repo: "payments-api",
    detail: "main · a3f82b1",
    time: "12 min ago",
    status: "Success",
  },
  {
    kind: "merge",
    title: "Rotate session signing keys",
    repo: "auth-service",
    detail: "PR #87 · Sam Rivera",
    time: "38 min ago",
    status: "Merged",
  },
  {
    kind: "fail",
    title: "Integration tests need attention",
    repo: "web-platform",
    detail: "CI pipeline · Run #1208",
    time: "54 min ago",
    status: "Failed",
  },
  {
    kind: "deploy",
    title: "Successfully deployed to staging",
    repo: "data-pipeline",
    detail: "main · e81c42a",
    time: "1 hour ago",
    status: "Success",
  },
];

export function summarize(days: number, repository: string) {
  const rows = daily.slice(-days);
  const series = rows.map((day) => {
    const data = day.repositories.filter(
      (repo) => repository === "all" || repo.name === repository,
    );
    return {
      date: day.date,
      deployments: data.reduce((sum, r) => sum + r.deployments, 0),
      opened: data.reduce((sum, r) => sum + r.opened, 0),
      merged: data.reduce((sum, r) => sum + r.merged, 0),
      workflows: data.reduce((sum, r) => sum + r.workflows, 0),
      failures: data.reduce((sum, r) => sum + r.failures, 0),
      failedDeployments: data.reduce((sum, r) => sum + r.failedDeployments, 0),
    };
  });
  const selected = repositories.filter(
    (repo) => repository === "all" || repo.name === repository,
  );
  const workflows = series.reduce((sum, d) => sum + d.workflows, 0);
  const failures = series.reduce((sum, d) => sum + d.failures, 0);
  return {
    series,
    workflows,
    failures,
    deployments: series.reduce((sum, d) => sum + d.deployments, 0),
    failedDeployments: series.reduce((sum, d) => sum + d.failedDeployments, 0),
    cycle: (
      selected.reduce((sum, r) => sum + r.cycle, 0) / selected.length
    ).toFixed(1),
    review: (
      selected.reduce((sum, r) => sum + r.review, 0) / selected.length
    ).toFixed(1),
    success: (((workflows - failures) / workflows) * 100).toFixed(1),
  };
}
