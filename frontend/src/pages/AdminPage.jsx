import React, { useEffect, useState } from "react";
import { ArrowLeft, Pencil, CheckCircle2, X, AlertTriangle } from "lucide-react";
import RoleList from "../components/admin/RoleList";
import RoleManager from "../components/admin/RoleManager";
import RoleEditForm from "../components/admin/RoleEditForm";
import CategoryBadge from "../components/shared/CategoryBadge";
import LoadingSpinner from "../components/shared/LoadingSpinner";
import { getRole } from "../services/api";
import { levelLabel } from "../constants/categories";

// View state machine: list | create | edit | detail
export default function AdminPage() {
  const [view, setView] = useState("list");
  const [slug, setSlug] = useState(null);
  const [toast, setToast] = useState(null);

  const showToast = (message) => {
    setToast(message);
    window.setTimeout(() => setToast(null), 4000);
  };

  const goList = () => {
    setView("list");
    setSlug(null);
  };

  return (
    <div className="page">
      {toast ? (
        <div className="alert alert-success mb-4">
          <CheckCircle2 size={18} />
          <div className="spacer">{toast}</div>
          <button className="btn btn-ghost btn-sm" onClick={() => setToast(null)}>
            <X size={14} />
          </button>
        </div>
      ) : null}

      {view === "list" && (
        <RoleList
          onCreate={() => setView("create")}
          onView={(s) => {
            setSlug(s);
            setView("detail");
          }}
          onEdit={(s) => {
            setSlug(s);
            setView("edit");
          }}
        />
      )}

      {view === "create" && (
        <RoleManager
          onSaved={(_role, msg) => {
            showToast(msg);
            goList();
          }}
          onCancel={goList}
        />
      )}

      {view === "edit" && (
        <RoleEditForm
          slug={slug}
          onSaved={(_role, msg) => {
            showToast(msg);
            goList();
          }}
          onCancel={goList}
        />
      )}

      {view === "detail" && (
        <RoleDetail
          slug={slug}
          onBack={goList}
          onEdit={() => setView("edit")}
        />
      )}
    </div>
  );
}

function RoleDetail({ slug, onBack, onEdit }) {
  const [role, setRole] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const data = await getRole(slug);
        if (active) setRole(data);
      } catch (e) {
        if (active) setError(e.message);
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [slug]);

  if (loading) {
    return (
      <div className="card card-body">
        <LoadingSpinner label="Loading role..." />
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <button className="btn btn-ghost btn-sm mb-4" onClick={onBack}>
          <ArrowLeft size={16} /> Back
        </button>
        <div className="alert alert-danger">
          <AlertTriangle size={18} />
          <div>{error}</div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header-row mb-4">
        <div className="flex items-center gap-3">
          <button className="btn btn-ghost btn-sm" onClick={onBack}>
            <ArrowLeft size={16} />
          </button>
          <div>
            <h1>{role.role_name}</h1>
            <div className="subtitle">
              {role.description || "No description provided."}
            </div>
          </div>
        </div>
        <button className="btn btn-primary" onClick={onEdit}>
          <Pencil size={16} /> Edit role
        </button>
      </div>

      <div className="card">
        <div className="card-header">
          <div className="card-title">
            Required Skills
            <span className="badge badge-primary">{role.skills.length}</span>
          </div>
        </div>
        <table className="table">
          <thead>
            <tr>
              <th>Skill</th>
              <th style={{ width: 160 }}>Required Level</th>
              <th style={{ width: 240 }}>Category</th>
            </tr>
          </thead>
          <tbody>
            {role.skills.map((s, i) => (
              <tr key={i}>
                <td className="font-semibold">{s.skill_name}</td>
                <td>
                  <span className="level-pill">L{s.required_level}</span>
                  <span className="text-secondary text-sm" style={{ marginLeft: 8 }}>
                    {levelLabel(s.required_level)}
                  </span>
                </td>
                <td>
                  <CategoryBadge category={s.category} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
