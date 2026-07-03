import React from "react";

// Controlled role dropdown. `roles` is [{ role_name, role_slug, skills_count }].
export default function RoleSelector({ roles, value, onChange }) {
  return (
    <div className="field" style={{ marginBottom: 0 }}>
      <label className="label">
        Target Role <span className="req">*</span>
      </label>
      <select
        className="select"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        <option value="">Select a role to analyze against...</option>
        {roles.map((r) => (
          <option key={r.role_slug} value={r.role_slug}>
            {r.role_name} ({r.skills_count} skills)
          </option>
        ))}
      </select>
    </div>
  );
}
