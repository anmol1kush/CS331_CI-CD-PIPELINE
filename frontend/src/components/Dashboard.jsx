import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Navbar from "./Navbar";
import AITester from "./AITester";
import CITrigger from "./CITrigger";
import "./Dashboard.css";

const containerVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.1 } }
};

const itemVariants = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" } }
};

const TABS = [
  { id: "overview", label: "Overview", icon: "🏠" },
  { id: "ai-tester", label: "AI Tester", icon: "🤖" },
  { id: "ci-trigger", label: "Run CI", icon: "⚡" },
];

const STAT_CARDS = [
  { icon: "⚡", label: "CI Runs", value: "∞", color: "#7c5cfc" },
  { icon: "🤖", label: "AI Tests", value: "—", color: "#06c7e1" },
  { icon: "✅", label: "Pass Rate", value: "—", color: "#22d3a0" },
  { icon: "🛡️", label: "Coverage", value: "—", color: "#f59e0b" },
];

const FEATURES = [
  {
    icon: "🤖",
    title: "AI Test Generation",
    desc: "Upload your code and let the AI generate comprehensive test cases using hybrid search algorithms.",
  },
  {
    icon: "⚡",
    title: "Trigger CI Pipeline",
    desc: "Manually trigger your GitHub Actions CI/CD workflow and monitor live pipeline status.",
  },
];

function Dashboard({ user, onLogout }) {
  const [activeTab, setActiveTab] = useState("overview");

  return (
    <div className="dashboard-page">
      <Navbar user={user} onLogout={onLogout} />

      <div className="dashboard-body">
        {/* Welcome */}
        <motion.div
          className="welcome-banner"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h2>
            👋 Welcome back,{" "}
            <span className="text-gradient">{user?.name || "User"}</span>
          </h2>
          <p>Here&apos;s what&apos;s happening in your CI/CD pipeline.</p>
        </motion.div>

        {/* Stat Cards */}
        <motion.div
          className="stats-row"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          {STAT_CARDS.map((s) => (
            <motion.div key={s.label} className="stat-card" variants={itemVariants}>
              <div className="stat-card-icon">{s.icon}</div>
              <div className="stat-card-value" style={{ color: s.color }}>{s.value}</div>
              <div className="stat-card-label">{s.label}</div>
            </motion.div>
          ))}
        </motion.div>

        {/* Tabs */}
        <motion.div
          className="tab-row"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          {TABS.map((tab) => (
            <button
              key={tab.id}
              className={`tab-btn ${activeTab === tab.id ? "active" : ""}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          ))}
        </motion.div>

        {/* Tab Content */}
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            className="tab-content-panel"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.25, ease: "easeInOut" }}
          >
            {activeTab === "overview" && (
              <motion.div
                className="feature-grid"
                variants={containerVariants}
                initial="hidden"
                animate="visible"
              >
                {FEATURES.map((f) => (
                  <motion.div
                    key={f.title}
                    className="feature-card"
                    variants={itemVariants}
                    onClick={() => setActiveTab(f.title.includes("AI") ? "ai-tester" : "ci-trigger")}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.99 }}
                  >
                    <div className="feature-card-icon">{f.icon}</div>
                    <div className="feature-card-title">{f.title}</div>
                    <div className="feature-card-desc">{f.desc}</div>
                    <div>
                      <span className="btn btn-primary btn-sm">
                        Open →
                      </span>
                    </div>
                  </motion.div>
                ))}
              </motion.div>
            )}
            {activeTab === "ai-tester" && <AITester user={user} />}
            {activeTab === "ci-trigger" && <CITrigger user={user} />}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}

export default Dashboard;