import { fetchCommitDetails, fetchSupportedFiles } from "../services/githubService.js";
import { callAI }                                  from "../services/aiService.js";
import { triggerPipeline }                         from "../services/pipelineService.js";
import { detectLanguage }                          from "../utils/languageDetector.js";
import { WebhookEvent }                            from "../models/WebhookEvent.js";
import dotenv from "dotenv";
dotenv.config();

const AI_SCORE_THRESHOLD = parseInt(process.env.AI_SCORE_THRESHOLD || "80");
console.log(`AI Score Threshold: ${AI_SCORE_THRESHOLD}`);

export async function handleWebhook(req, res) {
    const payload = req.body || {};

    const repo          = payload.repository?.name         || null;
    const owner         = payload.repository?.owner?.login || null;
    const commitId      = payload.after                    || null;
    const commitMessage = payload.head_commit?.message     || "";
    const branch        = payload.ref?.split("/").pop()    || "main";

    console.log(`\n── New push: ${owner}/${repo} @ ${commitId} ──`);

    // Respond immediately so GitHub doesn't time out
    res.status(202).send("Received");

    // Create a Pending record in MongoDB immediately
    const event = await WebhookEvent.create({
        commitId, repo, owner, commitMessage, branch,
        status: "Pending",
        threshold: AI_SCORE_THRESHOLD
    });

    try {
        if (!repo || !owner || !commitId) {
            await WebhookEvent.findByIdAndUpdate(event._id, { status: "Error" });
            return;
        }

        // Step 2: Fetch changed files from GitHub
        const changedFiles    = await fetchCommitDetails(owner, repo, commitId);
        const processedFiles  = await fetchSupportedFiles(changedFiles, detectLanguage);

        if (processedFiles.length === 0) {
            console.log("No supported files in this commit.");
            await WebhookEvent.findByIdAndUpdate(event._id, { status: "Error" });
            return;
        }

        // Step 3: Score each file with AI
        await WebhookEvent.findByIdAndUpdate(event._id, { status: "Scoring" });

        let totalScore = 0;

        for (const pf of processedFiles) {
            console.log(`  🤖 Scoring ${pf.fileName}...`);

            const aiResult = await callAI(pf.language, pf.sourceCode);

            pf.aiScore     = aiResult.score;
            pf.aiSummary   = aiResult.summary;
            pf.testCases   = aiResult.testCases;
            pf.testsPassed = aiResult.testCases.filter(t => t.passed).length;
            pf.testsFailed = aiResult.testCases.filter(t => !t.passed).length;
            pf.testsTotal  = aiResult.testCases.length;

            totalScore += aiResult.score;
            console.log(`     Score: ${aiResult.score} | Tests: ${pf.testsPassed}✓ ${pf.testsFailed}✗`);
        }

        const overallScore = Math.round(totalScore / processedFiles.length);
        console.log(`\n  📊 Overall Score: ${overallScore} / ${AI_SCORE_THRESHOLD} threshold`);

        // Step 4: Save files + scores to MongoDB
        await WebhookEvent.findByIdAndUpdate(event._id, { files: processedFiles, overallScore });

        // Step 4b: The Gate
        if (overallScore >= AI_SCORE_THRESHOLD) {
            console.log("   Score passed! Triggering pipeline...");
            const pipelineStatus = await triggerPipeline();
            const triggered      = pipelineStatus === 204;

            await WebhookEvent.findByIdAndUpdate(event._id, {
                pipelineTriggered: triggered,
                status: triggered ? "Deployed" : "Error"
            });
            console.log("  🚀 Pipeline trigger status:", pipelineStatus);
        } else {
            console.log("  ❌ Score too low. Pipeline blocked.");
            await WebhookEvent.findByIdAndUpdate(event._id, {
                pipelineTriggered: false,
                status: "Rejected"
            });
        }

    } catch (error) {
        console.error("Webhook processing error:", error.message);
        await WebhookEvent.findByIdAndUpdate(event._id, { status: "Error" });
    }
}