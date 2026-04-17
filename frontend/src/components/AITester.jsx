import { useState, useRef } from "react";
import "./AITester.css";

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

function AITester({ user }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const fileInputRef = useRef(null);

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
      setResult(null);
      setError("");
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!selectedFile) {
      setError("Please select a file to test");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/uploads`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      const data = await response.json();

      if (response.ok) {
        setResult(data);
      } else {
        setError(data.message || "Test failed");
      }
    } catch (err) {
      setError("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setSelectedFile(null);
    setResult(null);
    setError("");
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div className="ai-tester">
      <div className="tester-header">
        <h2>AI Code Testing</h2>
        <p>Test your code samples with our AI-powered testing pipeline</p>
      </div>

      <form onSubmit={handleSubmit} className="test-form">
        <div className="form-section">
          <label htmlFor="file-upload" className="file-label">
            Select Code File:
          </label>
          <input
            type="file"
            id="file-upload"
            ref={fileInputRef}
            onChange={handleFileSelect}
            accept=".py,.java,.c,.cpp,.txt"
            className="file-input"
          />
          {selectedFile && (
            <div className="file-info">
              Selected: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(2)} KB)
            </div>
          )}
        </div>

        <div className="form-actions">
          <button type="submit" disabled={loading || !selectedFile} className="test-btn">
            {loading ? "Running Test..." : "Run AI Test"}
          </button>
          <button type="button" onClick={handleClear} className="clear-btn">
            Clear
          </button>
        </div>
      </form>

      {error && (
        <div className="error-message">
          <h3>❌ Error</h3>
          <p>{error}</p>
        </div>
      )}

      {result && (
        <div className="test-result">
          <h3>✅ Test Results</h3>
          <div className="result-grid">
            <div className="result-card">
              <span className="card-label">File</span>
              <span className="card-value">{result.originalName}</span>
            </div>

            <div className="result-card">
              <span className="card-label">Status</span>
              <span className={`result-status ${(result.aiResult || result.result)?.toLowerCase()}`}>
                {result.aiResult || result.result || "UNKNOWN"}
              </span>
            </div>

            {result.message && (
              <div className="result-card full-width">
                <span className="card-label">Message</span>
                <span className="card-value">{result.message}</span>
              </div>
            )}
          </div>

          {result.aiError && (
            <div className="result-alert">
              <strong>⚠️ Error Details:</strong>
              <p>{result.aiError}</p>
            </div>
          )}

          {result.aiOutput && (
            <div className="result-section">
              <h4>Pipeline Output</h4>
              <pre className="output-text">{result.aiOutput}</pre>
            </div>
          )}

          {result.jsonResults && Object.keys(result.jsonResults).length > 0 && (
            <div className="result-section">
              <h4>Detailed Analysis</h4>
              <pre className="json-results">{JSON.stringify(result.jsonResults, null, 2)}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default AITester;