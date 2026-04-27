import { motion } from "framer-motion";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useTheme } from "../ThemeContext";
import "./Navbar.css";

function Navbar({ user, onLogout }) {
  const { theme, toggleTheme } = useTheme();
  const location = useLocation();
  const navigate = useNavigate();

  const initials = user?.name
    ? user.name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2)
    : "U";

  const handleLogout = () => {
    onLogout();
    navigate("/login");
  };

  const isActive = (path) => location.pathname === path;

  return (
    <motion.header
      className="navbar"
      initial={{ y: -80, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
    >
      {/* Logo */}
      <Link to="/" className="nav-logo">
        <div className="nav-logo-icon">⚡</div>
        <span className="text-gradient">CI/CD Pipeline</span>
      </Link>

      {/* Nav Links */}
      <nav className="nav-links">
        <Link
          to="/"
          className={`nav-link ${isActive("/") ? "active" : ""}`}
        >
          <span>🏠</span>
          <span className="nav-label">Dashboard</span>
        </Link>

        {user?.position === "admin" && (
          <Link
            to="/admin"
            className={`nav-link ${isActive("/admin") ? "active" : ""}`}
          >
            <span>🛡️</span>
            <span className="nav-label">Admin</span>
          </Link>
        )}

        <Link
          to="/settings"
          className={`nav-link ${isActive("/settings") ? "active" : ""}`}
        >
          <span>⚙️</span>
          <span className="nav-label">Settings</span>
        </Link>
      </nav>

      {/* Right side */}
      <div className="nav-right">
        {/* Theme Toggle */}
        <motion.button
          className="theme-toggle"
          onClick={toggleTheme}
          title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
        >
          {theme === "dark" ? "☀️" : "🌙"}
        </motion.button>

        {/* User */}
        {user && (
          <div className="nav-user">
            <motion.div
              className="nav-avatar"
              whileHover={{ scale: 1.1, boxShadow: "0 0 20px rgba(124,92,252,0.6)" }}
            >
              {initials}
            </motion.div>
            <div className="nav-user-info">
              <span className="nav-user-name">{user.name}</span>
              <span className="nav-user-role">{user.position}</span>
            </div>
          </div>
        )}

        {/* Logout */}
        <motion.button
          className="btn btn-danger btn-sm"
          onClick={handleLogout}
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
        >
          Logout
        </motion.button>
      </div>
    </motion.header>
  );
}

export default Navbar;
