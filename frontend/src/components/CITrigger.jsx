import React, { useEffect, useState } from "react";
import "./CITrigger.css";

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

function CITrigger({ user }) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [runDetails, setRunDetails] = useState(null);
  const [refreshLoading, setRefreshLoading] = useState(false);
  const [deployLoading, setDeployLoading] = useState(false);
  const [deployResult, setDeployResult] = useState(null);

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

  const fetchRunDetails = async () => {
    setRefreshLoading(true);
    setError("");
    try {
      const response = await fetch(`${API_BASE}/pipeline-run-details`);
      const data = await response.json();
      if (response.ok) {
        setRunDetails(data);
      } else {
        setError(data.error || "Unable to fetch workflow details");
      }
    } catch (err) {
      setError("Failed to load workflow details. Try again.");
    } finally {
      setRefreshLoading(false);
    }
  };

  useEffect(() => {
    fetchRunDetails();
  }, []);

  const handleDeploy = async () => {
    setDeployLoading(true);
    setError("");
    setDeployResult(null);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/deploy`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();
      if (response.ok) {
        setDeployResult(data);
        fetchRunDetails();
      } else {
        setError(data.error || "Failed to create deployment commit");
      }
    } catch (err) {
      setError("Network error. Please try again.");
    } finally {
      setDeployLoading(false);
    }
  };

  const workflow = runDetails?.run;
  const canDeploy = workflow?.conclusion === 'success';

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

      {workflow && (
        <div className="summary-card">
          <h3>Latest Workflow Summary</h3>
          <div className="summary-item">
            <span>Status:</span>
            <strong>{workflow.status}</strong>
          </div>
          <div className="summary-item">
            <span>Conclusion:</span>
            <strong>{workflow.conclusion || 'pending'}</strong>
          </div>
          <div className="summary-item">
            <span>Branch:</span>
            <strong>{workflow.headBranch}</strong>
          </div>
          <div className="summary-item">
            <span>Event:</span>
            <strong>{workflow.event}</strong>
          </div>
          {workflow.htmlUrl && (
            <div className="summary-item">
              <span>Workflow URL:</span>
              <a href={workflow.htmlUrl} target="_blank" rel="noopener noreferrer">
                Open GitHub Actions
              </a>
            </div>
          )}
          <button
            type="button"
            className="refresh-btn"
            onClick={fetchRunDetails}
            disabled={refreshLoading}
          >
            {refreshLoading ? 'Refreshing...' : 'Refresh Run Details'}
          </button>
        </div>
      )}

      {error && (
        <div className="error-message">
          <h3>Error</h3>
          <p>{error}</p>
        </div>
      )}

      {result && (
        <div className="trigger-result">
          <h3>CI Trigger Result</h3>
          <div className="result-content">
            <div className="result-item">
              <strong>Message:</strong> {result.message}
            </div>
          </div>
        </div>
      )}

      {canDeploy && (
        <div className="deploy-section">
          <button
            onClick={handleDeploy}
            disabled={deployLoading}
            className="deploy-btn"
          >
            {deployLoading ? "Deploying to Render..." : "Deploy to Render"}
          </button>
          <p className="deploy-note">
            Deployment is available when the latest CI workflow completes successfully.
          </p>
        </div>
      )}

      {deployResult && (
        <div className="deploy-result">
          <h3>Deploy Triggered</h3>
          <p>{deployResult.message}</p>
          {deployResult.deployUrl && (
            <div className="result-item">
              <strong>Render URL:</strong>
              <a href={deployResult.deployUrl} target="_blank" rel="noopener noreferrer">
                {deployResult.deployUrl}
              </a>
            </div>
          )}
          {deployResult.commitUrl && (
            <div className="result-item">
              <strong>Commit URL:</strong>
              <a href={deployResult.commitUrl} target="_blank" rel="noopener noreferrer">
                View Commit
              </a>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default CITrigger;