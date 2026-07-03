import React from "react";
import { useNavigate } from "react-router-dom";
import { Shield, User, ArrowRight, GaugeCircle } from "lucide-react";

export default function HomePage() {
  const navigate = useNavigate();

  return (
    <div className="page">
      <div className="home-hero">
        <div
          className="mode-icon"
          style={{ margin: "0 auto 18px", width: 56, height: 56 }}
        >
          <GaugeCircle size={28} />
        </div>
        <h1>Skill Gap Analyzer &amp; Course Recommender</h1>
        <p>
          Define role competency matrices, assess employee resumes against them,
          and generate personalized learning paths powered by retrieval-augmented
          analysis.
        </p>
      </div>

      <div className="mode-grid">
        <button className="mode-card" onClick={() => navigate("/admin")}>
          <div className="mode-icon">
            <Shield size={24} />
          </div>
          <h3>Administrator</h3>
          <p>
            Create and manage role definitions. Assign required skills, proficiency
            levels, and categories that drive gap analysis.
          </p>
          <span className="mode-cta">
            Manage roles <ArrowRight size={15} />
          </span>
        </button>

        <button className="mode-card" onClick={() => navigate("/employee")}>
          <div className="mode-icon">
            <User size={24} />
          </div>
          <h3>Employee</h3>
          <p>
            Select a target role, upload your resume, and receive a readiness
            score, category breakdown, and recommended courses.
          </p>
          <span className="mode-cta">
            Start analysis <ArrowRight size={15} />
          </span>
        </button>
      </div>
    </div>
  );
}
