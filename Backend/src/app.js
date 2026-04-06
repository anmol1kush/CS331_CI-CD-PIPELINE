import cors from "cors";
import express from "express";
import axios from "axios";
import multer from "multer";
import { triggerPipeline } from "./triggerPipeline.js";
import { connectWithRetry } from "./db.js";
import { UploadedFile } from "./models/UploadedFile.js";

const app = express();
app.use(cors());
app.use(express.json());

const SUPPORTED_EXTENSIONS = [".java", ".cpp", ".c", ".js"];

let webhooksCollection = [];

const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 5 * 1024 * 1024 },
});

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
      processedFiles: [],
    };

    if (repo && owner && commitId) {
      const commitResponse = await axios(
        `https://api.github.com/repos/${owner}/${repo}/commits/${commitId}`,
        {
          headers: process.env.GITHUB_TOKEN
            ? { Authorization: `token ${process.env.GITHUB_TOKEN}` }
            : {},
        }
      );

      const files = commitResponse.data.files || [];
      for (const file of files) {
        const fileName = file.filename;

        if (SUPPORTED_EXTENSIONS.some((ext) => fileName.endsWith(ext))) {
          console.log("Supported file detected:", fileName);

          try {
            const fileResponse = await axios(file.raw_url, {
              headers: process.env.GITHUB_TOKEN
                ? { Authorization: `token ${process.env.GITHUB_TOKEN}` }
                : {},
            });

            console.log("File Content:\n", fileResponse.data);

            entry.processedFiles.push({
              fileName,
              sourceCode: fileResponse.data,
            });
          } catch (err) {
            console.error(`Failed to fetch file ${fileName}:`, err.message);
          }
        }
      }
    }

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

app.post("/uploads", upload.single("file"), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: "Missing file field (multipart name: file)" });
    }
    const purpose = req.body.purpose;
    if (!purpose || !["testing", "deployment"].includes(purpose)) {
      return res
        .status(400)
        .json({ error: "purpose must be testing or deployment" });
    }

    const text = req.file.buffer.toString("utf8");
    const doc = await UploadedFile.create({
      originalName: req.file.originalname,
      purpose,
      mimeType: req.file.mimetype,
      size: req.file.size,
      content: text,
    });

    res.status(201).json({
      id: doc._id,
      originalName: doc.originalName,
      purpose: doc.purpose,
      size: doc.size,
      uploadedAt: doc.uploadedAt,
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Upload failed" });
  }
});

app.get("/uploads", async (req, res) => {
  try {
    const limit = Math.min(100, parseInt(req.query.limit) || 20);
    const items = await UploadedFile.find()
      .sort({ uploadedAt: -1 })
      .limit(limit)
      .select("-content")
      .lean();
    res.json(items);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Failed to list uploads" });
  }
});

function githubHeaders(token) {
  return {
    Authorization: `token ${token}`,
    Accept: "application/vnd.github+json",
  };
}

function githubRepoEnv() {
  const owner = process.env.GITHUB_REPO_OWNER;
  const name = process.env.GITHUB_REPO_NAME;
  const token = process.env.GITHUB_TOKEN;
  if (!owner || !name || !token) return null;
  return { owner, name, token };
}

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

app.post("/stop-pipeline", async (req, res) => {
  try {
    const owner = process.env.GITHUB_REPO_OWNER;
    const name = process.env.GITHUB_REPO_NAME;
    const token = process.env.GITHUB_TOKEN;

    if (!owner || !name || !token) {
      return res.status(503).json({
        error: "GitHub env not configured (GITHUB_REPO_OWNER, GITHUB_REPO_NAME, GITHUB_TOKEN)",
      });
    }

    const runsUrl = `https://api.github.com/repos/${owner}/${name}/actions/runs`;
    const runs = await axios.get(runsUrl, {
      headers: githubHeaders(token),
      params: { per_page: 5 },
    });

    const runsList = runs.data.workflow_runs || [];
    if (runsList.length === 0) {
      return res.status(404).json({ error: "No workflow runs to cancel" });
    }

    const latest = runsList.find((r) => r.status === "in_progress" || r.status === "queued");
    if (!latest) {
      return res.status(400).json({
        error: "No active or queued run to cancel",
        message: "Latest workflow is already completed or failed.",
      });
    }

    await axios.post(
      `https://api.github.com/repos/${owner}/${name}/actions/runs/${latest.id}/cancel`,
      {},
      { headers: githubHeaders(token) }
    );

    res.json({ message: "Pipeline cancel requested", runId: latest.id });
  } catch (err) {
    console.error(err.response?.data || err.message);
    res.status(500).json({ error: "Failed to stop pipeline" });
  }
});

