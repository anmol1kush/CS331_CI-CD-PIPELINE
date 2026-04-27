import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import Navbar from "./Navbar";
import "./AdminDashboard.css";

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

const containerVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.1 } }
};
const itemVariants = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" } }
};

const ROLE_CLASS = { admin: "pos-admin", manager: "pos-manager", developer: "pos-developer" };
const RESULT_BADGE = { pass: "badge-success", fail: "badge-danger", error: "badge-danger", warning: "badge-warning" };

function AdminDashboard({ user, onLogout }) {
  const [users, setUsers] = useState([]);
  const [tests, setTests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("token");
      const [usersRes, testsRes] = await Promise.all([
        fetch(`${API_BASE}/admin/users`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API_BASE}/admin/tests`, { headers: { Authorization: `Bearer ${token}` } }),
      ]);
      if (usersRes.ok && testsRes.ok) {
        const ud = await usersRes.json();
        const td = await testsRes.json();
        setUsers(ud.users || []);
        setTests(td.tests || []);
      } else setError("Failed to fetch admin data");
    } catch { setError("Network error"); }
    finally { setLoading(false); }
  };

  const statCards = [
    { icon: "👥", label: "Total Users", value: users.length, bg: "rgba(124,92,252,0.12)", color: "#7c5cfc" },
    { icon: "🧪", label: "Total Tests", value: tests.length, bg: "rgba(6,199,225,0.12)", color: "#06c7e1" },
    { icon: "👨‍💻", label: "Developers", value: users.filter(u => u.position === "developer").length, bg: "rgba(34,211,160,0.12)", color: "#22d3a0" },
    { icon: "🛡️", label: "Admins", value: users.filter(u => u.position === "admin").length, bg: "rgba(245,158,11,0.12)", color: "#f59e0b" },
  ];

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="spinner" style={{ width: 44, height: 44, borderTopColor: "var(--accent)" }} />
        <span style={{ color: "var(--text-secondary)", fontSize: 14 }}>Loading admin data…</span>
      </div>
    );
  }

  return (
    <div className="admin-page">
      <Navbar user={user} onLogout={onLogout} />

      <div className="admin-body">
        <motion.div
          className="admin-header-section"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h2>🛡️ <span className="text-gradient">Admin Dashboard</span></h2>
          <p>Manage users, monitor tests, and oversee your CI/CD pipeline.</p>
        </motion.div>

        {error && (
          <motion.div className="auth-error" style={{ marginBottom: 24 }}
            initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            ⚠️ {error}
          </motion.div>
        )}

        {/* Stat Cards */}
        <motion.div
          className="admin-stats-grid"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          {statCards.map((s) => (
            <motion.div key={s.label} className="admin-stat-card" variants={itemVariants}>
              <div className="admin-stat-header">
                <div className="admin-stat-icon" style={{ background: s.bg }}>
                  {s.icon}
                </div>
                <span className="badge badge-accent">&uarr;</span>
              </div>
              <div className="admin-stat-number" style={{ color: s.color }}>{s.value}</div>
              <div className="admin-stat-label">{s.label}</div>
            </motion.div>
          ))}
        </motion.div>

        {/* Tables */}
        <div className="admin-sections">
          {/* Users Table */}
          <motion.div
            className="admin-section"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <div className="admin-section-header">
              <div className="admin-section-title">👥 User Management</div>
              <span className="badge badge-info">{users.length} users</span>
            </div>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Username</th>
                  <th>Name</th>
                  <th>Role</th>
                  <th>Employee ID</th>
                  <th>Joined</th>
                </tr>
              </thead>
              <tbody>
                {users.length === 0 ? (
                  <tr><td colSpan={5} className="table-no-data">No users found</td></tr>
                ) : users.map((u) => (
                  <tr key={u._id}>
                    <td style={{ fontWeight: 600, color: "var(--text-primary)" }}>{u.username}</td>
                    <td>{u.name}</td>
                    <td>
                      <span className={`pos-badge ${ROLE_CLASS[u.position] || ""}`}>
                        {u.position}
                      </span>
                    </td>
                    <td style={{ fontFamily: "monospace", fontSize: 12 }}>{u.employeeId || "—"}</td>
                    <td>{u.createdAt ? new Date(u.createdAt).toLocaleDateString() : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </motion.div>

          {/* Tests Table */}
          <motion.div
            className="admin-section"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.45 }}
          >
            <div className="admin-section-header">
              <div className="admin-section-title">🧪 Recent AI Tests</div>
              <span className="badge badge-accent">{tests.length} runs</span>
            </div>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Employee ID</th>
                  <th>Test Type</th>
                  <th>Result</th>
                  <th>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {tests.length === 0 ? (
                  <tr><td colSpan={4} className="table-no-data">No tests found</td></tr>
                ) : tests.slice(0, 10).map((t) => (
                  <tr key={t._id}>
                    <td style={{ fontFamily: "monospace", fontSize: 12 }}>{t.employeeId}</td>
                    <td>{t.testType}</td>
                    <td>
                      <span className={`badge ${RESULT_BADGE[t.result?.toLowerCase()] || "badge-info"}`}>
                        {t.result}
                      </span>
                    </td>
                    <td>{t.createdAt ? new Date(t.createdAt).toLocaleString() : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </motion.div>
        </div>
      </div>
    </div>
  );
}

export default AdminDashboard;