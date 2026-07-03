import React from "react";
import { Plus, Trash2 } from "lucide-react";
import { CATEGORIES, categoryLabel, slugifyCategory } from "../../constants/categories";

const CUSTOM_VALUE = "__custom__";
const CATEGORY_KEYS = new Set(CATEGORIES.map((c) => c.key));

const LEVELS = [
  { value: 1, label: "L1 - Beginner" },
  { value: 2, label: "L2 - Intermediate" },
  { value: 3, label: "L3 - Advanced" },
  { value: 4, label: "L4 - Expert" },
];

const emptySkill = () => ({
  skill_name: "",
  required_level: 3,
  category: "",
});

// Controlled editable table of required skills. `skills` is an array of
// { skill_name, required_level, category }. Category is a required dropdown.
export default function SkillEditor({ skills, onChange }) {
  const update = (index, patch) => {
    const next = skills.map((s, i) => (i === index ? { ...s, ...patch } : s));
    onChange(next);
  };

  const addRow = () => onChange([...skills, emptySkill()]);
  const removeRow = (index) => onChange(skills.filter((_, i) => i !== index));

  return (
    <div>
      <div className="table-flush">
        <table className="table">
          <thead>
            <tr>
              <th style={{ width: "42%" }}>
                Skill Name <span className="text-danger">*</span>
              </th>
              <th style={{ width: "22%" }}>
                Required Level <span className="text-danger">*</span>
              </th>
              <th style={{ width: "30%" }}>
                Category <span className="text-danger">*</span>
              </th>
              <th style={{ width: "6%" }} />
            </tr>
          </thead>
          <tbody>
            {skills.length === 0 ? (
              <tr>
                <td colSpan={4} className="text-muted" style={{ textAlign: "center" }}>
                  No skills yet. Add at least one required skill.
                </td>
              </tr>
            ) : (
              skills.map((skill, i) => (
                <tr key={i}>
                  <td>
                    <input
                      className="input"
                      placeholder="e.g. Python"
                      value={skill.skill_name}
                      maxLength={80}
                      onChange={(e) => update(i, { skill_name: e.target.value })}
                    />
                  </td>
                  <td>
                    <select
                      className="select"
                      value={skill.required_level}
                      onChange={(e) =>
                        update(i, { required_level: Number(e.target.value) })
                      }
                    >
                      {LEVELS.map((l) => (
                        <option key={l.value} value={l.value}>
                          {l.label}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td>
                    <CategoryCell skill={skill} onUpdate={(patch) => update(i, patch)} />
                  </td>
                  <td style={{ textAlign: "center" }}>
                    <button
                      type="button"
                      className="btn btn-ghost btn-sm"
                      title="Remove skill"
                      onClick={() => removeRow(i)}
                    >
                      <Trash2 size={15} />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      <button type="button" className="btn btn-secondary btn-sm mt-3" onClick={addRow}>
        <Plus size={15} /> Add skill
      </button>
    </div>
  );
}

// Category selector with a "Custom category" escape hatch. When custom is
// chosen, a text input appears; its value is slugified into `category` while
// the raw text is kept in a transient `_customText` field (not sent to the API).
function CategoryCell({ skill, onUpdate }) {
  const isCustom =
    Boolean(skill._custom) ||
    (Boolean(skill.category) && !CATEGORY_KEYS.has(skill.category));

  const selectValue = isCustom ? CUSTOM_VALUE : skill.category || "";

  const handleSelect = (value) => {
    if (value === CUSTOM_VALUE) {
      onUpdate({ _custom: true, category: "", _customText: "" });
    } else {
      onUpdate({ _custom: false, category: value, _customText: undefined });
    }
  };

  const customText =
    skill._customText !== undefined
      ? skill._customText
      : skill.category
      ? categoryLabel(skill.category)
      : "";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      <select
        className="select"
        value={selectValue}
        onChange={(e) => handleSelect(e.target.value)}
      >
        <option value="">Select category...</option>
        {CATEGORIES.map((c) => (
          <option key={c.key} value={c.key}>
            {c.label}
          </option>
        ))}
        <option value={CUSTOM_VALUE}>+ Custom category...</option>
      </select>
      {isCustom ? (
        <input
          className="input"
          placeholder="e.g. Machine Vision"
          value={customText}
          onChange={(e) =>
            onUpdate({
              _custom: true,
              _customText: e.target.value,
              category: slugifyCategory(e.target.value),
            })
          }
        />
      ) : null}
    </div>
  );
}

export { emptySkill };
