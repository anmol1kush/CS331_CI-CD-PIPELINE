import React, { useEffect, useState } from "react";

export default function CICDDashboard() {

  const [status, setStatus] = useState("unknown");

  const fetchStatus = async () => {
    const res = await fetch("http://localhost:3000/pipeline-status");
    const data = await res.json();

    if (data.status === "in_progress") setStatus("Running");
    else if (data.conclusion === "success") setStatus("Success");
    else if (data.conclusion === "failure") setStatus("Failed");
    else setStatus("Idle");
  };

  const startPipeline = async () => {
    await fetch("http://localhost:3000/run-pipeline", { method: "POST" });
    fetchStatus();
  };

  const stopPipeline = async () => {
    await fetch("http://localhost:3000/stop-pipeline", { method: "POST" });
    fetchStatus();
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{padding:"40px",fontFamily:"Arial"}}>

      <h2>CI/CD Dashboard</h2>

      <h3>Status: {status}</h3>

      <button onClick={startPipeline} style={{marginRight:"10px"}}>
        Start Pipeline
      </button>

      <button onClick={stopPipeline}>
        Stop Pipeline
      </button>

    </div>
  );
}