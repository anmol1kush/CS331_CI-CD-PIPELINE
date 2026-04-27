import mongoose from "mongoose";

const testCaseSchema = new mongoose.Schema({
    testId:   { type: String },
    input:    { type: String },
    expected: { type: String },
    actual:   { type: String },
    passed:   { type: Boolean },
    error:    { type: String, default: null }
}, { _id: false });

const fileSchema = new mongoose.Schema({
    fileName:       { type: String, required: true },
    language:       { type: String },
    sourceCode:     { type: String },
    aiScore:        { type: Number, default: null },   // Score given by the AI for this file
    aiSummary:      { type: String, default: null },   // Optional: short note from AI (e.g. "good boundary handling")
    testCases:      { type: [testCaseSchema], default: [] },
    testsPassed:    { type: Number, default: 0 },
    testsFailed:    { type: Number, default: 0 },
    testsTotal:     { type: Number, default: 0 }
}, { _id: false });

const webhookEventSchema = new mongoose.Schema({
    // Commit metadata
    commitId:           { type: String, required: true },
    repo:               { type: String },
    owner:              { type: String },
    commitMessage:      { type: String, default: "" },
    branch:             { type: String, default: "main" },
    pushedAt:           { type: Date, default: Date.now },

    // Files in this commit
    files:              { type: [fileSchema], default: [] },

    // Overall score across all files (average)
    overallScore:       { type: Number, default: null },
    threshold:          { type: Number, default: 80 },

    // Pipeline decision
    pipelineTriggered:  { type: Boolean, default: false },
    status: {
        type: String,
        enum: ["Pending", "Scoring", "Deployed", "Rejected", "Error"],
        default: "Pending"
    },

    // If pipeline was triggered, track its GitHub Actions run status
    pipelineStatus:     { type: String, default: null },    // e.g. "in_progress", "completed"
    pipelineConclusion: { type: String, default: null }     // e.g. "success", "failure"
}, {
    timestamps: true   // adds createdAt + updatedAt automatically
});

export const WebhookEvent = mongoose.model("WebhookEvent", webhookEventSchema);
