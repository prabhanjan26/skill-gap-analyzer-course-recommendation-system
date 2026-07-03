import React from "react";
import { CheckCircle2, TrendingUp, ArrowDown, XCircle } from "lucide-react";
import CategoryBadge from "../shared/CategoryBadge";

const STATUS_META = {
  below_required: {
    label: "Below required",
    badge: "badge-warning",
    icon: <ArrowDown size={13} />,
  },
  missing: { label: "Missing", badge: "badge-danger", icon: <XCircle size={13} /> },
  fully_met: {
    label: "Fully met",
    badge: "badge-success",
    icon: <CheckCircle2 size={13} />,
  },
  exceeded: {
    label: "Exceeded",
    badge: "badge-primary",
    icon: <TrendingUp size={13} />,
  },
};

function buildRows(cmp) {
  const rows = [];
  (cmp.matched_skills || []).forEach((s) =>
    rows.push({
      status: "below_required",
      skill_name: s.skill_name,
      employee_level: s.employee_level,
      required_level: s.required_level,
      delta: `Gap ${s.gap}`,
      category: s.category,
    })
  );
  (cmp.missing_skills || []).forEach((s) =>
    rows.push({
      status: "missing",
      skill_name: s.skill_name,
      employee_level: null,
      required_level: s.required_level,
      delta: "-",
      category: s.category,
    })
  );
  (cmp.fully_met_skills || []).forEach((s) =>
    rows.push({
      status: "fully_met",
      skill_name: s.skill_name,
      employee_level: s.employee_level,
      required_level: s.required_level,
      delta: "Met",
      category: s.category,
    })
  );
  (cmp.exceeded_skills || []).forEach((s) =>
    rows.push({
      status: "exceeded",
      skill_name: s.skill_name,
      employee_level: s.employee_level,
      required_level: s.required_level,
      delta: `+${s.surplus}`,
      category: s.category,
    })
  );
  return rows;
}

export default function SkillComparisonTable({ comparison }) {
  const rows = buildRows(comparison);
  const additional = comparison.additional_skills || [];

  return (
    <div>
      <div className="card">
        <div className="card-header">
          <div className="card-title">Skill Comparison</div>
          <span className="text-sm text-muted">
            {rows.length} required skills evaluated
          </span>
        </div>
        <table className="table">
          <thead>
            <tr>
              <th>Skill</th>
              <th style={{ width: 150 }}>Status</th>
              <th style={{ width: 110 }}>Your Level</th>
              <th style={{ width: 110 }}>Required</th>
              <th style={{ width: 100 }}>Delta</th>
              <th style={{ width: 200 }}>Category</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => {
              const meta = STATUS_META[r.status];
              return (
                <tr key={i}>
                  <td className="font-semibold">{r.skill_name}</td>
                  <td>
                    <span className={"badge " + meta.badge}>
                      {meta.icon} {meta.label}
                    </span>
                  </td>
                  <td>
                    {r.employee_level ? (
                      <span className="level-pill">L{r.employee_level}</span>
                    ) : (
                      <span className="text-muted">-</span>
                    )}
                  </td>
                  <td>
                    <span className="level-pill">L{r.required_level}</span>
                  </td>
                  <td className="text-sm text-secondary">{r.delta}</td>
                  <td>
                    <CategoryBadge category={r.category} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {additional.length ? (
        <div className="card mt-4">
          <div className="card-header">
            <div className="card-title">Additional Skills</div>
            <span className="text-sm text-muted">
              Detected but not required for this role
            </span>
          </div>
          <div className="card-body">
            <div className="wrap">
              {additional.map((s, i) => (
                <span key={i} className="badge badge-neutral">
                  {s.skill_name} · L{s.estimated_level}
                </span>
              ))}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
