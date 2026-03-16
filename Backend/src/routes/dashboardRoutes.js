const dashboard = ()=>{
    console.log('dashboardRoutes');
}
app.post("/stop-pipeline", async (req, res) => {

    try {

        const runs = await axios.get(
            `https://api.github.com/repos/${process.env.GITHUB_REPO_OWNER}/${process.env.GITHUB_REPO_NAME}/actions/runs`,
            {
                headers: {
                    Authorization: `token ${process.env.GITHUB_TOKEN}`,
                    Accept: "application/vnd.github+json"
                }
            }
        );

        const latest = runs.data.workflow_runs[0];

        await axios.post(
            `https://api.github.com/repos/${process.env.GITHUB_REPO_OWNER}/${process.env.GITHUB_REPO_NAME}/actions/runs/${latest.id}/cancel`,
            {},
            {
                headers: {
                    Authorization: `token ${process.env.GITHUB_TOKEN}`,
                    Accept: "application/vnd.github+json"
                }
            }
        );

        res.json({ message: "Pipeline cancelled" });

    } catch (err) {
        res.status(500).json({ error: "Failed to stop pipeline" });
    }
});