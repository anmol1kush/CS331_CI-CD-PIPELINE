import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import "./AdminDashboard.css";

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

function AdminDashboard({ user, onLogout }) {
  const [users, setUsers] = useState([]);
  const [tests, setTests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');

      const [usersRes, testsRes] = await Promise.all([
        fetch(`${API_BASE}/admin/users`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${API_BASE}/admin/tests`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);

      if (usersRes.ok && testsRes.ok) {
        const usersData = await usersRes.json();
        const testsData = await testsRes.json();
        setUsers(usersData.users || []);
        setTests(testsData.tests || []);
      } else {
        setError("Failed to fetch admin data");
      }
    } catch (err) {
      setError("Network error");
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    onLogout();
  };

  if (loading) {
    return <div className="loading">Loading admin dashboard...</div>;
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
            <h3>Total Tests</h3>
            <div className="stat-number">{tests.length}</div>
          </div>
          <div className="stat-card">
            <h3>Active Users</h3>
            <div className="stat-number">
              {users.filter(u => u.position !== 'admin').length}
            </div>
          </div>
          <div className="stat-card">
            <h3>Admin Users</h3>
            <div className="stat-number">
              {users.filter(u => u.position === 'admin').length}
            </div>
          </div>
        </div>

        <div className="data-section">
          <div className="section">
            <h2>User Management</h2>
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Username</th>
                    <th>Name</th>
                    <th>Position</th>
                    <th>Employee ID</th>
                    <th>Created</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map(user => (
                    <tr key={user._id}>
                      <td>{user.username}</td>
                      <td>{user.name}</td>
                      <td>{user.position}</td>
                      <td>{user.employeeId}</td>
                      <td>{new Date(user.createdAt).toLocaleDateString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="section">
            <h2>Recent AI Tests</h2>
            <div className="table-container">
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
                  {tests.slice(0, 10).map(test => (
                    <tr key={test._id}>
                      <td>{test.employeeId}</td>
                      <td>{test.testType}</td>
                      <td>
                        <span className={`result-status ${test.result?.toLowerCase()}`}>
                          {test.result}
                        </span>
                      </td>
                      <td>{new Date(test.createdAt).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AdminDashboard;