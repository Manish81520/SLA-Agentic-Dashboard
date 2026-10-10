import React from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import HomePage from "./pages/HomePage";
import UploadPage from "./pages/UploadPage";
import PartnersManagePage from "./pages/PartnersManagePage";
import "./index.css";

function ResultPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const response = location.state?.response;

  if (!response) {
    return <Navigate replace to="/home" />;
  }

  return (
    <main className="up-page">
      <section className="up-result-card">
        <p className="up-eyebrow">Analysis complete</p>
        <h1>ExcelAnalyst response</h1>
        <pre className="up-result-json">{JSON.stringify(response, null, 2)}</pre>
        <button className="up-secondary-button" onClick={() => navigate("/home")}>
          ← Back to Dashboard
        </button>
      </section>
    </main>
  );
}

function App() {
  return (
    <Routes>
      {/* Default → Home */}
      <Route index element={<Navigate replace to="/home" />} />
      <Route path="/home" element={<HomePage />} />
      <Route path="/upload" element={<UploadPage />} />
      <Route path="/result" element={<ResultPage />} />
      <Route path="/partners/manage" element={<PartnersManagePage />} />
      {/* Catch-all */}
      <Route path="*" element={<Navigate replace to="/home" />} />
    </Routes>
  );
}

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
);
