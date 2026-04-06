import mongoose from "mongoose";

const MONGODB_URI =
  process.env.MONGODB_URI || "mongodb://127.0.0.1:27017/cicd_app";

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
