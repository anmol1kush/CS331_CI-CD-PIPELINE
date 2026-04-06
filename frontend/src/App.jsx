import { BrowserRouter, Routes, Route } from "react-router-dom";
import "./App.css";
import CICDDashboard from "./components/CICDDashboard";
import FollowUpPage from "./pages/FollowUpPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<CICDDashboard />} />
        <Route path="/follow-up" element={<FollowUpPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
