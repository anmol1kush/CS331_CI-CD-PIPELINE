import React, { useEffect, useState } from "react";
import PipelineActionsView from "./PipelineActionsView";

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

export default function CICDDashboard() {
  const [status, setStatus] = useState("unknown");
  const [message, setMessage] = useState("");
  const [purpose, setPurpose] = useState("testing");
  const [file, setFile] = useState(null);
  const [uploads, setUploads] = useState([]);

  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/pipeline-status`);
      const data = await res.json();
      if (!res.ok) {
        setStatus("Error");
        return;
      }
      if (data.message === "GitHub not configured" || data.message === "No workflow runs yet") {
        setStatus(data.message === "GitHub not configured" ? "Idle (configure GitHub)" : "Idle");
        return;
      }
      if (data.status === "in_progress" || data.status === "queued") setStatus("Running");
      else if (data.conclusion === "success") setStatus("Success");
      else if (data.conclusion === "failure" || data.conclusion === "cancelled")
        setStatus(data.conclusion === "cancelled" ? "Cancelled" : "Failed");
      else setStatus("Idle");
    } catch {
      setStatus("Offline");
    }
  };

  const loadUploads = async () => {
    try {
      const res = await fetch(`${API_BASE}/uploads`);
      if (!res.ok) return;
      const data = await res.json();
      setUploads(Array.isArray(data) ? data : []);
    } catch {
      setUploads([]);
    }
  };

  const startPipeline = async () => {
    setMessage("");
    try {
      const res = await fetch(`${API_BASE}/run-pipeline`, { method: "POST" });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setMessage(data.error || "Start failed");
        return;
      }
      setMessage(data.message || "Triggered");
      fetchStatus();
    } catch (e) {
      setMessage(e.message || "Start failed");
    }
  };

  const stopPipeline = async () => {
    setMessage("");
    try {
      const res = await fetch(`${API_BASE}/stop-pipeline`, { method: "POST" });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setMessage(data.error || data.message || "Stop failed");
        return;
      }
      setMessage(data.message || "Stopped");
      fetchStatus();
    } catch (e) {
      setMessage(e.message || "Stop failed");
    }
  };

  const submitUpload = async (e) => {
    e.preventDefault();
    setMessage("");
    if (!file) {
      setMessage("Choose a file first");
      return;
    }
    const fd = new FormData();
    fd.append("file", file);
    fd.append("purpose", purpose);
    try {
      const res = await fetch(`${API_BASE}/uploads`, { method: "POST", body: fd });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setMessage(data.error || "Upload failed");
        return;
      }
      setMessage(`Stored: ${data.originalName}`);
      setFile(null);
      e.currentTarget.reset();
      loadUploads();
    } catch (err) {
      setMessage(err.message || "Upload failed");
    }
  };

  useEffect(() => {
    fetchStatus();
    loadUploads();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div
      style={{
        padding: "40px",
        fontFamily: "system-ui, sans-serif",
        maxWidth: "900px",
        margin: "0 auto",
      }}
    >
      <h2 style={{ marginTop: 0 }}>CI/CD Dashboard</h2>

      <PipelineActionsView />

      <h3 style={{ fontSize: "15px", color: "#57606a" }}>Summary: {status}</h3>

      <div style={{ marginBottom: "16px" }}>
        <button type="button" onClick={startPipeline} style={{ marginRight: "10px" }}>
          Run pipeline
        </button>
        <button type="button" onClick={stopPipeline}>
          Stop pipeline
        </button>
      </div>

      {message ? (
        <p style={{ color: "#333", marginBottom: "16px" }} role="status">
          {message}
        </p>
      ) : null}

      <hr style={{ margin: "24px 0" }} />

      <h3>Test / deployment files (stored in MongoDB)</h3>
      <form onSubmit={submitUpload} style={{ marginBottom: "20px" }}>
        <div style={{ marginBottom: "8px" }}>
          <label htmlFor="purpose">Purpose: </label>
          <select
            id="purpose"
            value={purpose}
            onChange={(e) => setPurpose(e.target.value)}
          >
            <option value="testing">Testing</option>
            <option value="deployment">Deployment</option>
          </select>
        </div>
        <div style={{ marginBottom: "8px" }}>
          <input
            type="file"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
        </div>
        <button type="submit">Upload & store</button>
      </form>

      <h4>Recent uploads</h4>
      <ul style={{ paddingLeft: "20px" }}>
        {uploads.length === 0 ? (
          <li style={{ color: "#666" }}>No files stored yet</li>
        ) : (
          uploads.map((u) => (
            <li key={u._id}>
              {u.originalName} — {u.purpose} — {u.size} bytes —{" "}
              {u.uploadedAt ? new Date(u.uploadedAt).toLocaleString() : ""}
            </li>
          ))
        )}
      </ul>
    </div>
  );
}
