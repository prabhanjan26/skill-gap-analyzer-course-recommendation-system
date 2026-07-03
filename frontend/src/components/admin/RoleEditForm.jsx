import React, { useEffect, useState } from "react";
import { ArrowLeft, Save, AlertTriangle } from "lucide-react";
import SkillEditor from "./SkillEditor";
import { getRole, updateRole } from "../../services/api";
import LoadingSpinner from "../shared/LoadingSpinner";

// Edit-role form (DDD 11.2). Pre-populates from the existing role document.
export default function RoleEditForm({ slug, onSaved, onCancel }) {
  const [loading, setLoading] = useState(true);
  const [roleName, setRoleName] = useState("");
  const [description, setDescription] = useState("");
  const [skills, setSkills] = useState([]);
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState([]);
  const [loadError, setLoadError] = useState(null);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const role = await getRole(slug);
        if (!active) return;
        setRoleName(role.role_name || "");
        setDescription(role.description || "");
        setSkills(
          (role.skills || []).map((s) => ({
            skill_name: s.skill_name,
            required_level: s.required_level,
            category: s.category,
          }))
        );
      } catch (e) {
        if (active) setLoadError(e.message);
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [slug]);

  const validate = () => {
    const errs = [];
    if (!roleName.trim()) errs.push("Role name is required.");
    const valid = skills.filter((s) => s.skill_name.trim());
    if (valid.length === 0) errs.push("At least one skill is required.");
    valid.forEach((s) => {
      if (!s.category) errs.push(`Category is required for "${s.skill_name}".`);
    });
    return errs;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = validate();
    if (errs.length) {
      setErrors(errs);
      return;
    }
    setErrors([]);
    setSaving(true);
    try {
      const payload = {
        role_name: roleName.trim(),
        description: description.trim(),
        skills: skills
          .filter((s) => s.skill_name.trim())
          .map((s) => ({
            skill_name: s.skill_name.trim(),
            required_level: Number(s.required_level),
            category: s.category,
          })),
      };
      const role = await updateRole(slug, payload);
      onSaved(role, "Role updated successfully.");
    } catch (e2) {
      setErrors(e2.errors && e2.errors.length ? e2.errors : [e2.message]);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="card card-body">
        <LoadingSpinner label="Loading role..." />
      </div>
    );
  }

  if (loadError) {
    return (
      <div>
        <button className="btn btn-ghost btn-sm mb-4" onClick={onCancel}>
          <ArrowLeft size={16} /> Back
        </button>
        <div className="alert alert-danger">
          <AlertTriangle size={18} />
          <div>{loadError}</div>
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit}>
      <div className="page-header-row mb-4">
        <div className="flex items-center gap-3">
          <button type="button" className="btn btn-ghost btn-sm" onClick={onCancel}>
            <ArrowLeft size={16} />
          </button>
          <div>
            <h1>Edit Role</h1>
            <div className="subtitle">
              Update skills, levels, and categories. Changing the name regenerates the slug.
            </div>
          </div>
        </div>
      </div>

      {errors.length ? (
        <div className="alert alert-danger mb-4">
          <AlertTriangle size={18} />
          <div>
            {errors.map((e, i) => (
              <div key={i}>{e}</div>
            ))}
          </div>
        </div>
      ) : null}

      <div className="card card-body mb-4">
        <div className="grid grid-2">
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label">
              Role Name <span className="req">*</span>
            </label>
            <input
              className="input"
              maxLength={100}
              value={roleName}
              onChange={(e) => setRoleName(e.target.value)}
            />
          </div>
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label">Description</label>
            <input
              className="input"
              maxLength={500}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
        </div>
      </div>

      <div className="card mb-4">
        <div className="card-header">
          <div className="card-title">Required Skills</div>
        </div>
        <div className="card-body">
          <SkillEditor skills={skills} onChange={setSkills} />
        </div>
      </div>

      <div className="flex gap-3">
        <button type="submit" className="btn btn-primary" disabled={saving}>
          {saving ? <span className="spinner" /> : <Save size={16} />}
          {saving ? "Saving..." : "Save changes"}
        </button>
        <button type="button" className="btn btn-secondary" onClick={onCancel} disabled={saving}>
          Cancel
        </button>
      </div>
    </form>
  );
}
