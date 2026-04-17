import dotenv from "dotenv";
import mongoose from "mongoose";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

dotenv.config({ path: path.resolve(__dirname, "../../.env") });

const MONGODB_URI =
  process.env.MONGODB_URI || process.env.MONGO_URI || "mongodb://127.0.0.1:27017/cicd_app";

export async function connectDB() {
  if (mongoose.connection.readyState === 1) return;
  await mongoose.connect(MONGODB_URI);
  console.log("MongoDB connected");
}

export async function connectWithRetry(maxAttempts = 15, delayMs = 2000) {
  let lastErr;
  for (let i = 0; i < maxAttempts; i++) {
    try {
      await connectDB();
      return;
    } catch (err) {
      lastErr = err;
      console.warn(
        `MongoDB connection attempt ${i + 1}/${maxAttempts} failed:`,
        err.message
      );
      await new Promise((r) => setTimeout(r, delayMs));
    }
  }
  throw lastErr;
}
