import React from "react";

export default function LoadingSpinner({ size = "sm", label }) {
  return (
    <div className="center-col" style={{ padding: label ? "32px 0" : 0 }}>
      <span className={"spinner" + (size === "lg" ? " lg" : "")} />
      {label ? <span className="text-secondary text-sm">{label}</span> : null}
    </div>
  );
}
