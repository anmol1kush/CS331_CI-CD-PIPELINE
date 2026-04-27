import express from "express";
import { runPipeline, getPipelineStatus } from "../controllers/pipelineController.js";

const router = express.Router();

router.post("/run-pipeline",     runPipeline);
router.get("/pipeline-status",   getPipelineStatus);

export default router;