app.get("/pipeline-status", async (req, res) => {
  try {
    const owner = process.env.GITHUB_REPO_OWNER;
    const name = process.env.GITHUB_REPO_NAME;
    const token = process.env.GITHUB_TOKEN;

    if (!owner || !name || !token) {
      return res.json({
        status: "unknown",
        conclusion: null,
        message: "GitHub not configured",
      });
    }

    const url = `https://api.github.com/repos/${owner}/${name}/actions/runs`;

    const response = await axios.get(url, {
      headers: githubHeaders(token),
      params: { per_page: 1 },
    });

    const runs = response.data.workflow_runs || [];
    if (runs.length === 0) {
      return res.json({
        status: "completed",
        conclusion: null,
        message: "No workflow runs yet",
      });
    }

    const latest = runs[0];
    res.json({
      status: latest.status,
      conclusion: latest.conclusion,
    });
  } catch (err) {
    console.error(err.response?.data || err.message);
    res.status(500).json({ error: "Failed to fetch pipeline status" });
  }
});

app.get("/pipeline-run-details", async (req, res) => {
  try {
    const env = githubRepoEnv();
    if (!env) {
      return res.json({
        configured: false,
        message: "GitHub not configured",
        run: null,
        jobs: [],
      });
    }

    const { owner, name, token } = env;
    const runsRes = await axios.get(
      `https://api.github.com/repos/${owner}/${name}/actions/runs`,
      {
        headers: githubHeaders(token),
        params: { per_page: 1 },
      }
    );

    const runs = runsRes.data.workflow_runs || [];
    if (runs.length === 0) {
      return res.json({
        configured: true,
        message: "No workflow runs yet",
        run: null,
        jobs: [],
        workflowComplete: false,
      });
    }

    const r = runs[0];
    const jobsRes = await axios.get(
      `https://api.github.com/repos/${owner}/${name}/actions/runs/${r.id}/jobs`,
      {
        headers: githubHeaders(token),
        params: { per_page: 100 },
      }
    );

    const rawJobs = jobsRes.data.jobs || [];
    const jobs = rawJobs.map((j) => ({
      id: j.id,
      name: j.name,
      status: j.status,
      conclusion: j.conclusion,
      startedAt: j.started_at,
      completedAt: j.completed_at,
      htmlUrl: j.html_url,
    }));

    const workflowComplete = r.status === "completed";
    const allJobsComplete =
      jobs.length === 0
        ? workflowComplete
        : jobs.every((j) => j.status === "completed");

    res.json({
      configured: true,
      run: {
        id: r.id,
        name: r.name,
        displayTitle: r.display_title,
        status: r.status,
        conclusion: r.conclusion,
        htmlUrl: r.html_url,
        createdAt: r.created_at,
        updatedAt: r.updated_at,
        headBranch: r.head_branch,
        event: r.event,
      },
      jobs,
      workflowComplete,
      allJobsComplete,
    });
  } catch (err) {
    console.error(err.response?.data || err.message);
    res.status(500).json({ error: "Failed to fetch pipeline run details" });
  }
});

async function start() {
  await connectWithRetry();
  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Server running on port ${PORT}`);
  });
}

start().catch((err) => {
  console.error("Failed to start server:", err);
  process.exit(1);
});
