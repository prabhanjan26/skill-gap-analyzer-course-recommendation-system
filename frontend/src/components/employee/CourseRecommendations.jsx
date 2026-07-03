import React from "react";
import { BookOpen, Clock, GraduationCap, Info } from "lucide-react";
import { levelLabel } from "../../constants/categories";

function gapText(from, to) {
  if (from === null || from === undefined) return `New skill up to L${to}`;
  return `L${from} to L${to}`;
}

export default function CourseRecommendations({ recommendations, notices }) {
  if (!recommendations || recommendations.length === 0) {
    return (
      <div className="card card-body">
        <div className="empty-state">
          <div className="es-icon">
            <GraduationCap size={40} />
          </div>
          <div className="font-semibold">No course recommendations</div>
          <div className="text-sm mt-2">
            {notices && notices.length
              ? notices[0]
              : "No skill gaps were detected for this role."}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      {recommendations.map((group, gi) => (
        <div key={gi} className="card">
          <div className="card-header">
            <div className="card-title">
              <BookOpen size={16} />
              {group.skill_name}
            </div>
            <span className="badge badge-primary">
              {gapText(group.gap_from, group.gap_to)}
            </span>
          </div>
          <div className="card-body" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {(group.courses || []).length === 0 ? (
              <div className="text-muted text-sm">No courses matched for this gap.</div>
            ) : (
              group.courses.map((c, ci) => <CourseCard key={ci} course={c} />)
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

function CourseCard({ course }) {
  return (
    <div
      style={{
        border: "1px solid var(--border)",
        borderRadius: "var(--radius)",
        padding: "14px 16px",
      }}
    >
      <div className="flex justify-between items-center gap-3">
        <div style={{ minWidth: 0 }}>
          <div className="font-semibold">{course.title}</div>
          <div className="text-xs text-muted mt-2">{course.course_id}</div>
        </div>
        {typeof course.relevance_score === "number" ? (
          <span className="badge badge-success">
            {Math.round(course.relevance_score * 100)}% match
          </span>
        ) : null}
      </div>

      <div className="wrap mt-3">
        <span className="badge badge-neutral">{course.provider}</span>
        <span className="badge badge-primary">{levelLabel4(course.level)}</span>
        {course.duration_hours ? (
          <span className="badge badge-neutral">
            <Clock size={12} /> {course.duration_hours}h
          </span>
        ) : null}
      </div>

      {course.reasoning ? (
        <div className="alert alert-info mt-3" style={{ padding: "9px 12px" }}>
          <Info size={15} />
          <div className="text-sm">{course.reasoning}</div>
        </div>
      ) : null}
    </div>
  );
}

// Accepts either a level label string or numeric.
function levelLabel4(level) {
  if (typeof level === "number") return levelLabel(level);
  return level || "-";
}
