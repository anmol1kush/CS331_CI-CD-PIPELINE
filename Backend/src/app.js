import express from "express";
import axios from "axios";
import { MongoClient } from "mongodb";

const app = express();
app.use(express.json());

const SUPPORTED_EXTENSIONS = [".java", ".cpp", ".c", ".js"];

<<<<<<< HEAD
const MONGO_URL = process.env.MONGO_URL || "mongodb://mongo:27017";
const MONGO_DB = process.env.MONGO_DB || "cs331";

let dbClient;
let webhooksCollection;

async function connectDb() {
    dbClient = new MongoClient(MONGO_URL);
    await dbClient.connect();
    const db = dbClient.db(MONGO_DB);
    webhooksCollection = db.collection("webhooks");
    // Create an index for faster queries
    await webhooksCollection.createIndex({ receivedAt: -1 });
    console.log("Connected to MongoDB", MONGO_URL);
}

app.post("/github-webhook", async (req, res) => {
    const payload = req.body || {};

    const repo = payload.repository?.name || null;
    const owner = payload.repository?.owner?.login || null;
    const commitId = payload.after || null;

    console.log("New Commit:", commitId);

    try {
        // Save received payload to MongoDB immediately
        await webhooksCollection.insertOne({
            receivedAt: new Date(),
            repo,
            owner,
            commitId,
            payload
        });

        // Attempt to fetch commit details for supported files (best-effort)
        if (repo && owner && commitId) {
            const commitResponse = await axios(
                `https://api.github.com/repos/${owner}/${repo}/commits/${commitId}`,
                {
                    headers: {
                        Authorization: process.env.GITHUB_TOKEN ? `token ${process.env.GITHUB_TOKEN}` : undefined
                    }
                }
            );

            const files = commitResponse.data.files || [];

            const processedFiles = [];

            for (let file of files) {
                const fileName = file.filename;
                if (SUPPORTED_EXTENSIONS.some(ext => fileName.endsWith(ext))) {
                    console.log("Supported file detected:", fileName);
                    const fileResponse = await axios(file.raw_url, {
                        headers: {
                            Authorization: process.env.GITHUB_TOKEN ? `token ${process.env.GITHUB_TOKEN}` : undefined
                        }
                    });
                    const sourceCode = fileResponse.data;
                    processedFiles.push({ fileName, sourceCode });
                }
            }

            if (processedFiles.length > 0) {
                // Update the previously inserted document with file details
                await webhooksCollection.updateOne(
                    { commitId },
                    { $set: { processedFiles } }
                );
=======
app.post("/github-webhook", async (req, res) => {
    try {
        const repo = req.body?.repository?.name;
        const owner = req.body?.repository?.owner?.login;
        const commitId = req.body?.after;

        if (!repo || !owner || !commitId) {
            return res.status(400).send("Invalid webhook payload");
        }

        console.log("New Commit:", commitId);

        // Ensure GitHub token exists
        const token = process.env.GITHUB_TOKEN;
        if (!token) {
            console.error("GITHUB_TOKEN not set in environment variables");
            return res.status(500).send("Server configuration error");
        }

        // Get commit details
        const commitResponse = await axios.get(
            `https://api.github.com/repos/${owner}/${repo}/commits/${commitId}`,
            {
                headers: {
                    Authorization: `token ${token}`,
                },
            }
        );

        const files = commitResponse.data.files;

        for (let file of files) {
            const fileName = file.filename;

            // Check if supported language
            if (SUPPORTED_EXTENSIONS.some(ext => fileName.endsWith(ext))) {
                console.log("Supported file detected:", fileName);

                // Fetch raw file content
                const fileResponse = await axios.get(file.raw_url, {
                    headers: {
                        Authorization: `token ${token}`,
                    },
                });

                const sourceCode = fileResponse.data;

                console.log("----- SOURCE CODE -----");
                console.log(sourceCode);

                // 🔥 Send to AI engine here
                // await generateTestCases(sourceCode, fileName);
>>>>>>> 79bab1b (Updated webhook backend)
            }
        }

        res.status(200).send("Processed successfully");
    } catch (error) {
<<<<<<< HEAD
        console.error(error);
        res.status(500).send("Error");
=======
        console.error("Error:", error.response?.data || error.message);
        res.status(500).send("Error processing webhook");
>>>>>>> 79bab1b (Updated webhook backend)
    }
});

// Simple endpoint to retrieve recent webhook entries
app.get("/webhooks", async (req, res) => {
    try {
        const limit = Math.min(100, parseInt(req.query.limit) || 20);
        const entries = await webhooksCollection.find({}).sort({ receivedAt: -1 }).limit(limit).toArray();
        res.json(entries);
    } catch (err) {
        console.error(err);
        res.status(500).send("Error fetching webhooks");
    }
});

connectDb()
    .then(() => {
        app.listen(3000, () => {
            console.log("Server running on port 3000");
        });
    })
    .catch((err) => {
        console.error("Failed to connect to DB", err);
        process.exit(1);
    });
