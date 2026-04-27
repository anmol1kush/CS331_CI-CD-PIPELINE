import express from "express";
import { listWebhooks, getWebhookById } from "../controllers/dashboardController.js";

const router = express.Router();

router.get("/webhooks",     listWebhooks);
router.get("/webhooks/:id", getWebhookById);

export default router;