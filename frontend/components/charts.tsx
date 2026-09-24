export function TrendChart({
  data,
}: {
  data: { deployments: number; date: string }[];
}) {
  const width = 640,
    height = 165,
    max = Math.max(...data.map((d) => d.deployments), 1) + 4;
  const points = data.map(
    (d, i) =>
      `${(i / Math.max(data.length - 1, 1)) * width},${height - (d.deployments / max) * height}`,
  );
  return (
    <div className="chart-wrap">
      <svg
        viewBox="-32 -10 690 205"
        role="img"
        aria-label={`Deployment trend: ${data.map((d) => `${d.date}: ${d.deployments}`).join(", ")}`}
      >
        <defs>
          <linearGradient id="area" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#139b78" stopOpacity=".18" />
            <stop offset="100%" stopColor="#139b78" stopOpacity="0" />
          </linearGradient>
        </defs>
        {[0, 1, 2, 3].map((i) => (
          <g key={i}>
            <line
              x1="0"
              x2={width}
              y1={i * 55}
              y2={i * 55}
              stroke="#edf0eb"
              strokeDasharray="3 5"
            />
            <text
              x="-12"
              y={i * 55 + 4}
              textAnchor="end"
              fill="#919790"
              fontSize="10"
            >
              {Math.round(max * (1 - i / 3))}
            </text>
          </g>
        ))}
        <path
          d={`M0,${height} L${points.join(" L")} L${width},${height} Z`}
          fill="url(#area)"
        />
        <polyline
          points={points.join(" ")}
          fill="none"
          stroke="#128d6d"
          strokeWidth="2.5"
          strokeLinejoin="round"
        />
        {[0, 0.25, 0.5, 0.75, 1].map((f) => {
          const index = Math.round(f * (data.length - 1));
          return (
            <text
              key={f}
              x={f * width}
              y="192"
              textAnchor={f === 0 ? "start" : f === 1 ? "end" : "middle"}
              fill="#919790"
              fontSize="10"
            >
              {data[index].date.slice(5).replace("-", "/")}
            </text>
          );
        })}
      </svg>
    </div>
  );
}

export function ActivityChart({
  data,
}: {
  data: { opened: number; merged: number; date: string }[];
}) {
  const groups = Array.from({ length: Math.min(data.length, 10) }, (_, i) => {
    const chunk = data.slice(
      Math.floor((i * data.length) / Math.min(data.length, 10)),
      Math.floor(((i + 1) * data.length) / Math.min(data.length, 10)),
    );
    return {
      opened: chunk.reduce((s, d) => s + d.opened, 0),
      merged: chunk.reduce((s, d) => s + d.merged, 0),
      date: chunk[0].date,
    };
  });
  const max = Math.max(...groups.map((d) => d.opened), 1);
  return (
    <div
      className="bar-chart"
      role="img"
      aria-label={`Pull requests by date bucket: ${groups.map((d) => `${d.date}: ${d.opened} opened, ${d.merged} merged`).join("; ")}`}
    >
      <div className="bar-grid">
        {groups.map((d) => (
          <div className="bar-group" key={d.date}>
            <div className="bar-pair">
              <i style={{ height: `${(d.opened / max) * 100}%` }} />
              <i style={{ height: `${(d.merged / max) * 100}%` }} />
            </div>
            <span>{d.date.slice(8)}</span>
          </div>
        ))}
      </div>
      <div className="chart-legend">
        <span>
          <i /> Opened
        </span>
        <span>
          <i /> Merged
        </span>
      </div>
    </div>
  );
}
