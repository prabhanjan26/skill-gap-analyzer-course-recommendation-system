import React, { useEffect, useState, useCallback } from "react";
import { Plus, Pencil, Trash2, Eye, Layers, AlertTriangle } from "lucide-react";
import { listRoles, deleteRole } from "../../services/api";
import CategoryBadge from "../shared/CategoryBadge";
import LoadingSpinner from "../shared/LoadingSpinner";

export default function RoleList({ onCreate, onView, onEdit }) {
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deleting, setDeleting] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setRoles(await listRoles());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleDelete = async (slug, name) => {
    if (!window.confirm(`Delete role "${name}"? This cannot be undone.`)) return;
    setDeleting(slug);
    try {
      await deleteRole(slug);
      await load();
    } catch (e) {
      setError(e.message);
    } finally {
      setDeleting(null);
    }
  };

  return (
    <div>
      <div className="page-header-row mb-4">
        <div>
          <h1>Role Definitions</h1>
          <div className="subtitle">
            Manage competency matrices that drive skill gap analysis.
          </div>
        </div>
        <button className="btn btn-primary" onClick={onCreate}>
          <Plus size={16} /> Create role
        </button>
      </div>

      {error ? (
        <div className="alert alert-danger mb-4">
          <AlertTriangle size={18} />
          <div>{error}</div>
        </div>
      ) : null}

      <div className="card">
        {loading ? (
          <LoadingSpinner label="Loading roles..." />
        ) : roles.length === 0 ? (
          <div className="empty-state">
            <div className="es-icon">
              <Layers size={40} />
            </div>
            <div className="font-semibold">No roles defined yet</div>
            <div className="text-sm mt-2">
              Create your first role to begin building competency matrices.
            </div>
            <button className="btn btn-primary mt-4" onClick={onCreate}>
              <Plus size={16} /> Create role
            </button>
          </div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Role</th>
                <th style={{ width: 90 }}>Skills</th>
                <th>Categories</th>
                <th style={{ width: 170 }}>Updated</th>
                <th style={{ width: 150 }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {roles.map((role) => (
                <tr key={role._id}>
                  <td>
                    <div className="font-semibold">{role.role_name}</div>
                    <div className="text-xs text-muted">{role.role_slug}</div>
                  </td>
                  <td>
                    <span className="badge badge-primary">{role.skills_count}</span>
                  </td>
                  <td>
                    <div className="wrap">
                      {(role.categories || []).slice(0, 4).map((c) => (
                        <CategoryBadge key={c} category={c} />
                      ))}
                      {(role.categories || []).length > 4 ? (
                        <span className="badge badge-neutral">
                          +{role.categories.length - 4}
                        </span>
                      ) : null}
                    </div>
                  </td>
                  <td className="text-secondary text-sm">
                    {formatDate(role.updated_at)}
                  </td>
                  <td>
                    <div className="flex gap-2">
                      <button
                        className="btn btn-ghost btn-sm"
                        title="View"
                        onClick={() => onView(role.role_slug)}
                      >
                        <Eye size={15} />
                      </button>
                      <button
                        className="btn btn-ghost btn-sm"
                        title="Edit"
                        onClick={() => onEdit(role.role_slug)}
                      >
                        <Pencil size={15} />
                      </button>
                      <button
                        className="btn btn-danger btn-sm"
                        title="Delete"
                        disabled={deleting === role.role_slug}
                        onClick={() => handleDelete(role.role_slug, role.role_name)}
                      >
                        <Trash2 size={15} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function formatDate(iso) {
  if (!iso) return "-";
  try {
    return new Date(iso).toLocaleString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}
