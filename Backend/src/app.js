import cors from "cors";
import express from "express";
import axios from "axios";
import multer from "multer";
import bcrypt from "bcrypt";
import jwt from "jsonwebtoken";
import { triggerPipeline } from "./triggerPipeline.js";
import { connectWithRetry } from "./db.js";
import { UploadedFile } from "./models/UploadedFile.js";
import { User } from "./models/User.js";
import { AITest } from "./models/AITest.js";

const app = express();
app.use(cors());
app.use(express.json());

const SUPPORTED_EXTENSIONS = [".java", ".cpp", ".c", ".py"];

let webhooksCollection = [];

const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 5 * 1024 * 1024 },
});

// JWT Authentication Middleware
const authenticateToken = (req, res, next) => {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];

  if (!token) {
    return res.status(401).json({ error: 'Access token required' });
  }

  jwt.verify(token, process.env.JWT_SECRET || 'your-secret-key', (err, user) => {
    if (err) {
      return res.status(403).json({ error: 'Invalid token' });
    }
    req.user = user;
    next();
  });
};

app.get("/", (req, res) => {
  res.send("CI/CD Backend API is running");
});

// Authentication Routes
app.post("/auth/login", async (req, res) => {
  try {
    const { username, password } = req.body;

    if (!username || !password) {
      return res.status(400).json({ error: "Username and password required" });
    }

    const user = await User.findOne({ username });
    if (!user) {
      return res.status(401).json({ error: "Invalid credentials" });
    }

    const isValidPassword = await bcrypt.compare(password, user.passwordHash);
    if (!isValidPassword) {
      return res.status(401).json({ error: "Invalid credentials" });
    }

    const token = jwt.sign(
      {
        id: user._id,
        username: user.username,
        name: user.name,
        position: user.position,
        employeeId: user.employeeId
      },
      process.env.JWT_SECRET || 'your-secret-key',
      { expiresIn: '24h' }
    );

    res.json({
      token,
      user: {
        id: user._id,
        username: user.username,
        name: user.name,
        position: user.position,
        employeeId: user.employeeId
      }
    });
  } catch (error) {
    console.error("Login error:", error);
    res.status(500).json({ error: "Internal server error" });
  }
});

app.post("/auth/signup", async (req, res) => {
  try {
    const { username, password, name, position } = req.body;

    if (!username || !password || !name) {
      return res.status(400).json({ error: "Username, password, and name are required" });
    }

    const existingUser = await User.findOne({ username });

    if (existingUser) {
      return res.status(409).json({ error: "Username already exists" });
    }

    // Auto-generate employee ID
    const lastUser = await User.findOne().sort({ createdAt: -1 });
    const lastEmployeeNum = lastUser?.employeeId ? parseInt(lastUser.employeeId.replace('EMP', '')) : 0;
    const employeeId = `EMP${String(lastEmployeeNum + 1).padStart(6, '0')}`;

    const saltRounds = 10;
    const passwordHash = await bcrypt.hash(password, saltRounds);

    const user = new User({
      username,
      passwordHash,
      name,
      position: position || 'developer',
      employeeId
    });

    await user.save();

    const token = jwt.sign(
      {
        id: user._id,
        username: user.username,
        name: user.name,
        position: user.position,
        employeeId: user.employeeId
      },
      process.env.JWT_SECRET || 'your-secret-key',
      { expiresIn: '24h' }
    );

    res.status(201).json({
      token,
      user: {
        id: user._id,
        username: user.username,
        name: user.name,
        position: user.position,
        employeeId: user.employeeId
      }
    });
  } catch (error) {
    console.error("Signup error:", error);
    res.status(500).json({ error: "Internal server error" });
  }
});

