import React, { useRef, useState } from "react";
import { UploadCloud, FileText, X } from "lucide-react";

const ACCEPTED = [".pdf", ".docx", ".doc"];
const MAX_MB = 5;

function isAccepted(name) {
  const lower = name.toLowerCase();
  return ACCEPTED.some((ext) => lower.endsWith(ext));
}

// Controlled resume file picker with drag-and-drop. Calls onError(message) for
// client-side validation failures.
export default function ResumeUpload({ file, onFileSelect, onClear, onError }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);

  const validateAndSelect = (f) => {
    if (!f) return;
    if (!isAccepted(f.name)) {
      onError && onError("Invalid file type. Accepted: PDF, DOCX");
      return;
    }
    if (f.size > MAX_MB * 1024 * 1024) {
      onError && onError(`File exceeds ${MAX_MB}MB limit`);
      return;
    }
    if (f.size === 0) {
      onError && onError("Empty file uploaded");
      return;
    }
    onError && onError(null);
    onFileSelect(f);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    validateAndSelect(e.dataTransfer.files && e.dataTransfer.files[0]);
  };

  return (
    <div className="field" style={{ marginBottom: 0 }}>
      <label className="label">
        Resume <span className="req">*</span>
      </label>

      {file ? (
        <div className="file-chip">
          <span className="fc-icon">
            <FileText size={20} />
          </span>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div className="fc-name truncate">{file.name}</div>
            <div className="fc-size">{(file.size / 1024).toFixed(0)} KB</div>
          </div>
          <button type="button" className="btn btn-ghost btn-sm" onClick={onClear}>
            <X size={15} />
          </button>
        </div>
      ) : (
        <div
          className={"dropzone" + (dragging ? " drag" : "")}
          onClick={() => inputRef.current && inputRef.current.click()}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
        >
          <div className="dz-icon">
            <UploadCloud size={34} />
          </div>
          <div className="dz-title">Click to upload or drag and drop</div>
          <div className="dz-sub">PDF or DOCX, up to {MAX_MB}MB</div>
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.docx,.doc"
            style={{ display: "none" }}
            onChange={(e) => validateAndSelect(e.target.files && e.target.files[0])}
          />
        </div>
      )}
      <div className="hint">
        Your resume is processed transiently and deleted after analysis completes.
      </div>
    </div>
  );
}
