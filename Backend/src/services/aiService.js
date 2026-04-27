import axios from "axios";
import dotenv from "dotenv";
dotenv.config();

const AI_API_URL = process.env.AI_API_URL || "http://localhost:8000/evaluate";

/**
 * Send source code to the AI API and get back a score + test results.
 * @param {string} language - "java" | "python" | "cpp" | "c" | "javascript"
 * @param {string} code     - raw source code string
 * @returns {{ score: number, summary: string, testCases: Array }}
 */
export async function callAI(language, code) {
    try {
        const response = await axios.post(AI_API_URL, { language, code }, { timeout: 60000 });
        const data = response.data;

        return {
            score:     data.score     ?? 0,
            summary:   data.summary   ?? "",
            testCases: data.testCases ?? []
        };
    } catch (err) {
        console.error("AI API error:", err.message);
        return {
            score:     0,
            summary:   "AI API error: " + err.message,
            testCases: []
        };
    }
}
