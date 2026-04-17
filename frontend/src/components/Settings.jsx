import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import "./Settings.css";

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

function Settings({ user, onLogout }) {
  const [settings, setSettings] = useState({
    theme: "light",
    notifications: true,
    autoSave: false
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/settings`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setSettings(data.settings || settings);
      }
    } catch (err) {
      console.error("Failed to fetch settings:", err);
    }
  };

  const handleSettingChange = (key, value) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleSave = async () => {
    setLoading(true);
    setMessage("");

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/settings`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ settings })
      });

      if (response.ok) {
        setMessage("Settings saved successfully!");
      } else {
        setMessage("Failed to save settings");
      }
    } catch (err) {
      setMessage("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    onLogout();
  };

  return (
    <div className="settings">
      <header className="settings-header">
        <div className="header-content">
          <h1>Settings</h1>
          <div className="header-actions">
            {user.position === 'admin' && (
              <Link to="/admin" className="admin-link">Admin Panel</Link>
            )}
            <Link to="/" className="dashboard-link">Dashboard</Link>
            <button onClick={handleLogout} className="logout-btn">Logout</button>
          </div>
        </div>
      </header>

      <div className="settings-content">
        <div className="settings-section">
          <h2>User Profile</h2>
          <div className="profile-info">
            <div className="info-item">
              <strong>Username:</strong> {user.username}
            </div>
            <div className="info-item">
              <strong>Full Name:</strong> {user.name}
            </div>
            <div className="info-item">
              <strong>Position:</strong> {user.position}
            </div>
            <div className="info-item">
              <strong>Employee ID:</strong> {user.employeeId}
            </div>
          </div>
        </div>

        <div className="settings-section">
          <h2>Application Settings</h2>
          <div className="setting-item">
            <label>
              <input
                type="checkbox"
                checked={settings.notifications}
                onChange={(e) => handleSettingChange('notifications', e.target.checked)}
              />
              Enable Notifications
            </label>
          </div>
          <div className="setting-item">
            <label>
              <input
                type="checkbox"
                checked={settings.autoSave}
                onChange={(e) => handleSettingChange('autoSave', e.target.checked)}
              />
              Auto-save Form Data
            </label>
          </div>
          <div className="setting-item">
            <label>
              Theme:
              <select
                value={settings.theme}
                onChange={(e) => handleSettingChange('theme', e.target.value)}
              >
                <option value="light">Light</option>
                <option value="dark">Dark</option>
                <option value="auto">Auto</option>
              </select>
            </label>
          </div>
        </div>

        <div className="settings-actions">
          <button onClick={handleSave} disabled={loading} className="save-btn">
            {loading ? "Saving..." : "Save Settings"}
          </button>
          {message && (
            <div className={`message ${message.includes('success') ? 'success' : 'error'}`}>
              {message}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Settings;