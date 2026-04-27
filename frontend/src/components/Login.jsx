import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useTheme } from "../ThemeContext";
import "./Auth.css";

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

const cardVariants = {
  hidden: { opacity: 0, y: 40, scale: 0.97 },
  visible: {
    opacity: 1, y: 0, scale: 1,
    transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] }
  }
};

const fieldVariants = {
  hidden: { opacity: 0, x: -20 },
  visible: (i) => ({
    opacity: 1, x: 0,
    transition: { delay: i * 0.1 + 0.3, duration: 0.35, ease: "easeOut" }
  })
};

function Login({ onLogin }) {
  const [formData, setFormData] = useState({ username: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();

  const handleChange = (e) =>
    setFormData({ ...formData, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });
      const data = await res.json();
      if (res.ok) { onLogin(data.user, data.token); navigate("/"); }
      else setError(data.error || "Login failed");
    } catch { setError("Network error. Please try again."); }
    finally { setLoading(false); }
  };

  const fields = [
    { name: "username", label: "Username", type: "text", placeholder: "Enter your username" },
    { name: "password", label: "Password", type: "password", placeholder: "Enter your password" },
  ];

  return (
    <div className="auth-page">
      {/* Animated background blobs */}
      <div className="animated-bg">
        <div className="blob3" />
      </div>

      {/* Theme toggle */}
      <div className="auth-theme-toggle">
        <motion.button
          className="theme-toggle"
          onClick={toggleTheme}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
          title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
        >
          {theme === "dark" ? "☀️" : "🌙"}
        </motion.button>
      </div>

      <motion.div
        className="auth-card"
        variants={cardVariants}
        initial="hidden"
        animate="visible"
      >
        {/* Brand */}
        <div className="auth-brand">
          <motion.div
            className="auth-icon"
            animate={{ boxShadow: ["0 0 20px rgba(124,92,252,0.4)", "0 0 40px rgba(6,199,225,0.4)", "0 0 20px rgba(124,92,252,0.4)"] }}
            transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
          >
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
          </motion.div>
          <div>
            <h1 className="auth-title">Welcome back</h1>
          </div>
        </div>

        {/* Error */}
        {error && (
          <motion.div className="auth-error" initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
            ⚠️ {error}
          </motion.div>
        )}

        <form className="auth-form" onSubmit={handleSubmit}>
          {fields.map((f, i) => (
            <motion.div key={f.name} className="input-wrap" custom={i} variants={fieldVariants} initial="hidden" animate="visible">
              <label htmlFor={f.name}>{f.label}</label>
              <input
                className="input-field"
                id={f.name}
                type={f.type}
                name={f.name}
                value={formData[f.name]}
                onChange={handleChange}
                placeholder={f.placeholder}
                required
                autoComplete={f.name === "password" ? "current-password" : "username"}
              />
            </motion.div>
          ))}

          <motion.div
            className="auth-submit"
            custom={fields.length}
            variants={fieldVariants}
            initial="hidden"
            animate="visible"
          >
            <motion.button
              type="submit"
              className="btn btn-primary btn-lg btn-full"
              disabled={loading}
              whileHover={!loading ? { scale: 1.02 } : {}}
              whileTap={!loading ? { scale: 0.98 } : {}}
            >
              {loading ? (
                <><span className="spinner" /> Signing in...</>
              ) : (
                <>Sign In →</>
              )}
            </motion.button>
          </motion.div>
        </form>

        <div className="divider" />
        <p className="auth-footer">
          Don&apos;t have an account?{" "}
          <Link to="/signup">Create account</Link>
        </p>
      </motion.div>
    </div>
  );
}

export default Login;