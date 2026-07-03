// Shared 12-category taxonomy (mirrors backend/app/constants/categories.py).
// Single source of truth for the frontend.

export const CATEGORIES = [
  { key: "programming_languages", label: "Programming Languages" },
  { key: "frontend", label: "Frontend Development" },
  { key: "backend", label: "Backend Development" },
  { key: "databases", label: "Databases" },
  { key: "devops", label: "DevOps & Infrastructure" },
  { key: "cloud", label: "Cloud Platforms" },
  { key: "architecture", label: "System Architecture" },
  { key: "data_engineering", label: "Data Engineering" },
  { key: "data_science", label: "Data Science & ML" },
  { key: "quality", label: "Quality & Testing" },
  { key: "security", label: "Security" },
  { key: "soft_skills", label: "Soft Skills & Leadership" },
  { key: "mobile", label: "Mobile Development" },
  { key: "ui_ux", label: "UI/UX & Design" },
  { key: "ai_ml", label: "AI & Machine Learning" },
  { key: "networking", label: "Networking & Systems" },
  { key: "blockchain", label: "Blockchain & Web3" },
  { key: "game_development", label: "Game Development" },
  { key: "embedded_iot", label: "Embedded & IoT" },
  { key: "product_management", label: "Product & Project Management" },
];

export const CATEGORY_LABELS = CATEGORIES.reduce((acc, c) => {
  acc[c.key] = c.label;
  return acc;
}, {});

// Slugify free text into a backend-safe custom category key.
export function slugifyCategory(text) {
  return (text || "")
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
}

// Title-case an unknown slug so custom categories display nicely.
function titleCaseSlug(key) {
  return String(key)
    .split("_")
    .filter(Boolean)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

export function categoryLabel(key) {
  if (!key) return "";
  return CATEGORY_LABELS[key] || titleCaseSlug(key);
}

export const PROFICIENCY_LABELS = {
  1: "Beginner",
  2: "Intermediate",
  3: "Advanced",
  4: "Expert",
};

export function levelLabel(n) {
  return PROFICIENCY_LABELS[n] || `L${n}`;
}