app.get("/auth/me", authenticateToken, async (req, res) => {
  try {
    const user = await User.findById(req.user.id);
    if (!user) {
      return res.status(404).json({ error: "User not found" });
    }

    res.json({
      user: {
        id: user._id,
        username: user.username,
        name: user.name,
        position: user.position,
        employeeId: user.employeeId
      }
    });
  } catch (error) {
    console.error("Get user error:", error);
    res.status(500).json({ error: "Internal server error" });
  }
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

app.post("/uploads", authenticateToken, upload.single("file"), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: "Missing file field (multipart name: file)" });
    }

    const text = req.file.buffer.toString("utf8");

    // Import fs and path
    const fs = await import('fs');
    const path = await import('path');

    // Save to Intelligence-Module/uploads directory
    const intelligenceModuleDir = path.join(process.cwd(), '..', 'Intelligence-Module');
    const uploadsDir = path.join(intelligenceModuleDir, 'uploads');
    
    if (!fs.existsSync(uploadsDir)) {
      fs.mkdirSync(uploadsDir, { recursive: true });
    }

    // Save file to Intelligence-Module/uploads
    const uploadPath = path.join(uploadsDir, req.file.originalname);
    fs.writeFileSync(uploadPath, text);

    // Save file to database
    const doc = await UploadedFile.create({
      originalName: req.file.originalname,
      purpose: "testing",
      mimeType: req.file.mimetype,
      size: req.file.size,
      content: text,
      uploadedBy: req.user.id
    });

    console.log(`File saved to: ${uploadPath}`);

    // Run Orchestrator.py from Intelligence-Module
    const { spawn } = await import('child_process');
    
    let responseSent = false;
    
    const pythonProcess = spawn('python', ['Orchestrator.py'], {
      cwd: intelligenceModuleDir,
      stdio: ['pipe', 'pipe', 'pipe'],
      env: {
        ...process.env,
        TARGET_FILE: uploadPath
      }
    });

    let output = '';
    let errorOutput = '';

    pythonProcess.stdout.on('data', (data) => {
      const chunk = data.toString();
      output += chunk;
      console.log('Orchestrator stdout:', chunk);
    });

    pythonProcess.stderr.on('data', (data) => {
      const chunk = data.toString();
      errorOutput += chunk;
      console.log('Orchestrator stderr:', chunk);
    });

    pythonProcess.on('close', async (code) => {
      if (responseSent) return;
      responseSent = true;
      
      console.log(`Orchestrator process exited with code ${code}`);
      
      try {
        let jsonResults = {};
        let successStatus = 'PASS';

        // Determine status from exit code
        if (code !== 0) {
          successStatus = 'FAIL';
        }

        // Save AI test result to database
        const aiTest = new AITest({
          employeeId: req.user.employeeId,
          employeeName: req.user.name,
          position: req.user.position,
          testType: 'upload',
          filename: req.file.originalname,
          sourcePath: `Intelligence-Module/uploads/${req.file.originalname}`,
          result: successStatus,
          output: output || errorOutput,
          jsonResults: jsonResults,
          fileContents: text,
          uploadedBy: req.user.id
        });

        await aiTest.save();
        console.log(`Saved AI test result for ${req.file.originalname}`);

        res.status(201).json({
          id: doc._id,
          originalName: doc.originalName,
          purpose: "testing",
          size: doc.size,
          uploadedAt: doc.uploadedAt,
          aiResult: successStatus,
          aiOutput: output || errorOutput,
          jsonResults: jsonResults,
          message: "File uploaded and AI testing completed"
        });
      } catch (error) {
        console.error("AI testing error:", error);
        res.status(201).json({
          id: doc._id,
          originalName: doc.originalName,
          purpose: "testing",
          size: doc.size,
          uploadedAt: doc.uploadedAt,
          aiError: error.message,
          message: "File uploaded but testing encountered an error"
        });
      }
    });

    pythonProcess.on('error', (error) => {
      if (responseSent) return;
      responseSent = true;
      
      console.error("Process error:", error);
      res.status(201).json({
        id: doc._id,
        originalName: doc.originalName,
        purpose: "testing",
        size: doc.size,
        uploadedAt: doc.uploadedAt,
        aiError: "Failed to start AI testing process: " + error.message,
        message: "File uploaded but AI testing could not be started"
      });
    });

    // Timeout after 60 seconds
    const timeoutHandle = setTimeout(() => {
      if (responseSent) return;
      responseSent = true;
      
      pythonProcess.kill();
      res.status(201).json({
        id: doc._id,
        originalName: doc.originalName,
        purpose: "testing",
        size: doc.size,
        uploadedAt: doc.uploadedAt,
        aiError: "AI testing process timed out",
        message: "File uploaded but AI testing took too long"
      });
    }, 60000);

  } catch (err) {
    console.error("Upload error:", err);
    res.status(500).json({ error: "Upload failed", details: err.message });
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

app.post("/run-pipeline", authenticateToken, async (req, res) => {
  try {
    const status = await triggerPipeline();

    if (status === 204) {
      // Save CI trigger event
      const aiTest = new AITest({
        employeeId: req.user.employeeId,
        employeeName: req.user.name,
        position: req.user.position,
        testType: 'ci_trigger',
        result: 'triggered',
        output: 'CI/CD pipeline triggered successfully',
        uploadedBy: req.user.id
      });
      await aiTest.save();

      res.json({ message: "Pipeline triggered successfully" });
    } else {
      res.json({ message: "Pipeline trigger failed", status });
    }
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Pipeline trigger failed" });
  }
});

app.post("/trigger-ci", authenticateToken, async (req, res) => {
  try {
    const status = await triggerPipeline();

    if (status === 204) {
      // Save CI trigger event
      const aiTest = new AITest({
        employeeId: req.user.employeeId,
        employeeName: req.user.name,
        position: req.user.position,
        testType: 'ci_trigger',
        result: 'triggered',
        output: 'CI/CD pipeline triggered successfully',
        uploadedBy: req.user.id
      });
      await aiTest.save();

      res.json({ message: "✓ CI/CD pipeline triggered successfully! Check GitHub Actions for progress." });
    } else {
      res.status(500).json({ error: "Failed to trigger CI pipeline" });
    }
  } catch (error) {
    console.error("CI trigger error:", error);
    res.status(500).json({ error: "Error triggering CI pipeline" });
  }
});

// Sample testing route
app.post("/test-sample", authenticateToken, async (req, res) => {
  try {
    const { sample } = req.body;

    if (!sample) {
      return res.status(400).json({ error: "Sample name required" });
    }

    // Read sample file
    const fs = await import('fs');
    const path = await import('path');
    const samplePath = path.join(process.cwd(), 'samples', sample);

    if (!fs.existsSync(samplePath)) {
      return res.status(404).json({ error: "Sample file not found" });
    }

    const fileContents = fs.readFileSync(samplePath, 'utf-8');

    // Run AI testing
    const { spawn } = await import('child_process');
    const pythonProcess = spawn('python', ['run_target_orchestrator.py'], {
      cwd: process.cwd(),
      stdio: ['pipe', 'pipe', 'pipe']
    });

    let output = '';
    let errorOutput = '';

    pythonProcess.stdout.on('data', (data) => {
      output += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
      errorOutput += data.toString();
    });

    pythonProcess.on('close', async (code) => {
      try {
        // Read results from TARGET_CODE directory
        let jsonResults = {};
        const resultsPath = path.join(process.cwd(), 'TARGET_CODE', 'pipeline_results_summary.json');

        if (fs.existsSync(resultsPath)) {
          const resultsContent = fs.readFileSync(resultsPath, 'utf-8');
          jsonResults = JSON.parse(resultsContent);
        }

        // Save AI test result
        const aiTest = new AITest({
          employeeId: req.user.employeeId,
          employeeName: req.user.name,
          position: req.user.position,
          testType: 'sample',
          filename: sample,
          sourcePath: `samples/${sample}`,
          result: code === 0 ? 'PASS' : 'FAIL',
          output: output || errorOutput,
          jsonResults,
          fileContents,
          uploadedBy: req.user.id
        });

        await aiTest.save();

        res.json({
          filename: sample,
          result: code === 0 ? 'PASS' : 'FAIL',
          output: output || errorOutput,
          jsonResults
        });
      } catch (error) {
        console.error("Sample testing error:", error);
        res.status(500).json({ error: "Sample testing failed", details: error.message });
      }
    });

    pythonProcess.on('error', (error) => {
      console.error("Process error:", error);
      res.status(500).json({ error: "Failed to start sample testing" });
    });

  } catch (error) {
    console.error("Sample test error:", error);
    res.status(500).json({ error: "Sample testing failed" });
  }
});

// Get samples list
app.get("/samples", authenticateToken, async (req, res) => {
  try {
    const fs = await import('fs');
    const path = await import('path');
    const samplesDir = path.join(process.cwd(), 'samples');

    if (!fs.existsSync(samplesDir)) {
      return res.json([]);
    }

    const files = fs.readdirSync(samplesDir);
    const supportedExt = ['.py', '.c', '.cpp', '.java'];
    const samples = files.filter(file =>
      supportedExt.some(ext => file.endsWith(ext))
    );

    res.json(samples);
  } catch (error) {
    console.error("Get samples error:", error);
    res.status(500).json({ error: "Failed to get samples" });
  }
});

// Admin routes
app.get("/admin/users", authenticateToken, async (req, res) => {
  try {
    // Check if user is admin
    if (req.user.position !== 'admin') {
      return res.status(403).json({ error: "Admin access required" });
    }

    const users = await User.find({}, '-passwordHash').sort({ createdAt: -1 });
    res.json(users);
  } catch (error) {
    console.error("Get users error:", error);
    res.status(500).json({ error: "Failed to get users" });
  }
});

app.get("/admin/tests", authenticateToken, async (req, res) => {
  try {
    // Check if user is admin
    if (req.user.position !== 'admin') {
      return res.status(403).json({ error: "Admin access required" });
    }

    const tests = await AITest.find()
      .populate('uploadedBy', 'username name')
      .sort({ createdAt: -1 })
      .limit(100);
    res.json(tests);
  } catch (error) {
    console.error("Get tests error:", error);
    res.status(500).json({ error: "Failed to get tests" });
  }
});

// User settings
app.put("/settings", authenticateToken, async (req, res) => {
  try {
    const { name, newPassword } = req.body;
    const userId = req.user.id;

    const updateData = {};
    if (name) updateData.name = name;

    if (newPassword) {
      const saltRounds = 10;
      updateData.passwordHash = await bcrypt.hash(newPassword, saltRounds);
    }

    const user = await User.findByIdAndUpdate(userId, updateData, { new: true });
    if (!user) {
      return res.status(404).json({ error: "User not found" });
    }

    res.json({
      message: "Settings updated successfully",
      user: {
        id: user._id,
        username: user.username,
        name: user.name,
        position: user.position,
        employeeId: user.employeeId
      }
    });
  } catch (error) {
    console.error("Settings update error:", error);
    res.status(500).json({ error: "Failed to update settings" });
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
