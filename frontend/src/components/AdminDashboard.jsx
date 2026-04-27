import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import Navbar from "./Navbar";
import "./AdminDashboard.css";

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

function AdminDashboard({ onLogout }) {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [removingUserId, setRemovingUserId] = useState("");
  const [error, setError] = useState("");

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    setLoading(true);
    setError("");
    try {
      const token = localStorage.getItem("token");
      const usersRes = await fetch(`${API_BASE}/admin/users`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (!usersRes.ok) {
        const data = await usersRes.json().catch(() => ({}));
        setUsers([]);
        setError(data.error || "Failed to fetch employees");
        return;
      }

      const usersData = await usersRes.json();
      setUsers(usersData.users || []);
    } catch {
      setError("Network error");
      setUsers([]);
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveEmployee = async (employee) => {
    if (employee.position === "admin") {
      return;
    }

    const confirmed = window.confirm(
      `Remove ${employee.name} (${employee.employeeId}) from the database?`
    );

    if (!confirmed) {
      return;
    }

    setRemovingUserId(employee._id);
    setError("");

    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API_BASE}/admin/users/${employee._id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` }
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        setError(data.error || "Failed to remove employee");
        return;
      }

      setUsers((currentUsers) =>
        currentUsers.filter((currentUser) => currentUser._id !== employee._id)
      );
    } catch {
      setError("Network error");
    } finally {
      setRemovingUserId("");
    }
  };

  const handleLogout = () => {
    onLogout();
  };

  const employeeUsers = users.filter((listedUser) => listedUser.position !== "admin");
  const adminUsers = users.filter((listedUser) => listedUser.position === "admin");

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="spinner" style={{ width: 44, height: 44, borderTopColor: "var(--accent)" }} />
        <span style={{ color: "var(--text-secondary)", fontSize: 14 }}>Loading admin data…</span>
      </div>
    );
  }

  return (
    <div className="admin-dashboard">
      <header className="admin-header">
        <div className="header-content">
          <h1>Admin Dashboard</h1>
          <div className="header-actions">
            <Link to="/" className="back-link">Back to Dashboard</Link>
            <Link to="/settings" className="settings-link">Settings</Link>
            <button onClick={handleLogout} className="logout-btn">Logout</button>
          </div>
        </div>
      </header>

      <div className="admin-content">
        {error && <div className="error-message">{error}</div>}

        <div className="stats-grid">
          <div className="stat-card">
            <h3>Total Users</h3>
            <div className="stat-number">{users.length}</div>
          </div>
          <div className="stat-card">
            <h3>Total Employees</h3>
            <div className="stat-number">{employeeUsers.length}</div>
          </div>
          <div className="stat-card">
            <h3>Admin Users</h3>
            <div className="stat-number">{adminUsers.length}</div>
          </div>
        </div>

        <div className="data-section">
          <div className="section">
            <h2>Employee Management</h2>
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Username</th>
                    <th>Name</th>
                    <th>Position</th>
                    <th>Employee ID</th>
                    <th>Created</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.length === 0 && (
                    <tr>
                      <td colSpan="6" className="empty-state">No employees found.</td>
                    </tr>
                  )}
                  {users.map((listedUser) => (
                    <tr key={listedUser._id}>
                      <td>{listedUser.username}</td>
                      <td>{listedUser.name}</td>
                      <td>{listedUser.position}</td>
                      <td>{listedUser.employeeId}</td>
                      <td>{new Date(listedUser.createdAt).toLocaleDateString()}</td>
                      <td>
                        {listedUser.position === "admin" ? (
                          <span className="protected-badge">Protected</span>
                        ) : (
                          <button
                            type="button"
                            className="remove-btn"
                            onClick={() => handleRemoveEmployee(listedUser)}
                            disabled={removingUserId === listedUser._id}
                          >
                            {removingUserId === listedUser._id ? "Removing..." : "Remove"}
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
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
