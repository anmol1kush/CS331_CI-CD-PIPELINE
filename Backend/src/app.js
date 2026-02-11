import express, { json } from "express";
import axios from "axios";

const app = express();
app.use(json());

const SUPPORTED_EXTENSIONS = [".java", ".cpp", ".c", ".js"];

app.post("/github-webhook", async (req, res) => {

    const repo = req.body.repository.name;
    const owner = req.body.repository.owner.login;
    const commitId = req.body.after;

    console.log("New Commit:", commitId);

    try {

        // Get commit details
        const commitResponse = await axios(
            `https://api.github.com/repos/${owner}/${repo}/commits/${commitId}`,
            {
                headers: {
                    Authorization: "token YOUR_GITHUB_TOKEN"
                }
            }
        );

        const files = commitResponse.data.files;

        for (let file of files) {

            const fileName = file.filename;

            // Check if supported language
            if (SUPPORTED_EXTENSIONS.some(ext => fileName.endsWith(ext))) {

                console.log("Supported file detected:", fileName);

                // Fetch raw file content
                const fileResponse = await axios(file.raw_url, {
                    headers: {
                        Authorization: "token YOUR_GITHUB_TOKEN"
                    }
                });

                const sourceCode = fileResponse.data;

                console.log("----- SOURCE CODE -----");
                console.log(sourceCode);

                // 🔥 Send to AI engine here
                // await generateTestCases(sourceCode, fileName);

            }
        }

        res.status(200).send("Processed successfully");

    } catch (error) {
        console.error(error.message);
        res.status(500).send("Error");
    }
});

app.listen(3000, () => {
    console.log("Server running on port 3000");
});
