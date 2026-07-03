import React from "react";
import { categoryLabel } from "../../constants/categories";

function fillClass(score) {
  if (score >= 75) return "success";
  if (score >= 50) return "";
  if (score >= 25) return "warning";
  return "danger";
}

// Horizontal bar chart of per-category readiness scores.
export default function SkillGapChart({ categoryBreakdown }) {
  const entries = Object.entries(categoryBreakdown || {}).sort(
    (a, b) => a[1].score - b[1].score
  );

  if (entries.length === 0) {
    return <div className="text-muted text-sm">No category data available.</div>;
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {entries.map(([key, data]) => (
        <div key={key}>
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-semibold">{categoryLabel(key)}</span>
            <span className="text-sm text-secondary">{data.score}%</span>
          </div>
          <div className="meter">
            <div
              className={"meter-fill " + fillClass(data.score)}
              style={{ width: `${Math.max(2, data.score)}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
