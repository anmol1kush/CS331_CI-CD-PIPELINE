import { useState } from "react";
import "./CITrigger.css";

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

function CITrigger({ user }) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const handleTriggerCI = async () => {
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/trigger-ci`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          employeeId: user.employeeId
        })
      });

      const data = await response.json();

      if (response.ok) {
        setResult(data);
      } else {
        setError(data.message || "Failed to trigger CI pipeline");
      }
    } catch (err) {
      setError("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ci-trigger">
      <div className="trigger-header">
        <h2>CI/CD Pipeline Trigger</h2>
        <p>Trigger automated CI/CD workflows for your project</p>
      </div>

      <div className="trigger-section">
        <div className="trigger-info">
          <h3>Pipeline Information</h3>
          <div className="info-item">
            <strong>Employee ID:</strong> {user.employeeId}
          </div>
          <div className="info-item">
            <strong>Workflow:</strong> GitHub Actions CI/CD Pipeline
          </div>
          <div className="info-item">
            <strong>Repository:</strong> CS331_CI-CD-PIPELINE
          </div>
        </div>

        <div className="trigger-actions">
          <button
            onClick={handleTriggerCI}
            disabled={loading}
            className="trigger-btn"
          >
            {loading ? "Triggering Pipeline..." : "Trigger CI Pipeline"}
          </button>
        </div>
      </div>

      {error && (
        <div className="error-message">
          <h3>Error</h3>
          <p>{error}</p>
        </div>
      )}

      {result && (
        <div className="trigger-result">
          <h3>Pipeline Triggered Successfully</h3>
          <div className="result-content">
            <div className="result-item">
              <strong>Status:</strong> {result.status}
            </div>
            <div className="result-item">
              <strong>Message:</strong> {result.message}
            </div>
            {result.workflowUrl && (
              <div className="result-item">
                <strong>Workflow URL:</strong>
                <a href={result.workflowUrl} target="_blank" rel="noopener noreferrer">
                  View Workflow
                </a>
              </div>
            )}
            {result.runId && (
              <div className="result-item">
                <strong>Run ID:</strong> {result.runId}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default CITrigger;