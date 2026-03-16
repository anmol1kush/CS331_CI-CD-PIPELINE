import cors from "cors"
import express from "express";
import axios from "axios";
import { triggerPipeline } from "./triggerPipeline.js";




const app = express();
app.use(cors())
app.use(express.json());

const SUPPORTED_EXTENSIONS = [".java", ".cpp", ".c", ".js"];


let webhooksCollection = [];

app.get("/", (req, res) => {
    res.send("Server is running");
});

app.post("/github-webhook", async (req, res) => {
    const payload = req.body || {};

    const repo = payload.repository?.name || null;
    const owner = payload.repository?.owner?.login || null;
    const commitId = payload.after || null;

    console.log("New Commit:", commitId);

    try {
        const entry = {
            receivedAt: new Date(),
            repo,
            owner,
            commitId,
            payload,
            processedFiles: []
        };

        // Attempt to fetch commit details
        if (repo && owner && commitId) {
            const commitResponse = await axios(
                `https://api.github.com/repos/${owner}/${repo}/commits/${commitId}`,
                {
                    headers: process.env.GITHUB_TOKEN
                        ? { Authorization: `token ${process.env.GITHUB_TOKEN}` }
                        : {}
                }
            );

            const files = commitResponse.data.files || [];
for (let file of files) {
    const fileName = file.filename;

    if (SUPPORTED_EXTENSIONS.some(ext => fileName.endsWith(ext))) {
        console.log("Supported file detected:", fileName);

        try {
            const fileResponse = await axios(file.raw_url, {
                headers: process.env.GITHUB_TOKEN
                    ? { Authorization: `token ${process.env.GITHUB_TOKEN}` }
                    : {}
            });

            console.log("File Content:\n", fileResponse.data);

            entry.processedFiles.push({
                fileName,
                sourceCode: fileResponse.data
            });
        } catch (err) {
            console.error(`Failed to fetch file ${fileName}:`, err.message);
        }
    }
}
           
                
            
        }

        // Save in memory
        webhooksCollection.push(entry);

        res.status(200).send("Processed successfully");
    } catch (error) {
        console.error(error.message);
        res.status(500).send("Error");
    }
});


app.get("/webhooks", (req, res) => {
    const limit = Math.min(100, parseInt(req.query.limit) || 20);

    const sorted = [...webhooksCollection]
        .sort((a, b) => b.receivedAt - a.receivedAt)
        .slice(0, limit);

    res.json(sorted);
});


const PORT = process.env.PORT || 3000;

app.post("/run-pipeline", async (req, res) => {

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

});

app.get("/pipeline-status", async (req, res) => {
    try {

        const url = `https://api.github.com/repos/${process.env.GITHUB_REPO_OWNER}/${process.env.GITHUB_REPO_NAME}/actions/runs`;

        const response = await axios.get(url, {
            headers: {
                Authorization: `token ${process.env.GITHUB_TOKEN}`,
                Accept: "application/vnd.github+json"
            }
        });

        const latest = response.data.workflow_runs[0];

        res.json({
            status: latest.status,
            conclusion: latest.conclusion,
            id: latest.id
        });

    } catch (err) {
        res.status(500).json({ error: "Failed to fetch pipeline status" });
    }
});

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});