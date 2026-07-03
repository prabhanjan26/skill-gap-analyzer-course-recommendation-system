import React, { useState } from "react";
import {
  BarChart3,
  Layers,
  GraduationCap,
  ListChecks,
  Activity,
  Info,
  RotateCcw,
} from "lucide-react";
import ReadinessScore from "../dashboard/ReadinessScore";
import SkillComparisonTable from "../dashboard/SkillComparisonTable";
import CategoryBreakdown from "../dashboard/CategoryBreakdown";
import CourseRecommendations from "./CourseRecommendations";
import CategoryBadge from "../shared/CategoryBadge";
import { levelLabel } from "../../constants/categories";

const TABS = [
  { key: "comparison", label: "Skill Comparison", icon: BarChart3 },
  { key: "categories", label: "Category Breakdown", icon: Layers },
  { key: "courses", label: "Course Recommendations", icon: GraduationCap },
  { key: "extracted", label: "Extracted Skills", icon: ListChecks },
  { key: "metadata", label: "Pipeline Metadata", icon: Activity },
];

export default function AnalysisResults({ result, onReset }) {
  const [tab, setTab] = useState("comparison");
  const cmp = result.comparison_result;

  const counts = {
    comparison:
      (cmp.matched_skills?.length || 0) +
      (cmp.missing_skills?.length || 0) +
      (cmp.fully_met_skills?.length || 0) +
      (cmp.exceeded_skills?.length || 0),
    categories: Object.keys(cmp.category_breakdown || {}).length,
    courses: result.course_recommendations?.length || 0,
    extracted: result.extracted_skills?.length || 0,
  };

  return (
    <div>
      <div className="page-header-row mb-4">
        <div>
          <h1>Analysis Results</h1>
          <div className="subtitle">
            {result.employee_name ? `${result.employee_name} · ` : ""}
            {result.role_analyzed.role_name}
          </div>
        </div>
        <button className="btn btn-secondary" onClick={onReset}>
          <RotateCcw size={15} /> New analysis
        </button>
      </div>

      {result.notices && result.notices.length ? (
        <div className="alert alert-warning mb-4">
          <Info size={18} />
          <div>
            {result.notices.map((n, i) => (
              <div key={i}>{n}</div>
            ))}
          </div>
        </div>
      ) : null}

      <div className="mb-4">
        <ReadinessScore
          score={result.readiness_score}
          breakdown={result.readiness_breakdown}
        />
      </div>

      <div className="tabs">
        {TABS.map((t) => {
          const Icon = t.icon;
          const count = counts[t.key];
          return (
            <button
              key={t.key}
              className={"tab" + (tab === t.key ? " active" : "")}
              onClick={() => setTab(t.key)}
            >
              <Icon size={15} />
              {t.label}
              {typeof count === "number" ? (
                <span className="tab-count">{count}</span>
              ) : null}
            </button>
          );
        })}
      </div>

      {tab === "comparison" && <SkillComparisonTable comparison={cmp} />}
      {tab === "categories" && (
        <CategoryBreakdown categoryBreakdown={cmp.category_breakdown} />
      )}
      {tab === "courses" && (
        <CourseRecommendations
          recommendations={result.course_recommendations}
          notices={result.notices}
        />
      )}
      {tab === "extracted" && (
        <ExtractedSkills skills={result.extracted_skills} />
      )}
      {tab === "metadata" && <PipelineMetadata meta={result.analysis_metadata} />}
    </div>
  );
}

function ExtractedSkills({ skills }) {
  if (!skills || skills.length === 0) {
    return (
      <div className="card card-body">
        <div className="empty-state">
          <div className="es-icon">
            <ListChecks size={40} />
          </div>
          <div className="font-semibold">No skills extracted</div>
          <div className="text-sm mt-2">
            The resume did not yield any identifiable skills for this role.
          </div>
        </div>
      </div>
    );
  }
  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">Extracted Skills</div>
        <span className="text-sm text-muted">
          Identified by the LLM from the resume
        </span>
      </div>
      <table className="table">
        <thead>
          <tr>
            <th>Skill</th>
            <th style={{ width: 130 }}>Est. Level</th>
            <th style={{ width: 120 }}>Confidence</th>
            <th style={{ width: 190 }}>Category</th>
            <th>Evidence</th>
          </tr>
        </thead>
        <tbody>
          {skills.map((s, i) => (
            <tr key={i}>
              <td className="font-semibold">{s.skill_name}</td>
              <td>
                <span className="level-pill">L{s.estimated_level}</span>
                <span className="text-xs text-secondary" style={{ marginLeft: 6 }}>
                  {levelLabel(s.estimated_level)}
                </span>
              </td>
              <td>
                <ConfidenceBar value={s.confidence} />
              </td>
              <td>
                <CategoryBadge category={s.category} />
              </td>
              <td className="text-sm text-secondary">
                {s.evidence_snippet || "-"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ConfidenceBar({ value }) {
  const pct = Math.round((value || 0) * 100);
  return (
    <div className="flex items-center gap-2">
      <div className="meter" style={{ flex: 1 }}>
        <div className="meter-fill" style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-secondary" style={{ width: 32 }}>
        {pct}%
      </span>
    </div>
  );
}

function PipelineMetadata({ meta }) {
  const items = [
    { label: "Pipeline duration", value: `${meta.pipeline_duration_ms} ms` },
    { label: "LLM calls", value: meta.llm_calls },
    { label: "Chunks generated", value: meta.chunks_generated },
    { label: "Chunks retrieved", value: meta.chunks_retrieved },
    { label: "Courses in catalog", value: meta.courses_in_catalog },
    { label: "Courses retrieved (stage 1)", value: meta.courses_retrieved_stage1 },
    { label: "Courses after re-ranking", value: meta.courses_after_reranking },
    { label: "Timestamp", value: meta.timestamp },
  ];
  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">Pipeline Metadata</div>
      </div>
      <div className="card-body">
        <div className="grid grid-2">
          {items.map((it) => (
            <div
              key={it.label}
              className="flex justify-between"
              style={{
                padding: "10px 0",
                borderBottom: "1px solid var(--border)",
              }}
            >
              <span className="text-secondary text-sm">{it.label}</span>
              <span className="font-semibold text-sm">{it.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
