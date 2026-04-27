import { triggerPipeline, getLatestPipelineRun } from "../services/pipelineService.js";

export async function runPipeline(req, res) {
    try {
        const status = await triggerPipeline();
        if (status === 204) {
            res.json({ message: "Pipeline triggered successfully" });
        } else {
            res.json({ message: "Pipeline trigger failed", status });
        }
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: "Pipeline trigger failed" });
    }
}

export async function getPipelineStatus(req, res) {
    try {
        const latest = await getLatestPipelineRun();
        res.json({
            status:     latest?.status     ?? null,
            conclusion: latest?.conclusion ?? null
        });
    } catch (err) {
        console.error("Pipeline API ERROR:", err.message);
        res.status(500).json({ error: "Failed to fetch pipeline status" });
    }
}
