import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import "./PipelineActionsView.css";

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

function JobStatusIcon({ status, conclusion }) {
  if (status === "queued" || status === "waiting") {
    return (
      <span className="pa-job-icon" title="Queued">
        <span className="pa-dot" />
      </span>
    );
  }
  if (status === "in_progress") {
    return (
      <span className="pa-job-icon" title="In progress">
        <span className="pa-dot pa-dot--running" />
      </span>
    );
  }
  if (status === "completed") {
    if (conclusion === "success") {
      return (
        <span className="pa-job-icon" title="Success">
          <span className="pa-check">✓</span>
        </span>
      );
    }
    if (conclusion === "failure" || conclusion === "timed_out") {
      return (
        <span className="pa-job-icon" title="Failed">
          <span className="pa-x">✕</span>
        </span>
      );
    }
    return (
      <span className="pa-job-icon" title={conclusion || "Completed"}>
        <span className="pa-dot" />
      </span>
    );
  }
  return (
    <span className="pa-job-icon">
      <span className="pa-spinner" />
    </span>
  );
}

function runBadgeClass(run) {
  if (!run) return "";
  const base = "pa-run-badge";
  if (run.status === "completed") {
    const c = (run.conclusion || "neutral").replace(/ /g, "_");
    return `${base} pa-run-badge--completed pa-conclusion--${c}`;
  }
  return `${base} pa-run-badge--${run.status.replace(/ /g, "_")}`;
}

export default function PipelineActionsView() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const res = await fetch(`${API_BASE}/pipeline-run-details`);
        const json = await res.json();
        if (cancelled) return;
        if (!res.ok) {
          setError(json.error || "Failed to load");
          return;
        }
        setError(null);
        setData(json);
      } catch (e) {
        if (!cancelled) setError(e.message || "Offline");
      }
    };

    load();
    const id = setInterval(load, 3500);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  if (error && !data) {
    return (
      <div className="pa-root">
        <div className="pa-offline">Could not load workflow: {error}</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="pa-root">
        <div className="pa-empty">Loading workflow…</div>
      </div>
    );
  }

  if (!data.configured) {
    return (
      <div className="pa-root">
        <div className="pa-empty">
          Connect GitHub (repo + token) to see Actions-style job status here.
        </div>
      </div>
    );
  }

  if (!data.run) {
    return (
      <div className="pa-root">
        <div className="pa-empty">{data.message || "No runs yet. Trigger a workflow."}</div>
      </div>
    );
  }

  const { run, jobs, workflowComplete } = data;
  const showFollowUp = workflowComplete;

  return (
    <div className="pa-root">
      <div className="pa-header">
        <div>
          <h3 className="pa-title">{run.displayTitle || run.name}</h3>
          <p className="pa-meta">
            Workflow · {run.name}
            {run.headBranch ? ` · ${run.headBranch}` : ""}
            {run.createdAt ? ` · ${new Date(run.createdAt).toLocaleString()}` : ""}
          </p>
        </div>
        <span className={runBadgeClass(run)} title={run.status}>
          {run.status === "in_progress"
            ? "In progress"
            : run.status === "queued"
              ? "Queued"
              : run.status === "completed"
                ? run.conclusion || "Completed"
                : run.status}
        </span>
      </div>

      <div className="pa-jobs-head">Jobs</div>

      {jobs.length === 0 ? (
        <div className="pa-empty">
          {run.status === "queued" || run.status === "in_progress"
            ? "Waiting for jobs to appear…"
            : "No job records for this run."}
        </div>
      ) : (
        jobs.map((job) => (
          <a
            key={job.id}
            className="pa-job-row"
            href={job.htmlUrl}
            target="_blank"
            rel="noreferrer"
          >
            <JobStatusIcon status={job.status} conclusion={job.conclusion} />
            <span className="pa-job-name">{job.name}</span>
            <span className="pa-job-state">
              {job.status === "completed" && job.conclusion
                ? job.conclusion.replace(/_/g, " ")
                : job.status.replace(/_/g, " ")}
            </span>
          </a>
        ))
      )}

      {showFollowUp ? (
        <div className="pa-follow-up">
          <Link to="/follow-up">Open follow-up form →</Link>
          <p className="pa-external">
            View full run on{" "}
            <a href={run.htmlUrl} target="_blank" rel="noreferrer">
              GitHub
            </a>
          </p>
        </div>
      ) : (
        <p className="pa-external" style={{ padding: "12px 16px", margin: 0 }}>
          <a href={run.htmlUrl} target="_blank" rel="noreferrer">
            View run on GitHub
          </a>
        </p>
      )}
    </div>
  );
}
