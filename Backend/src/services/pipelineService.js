import fetch from "node-fetch";
import dotenv from "dotenv";
dotenv.config();

/**
 * Trigger a GitHub Actions workflow_dispatch event.
 * @returns {number} HTTP status code (204 = success)
 */
export async function triggerPipeline() {
    const { GITHUB_REPO_OWNER, GITHUB_REPO_NAME, WORKFLOW_FILE, GITHUB_TOKEN } = process.env;

    const url = `https://api.github.com/repos/${GITHUB_REPO_OWNER}/${GITHUB_REPO_NAME}/actions/workflows/${WORKFLOW_FILE}/dispatches`;

    const response = await fetch(url, {
        method: "POST",
        headers: {
            Authorization:  `token ${GITHUB_TOKEN}`,
            Accept:         "application/vnd.github+json",
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ ref: "main" })
    });

    return response.status;
}

/**
 * Fetch the latest GitHub Actions run for the repository.
 */
export async function getLatestPipelineRun() {
    const { GITHUB_REPO_OWNER, GITHUB_REPO_NAME, GITHUB_TOKEN } = process.env;

    const url = `https://api.github.com/repos/${GITHUB_REPO_OWNER}/${GITHUB_REPO_NAME}/actions/runs`;

    const response = await fetch(url, {
        headers: {
            Authorization: `token ${GITHUB_TOKEN}`,
            Accept:        "application/vnd.github+json"
        }
    });

    const data = await response.json();
    return data.workflow_runs?.[0] ?? null;
}
