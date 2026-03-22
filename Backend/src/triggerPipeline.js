import fetch from "node-fetch";
import dotenv from "dotenv";
dotenv.config();
console.log("TOKEN:", process.env.GITHUB_TOKEN);
console.log("OWNER:", process.env.GITHUB_REPO_OWNER);
console.log("REPO:", process.env.GITHUB_REPO_NAME);
console.log("WORKFLOW:", process.env.WORKFLOW_FILE);

export async function triggerPipeline() {

    const url = `https://api.github.com/repos/${process.env.GITHUB_REPO_OWNER}/${process.env.GITHUB_REPO_NAME}/actions/workflows/${process.env.WORKFLOW_FILE}/dispatches`;

    const response = await fetch(url, {
        method: "POST",
        headers: {
            "Authorization": `token ${process.env.GITHUB_TOKEN}`,
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            ref: "main"
        })
    });

    return response.status;
}