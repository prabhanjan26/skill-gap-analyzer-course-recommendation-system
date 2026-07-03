import React from "react";
import { categoryLabel } from "../../constants/categories";

// Neutral, professional category chip. No color-coding by category (keeps the
// palette calm); the label carries the meaning.
export default function CategoryBadge({ category }) {
  if (!category) return null;
  return (
    <span className="badge badge-neutral category-badge">
      {categoryLabel(category)}
    </span>
  );
}
