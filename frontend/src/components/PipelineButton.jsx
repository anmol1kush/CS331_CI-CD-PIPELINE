import React from "react";

function PipelineButton() {

    const triggerPipeline = async () => {

        const response = await fetch("http://localhost:3000/run-pipeline", {
            method: "POST"
        });

        const data = await response.json();

        alert(data.message);
    };

    return (
        <div style={{padding:"40px"}}>
            <h2>CI/CD Dashboard</h2>

            <button
                onClick={triggerPipeline}
                style={{
                    padding:"12px 20px",
                    fontSize:"16px",
                    background:"#4CAF50",
                    color:"white",
                    border:"none",
                    borderRadius:"6px",
                    cursor:"pointer"
                }}
            >
                Run CI Pipeline
            </button>
        </div>
    );
}

export default PipelineButton;