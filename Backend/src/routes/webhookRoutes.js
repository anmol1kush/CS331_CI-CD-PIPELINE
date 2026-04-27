import express from "express";
import { handleWebhook } from "../controllers/webhookController.js";

const router = express.Router();

router.post("/github-webhook", handleWebhook);

export default router;