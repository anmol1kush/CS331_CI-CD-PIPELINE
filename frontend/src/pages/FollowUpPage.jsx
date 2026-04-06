import React, { useState } from "react";
import { Link } from "react-router-dom";
import "./FollowUpPage.css";

export default function FollowUpPage() {
  const [value, setValue] = useState("");

  const onSubmit = (e) => {
    e.preventDefault();
    // Placeholder: wire to an API later
    window.alert(value.trim() ? `Received (${value.length} characters).` : "Nothing entered.");
  };

  return (
    <div className="fu-page">
      <nav className="fu-nav">
        <Link to="/">← Back to dashboard</Link>
      </nav>

      <div className="fu-card">
        <h1 className="fu-title">Follow-up</h1>
        <p className="fu-lead">
          Pipeline finished. Add any note or input here for the next step (not saved yet).
        </p>

        <form onSubmit={onSubmit} className="fu-form">
          <label htmlFor="fu-input" className="fu-label">
            Your input
          </label>
          <textarea
            id="fu-input"
            className="fu-textarea"
            rows={6}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder="Type something…"
          />
          <button type="submit" className="fu-submit">
            Submit
          </button>
        </form>
      </div>
    </div>
  );
}
