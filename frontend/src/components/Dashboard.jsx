import { useState } from "react";
import { Link } from "react-router-dom";
import AITester from "./AITester";
import CITrigger from "./CITrigger";
import "./Dashboard.css";

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

function Dashboard({ user, onLogout }) {
  const [activeTab, setActiveTab] = useState("ai-tester");

  const handleLogout = () => {
    onLogout();
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-content">
          <h1>CI/CD Pipeline Dashboard</h1>
          <div className="user-info">
            <span>Welcome, {user.name} ({user.position})</span>
            <div className="header-actions">
              {user.position === 'admin' && (
                <Link to="/admin" className="admin-link">Admin Panel</Link>
              )}
              <Link to="/settings" className="settings-link">Settings</Link>
              <button onClick={handleLogout} className="logout-btn">Logout</button>
            </div>
          </div>
        </div>
      </header>

      <div className="dashboard-content">
        <div className="tabs">
          <button
            className={`tab ${activeTab === 'ai-tester' ? 'active' : ''}`}
            onClick={() => setActiveTab('ai-tester')}
          >
            Run AI Tester
          </button>
          <button
            className={`tab ${activeTab === 'ci-trigger' ? 'active' : ''}`}
            onClick={() => setActiveTab('ci-trigger')}
          >
            Run CI
          </button>
        </div>

        <div className="tab-content">
          {activeTab === 'ai-tester' && <AITester user={user} />}
          {activeTab === 'ci-trigger' && <CITrigger user={user} />}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;