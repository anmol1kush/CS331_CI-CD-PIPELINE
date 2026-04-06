import mongoose from "mongoose";

const uploadedFileSchema = new mongoose.Schema({
  originalName: { type: String, required: true },
  purpose: {
    type: String,
    enum: ["testing", "deployment"],
    required: true,
  },
  mimeType: { type: String, default: "text/plain" },
  size: { type: Number, required: true },
  content: { type: String, required: true },
  uploadedAt: { type: Date, default: Date.now },
});

export const UploadedFile = mongoose.model("UploadedFile", uploadedFileSchema);
