import mongoose from "mongoose";

const aiTestSchema = new mongoose.Schema({
  employeeId: { type: String, required: true },
  employeeName: { type: String, required: true },
  position: { type: String, default: "developer" },
  testType: {
    type: String,
    enum: ["upload", "sample", "ci_trigger", "deploy_trigger"],
    required: true
  },
  filename: { type: String },
  sourcePath: { type: String },
  result: {
    type: String,
    enum: ["PASS", "FAIL", "triggered"],
    required: true
  },
  output: { type: String },
  jsonResults: { type: mongoose.Schema.Types.Mixed },
  fileContents: { type: String },
  uploadedBy: { type: mongoose.Schema.Types.ObjectId, ref: "User" },
  createdAt: { type: Date, default: Date.now }
});

export const AITest = mongoose.model("AITest", aiTestSchema);