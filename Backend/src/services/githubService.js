import axios from "axios";
import dotenv from "dotenv";
dotenv.config();

const SUPPORTED_EXTENSIONS = [".java", ".cpp", ".c", ".js", ".py"];

function githubHeaders() {
    return process.env.GITHUB_TOKEN
        ? { Authorization: `token ${process.env.GITHUB_TOKEN}` }
        : {};
}

/**
 * Fetch metadata + file list for a single commit.
 */
export async function fetchCommitDetails(owner, repo, commitId) {
    const response = await axios.get(
        `https://api.github.com/repos/${owner}/${repo}/commits/${commitId}`,
        { headers: githubHeaders() }
    );
    return response.data.files || [];
}

/**
 * Download raw source code for every supported file in the commit.
 * @returns {Array<{ fileName, language, sourceCode }>}
 */
export async function fetchSupportedFiles(files, detectLanguage) {
    const results = [];

    for (const file of files) {
        const fileName = file.filename;
        if (!SUPPORTED_EXTENSIONS.some(ext => fileName.endsWith(ext))) continue;

        try {
            const res = await axios.get(file.raw_url, { headers: githubHeaders() });
            results.push({
                fileName,
                language:   detectLanguage(fileName),
                sourceCode: res.data
            });
            console.log("  ✓ Fetched:", fileName);
        } catch (err) {
            console.error("  ✗ Failed to fetch:", fileName, err.message);
        }
    }

    return results;
}
