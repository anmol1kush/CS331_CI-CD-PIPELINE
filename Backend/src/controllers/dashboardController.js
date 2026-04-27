import { WebhookEvent } from "../models/WebhookEvent.js";

export async function listWebhooks(req, res) {
    try {
        const limit  = Math.min(100, parseInt(req.query.limit) || 20);
        const events = await WebhookEvent.find()
            .sort({ pushedAt: -1 })
            .limit(limit)
            .select("-files.sourceCode"); // omit source code in list view

        res.json(events);
    } catch (err) {
        res.status(500).json({ error: "Failed to fetch webhook events" });
    }
}

export async function getWebhookById(req, res) {
    try {
        const event = await WebhookEvent.findById(req.params.id);
        if (!event) return res.status(404).json({ error: "Event not found" });
        res.json(event);
    } catch (err) {
        res.status(500).json({ error: "Failed to fetch event" });
    }
}