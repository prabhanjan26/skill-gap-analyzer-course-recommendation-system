import React from "react";
import { CheckCircle2, AlertCircle, XCircle, Layers } from "lucide-react";

function scoreClass(score) {
  if (score >= 75) return { color: "var(--success)", label: "Strong match" };
  if (score >= 50) return { color: "var(--warning)", label: "Partial match" };
  return { color: "var(--danger)", label: "Significant gaps" };
}

export default function ReadinessScore({ score, breakdown }) {
  const radius = 58;
  const circumference = 2 * Math.PI * radius;
  const pct = Math.max(0, Math.min(100, score));
  const offset = circumference - (pct / 100) * circumference;
  const { color, label } = scoreClass(score);

  return (
    <div className="card card-body">
      <div className="readiness">
        <div className="ring">
          <svg width="132" height="132">
            <circle
              cx="66"
              cy="66"
              r={radius}
              fill="none"
              stroke="var(--border)"
              strokeWidth="10"
            />
            <circle
              cx="66"
              cy="66"
              r={radius}
              fill="none"
              stroke={color}
              strokeWidth="10"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={offset}
            />
          </svg>
          <div className="ring-label">
            <span className="ring-value" style={{ color }}>
              {score}
            </span>
            <span className="ring-unit">/ 100</span>
          </div>
        </div>

        <div style={{ flex: 1 }}>
          <div className="flex items-center gap-2 mb-2">
            <h2>Role Readiness</h2>
            <span
              className="badge"
              style={{
                background: "transparent",
                color,
                borderColor: "currentColor",
              }}
            >
              {label}
            </span>
          </div>
          <div className="stat-row">
            <BreakdownTile
              icon={<Layers size={16} />}
              value={breakdown.total_required_skills}
              label="Required skills"
              tone="neutral"
            />
            <BreakdownTile
              icon={<CheckCircle2 size={16} />}
              value={breakdown.fully_met}
              label="Fully met"
              tone="success"
            />
            <BreakdownTile
              icon={<AlertCircle size={16} />}
              value={breakdown.partially_met}
              label="Below required"
              tone="warning"
            />
            <BreakdownTile
              icon={<XCircle size={16} />}
              value={breakdown.missing}
              label="Missing"
              tone="danger"
            />
          </div>
        </div>
      </div>
    </div>
  );
}

function BreakdownTile({ icon, value, label, tone }) {
  const toneColor = {
    neutral: "var(--text-secondary)",
    success: "var(--success)",
    warning: "var(--warning)",
    danger: "var(--danger)",
  }[tone];
  return (
    <div className="stat">
      <div className="flex items-center gap-2" style={{ color: toneColor }}>
        {icon}
        <span className="stat-value" style={{ color: "var(--text)" }}>
          {value}
        </span>
      </div>
      <div className="stat-label">{label}</div>
    </div>
  );
}
