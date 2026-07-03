import React from "react";
import { categoryLabel } from "../../constants/categories";
import SkillGapChart from "../employee/SkillGapChart";

function scoreTone(score) {
  if (score >= 75) return "badge-success";
  if (score >= 50) return "badge-warning";
  return "badge-danger";
}

export default function CategoryBreakdown({ categoryBreakdown }) {
  const entries = Object.entries(categoryBreakdown || {});

  if (entries.length === 0) {
    return (
      <div className="card card-body">
        <div className="text-muted">No category breakdown available.</div>
      </div>
    );
  }

  return (
    <div>
      <div className="card mb-4">
        <div className="card-header">
          <div className="card-title">Readiness by Category</div>
        </div>
        <div className="card-body">
          <SkillGapChart categoryBreakdown={categoryBreakdown} />
        </div>
      </div>

      <div className="grid grid-3">
        {entries.map(([key, data]) => (
          <div key={key} className="card card-pad">
            <div className="flex justify-between items-center mb-2">
              <h3 style={{ fontSize: 14 }}>{categoryLabel(key)}</h3>
              <span className={"badge " + scoreTone(data.score)}>{data.score}%</span>
            </div>
            <div className="divider" style={{ margin: "12px 0" }} />
            <div className="flex justify-between text-sm">
              <span className="text-secondary">Skills</span>
              <span className="font-semibold">{data.total}</span>
            </div>
            <div className="flex justify-between text-sm mt-2">
              <span className="text-secondary">Met</span>
              <span className="font-semibold text-success">{data.met}</span>
            </div>
            <div className="flex justify-between text-sm mt-2">
              <span className="text-secondary">Below required</span>
              <span className="font-semibold text-warning">{data.gaps}</span>
            </div>
            <div className="flex justify-between text-sm mt-2">
              <span className="text-secondary">Missing</span>
              <span className="font-semibold text-danger">{data.missing}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
