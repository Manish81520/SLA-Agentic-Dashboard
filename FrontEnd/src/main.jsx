import React from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import UploadPage from "./pages/UploadPage";
import "./index.css";

function ResultPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const response = location.state?.response;

  if (!response) {
    return <Navigate replace to="/" />;
  }

  return (
    <main className="up-page">
      <section className="up-result-card">
        <p className="up-eyebrow">Analysis complete</p>
        <h1>ExcelAnalyst response</h1>
        <pre className="up-result-json">{JSON.stringify(response, null, 2)}</pre>
        <button className="up-secondary-button" onClick={() => navigate("/")}>Upload another CSV</button>
      </section>
    </main>
  );
}

function App() {
  return (
    <Routes>
      <Route element={<UploadPage />} path="/" />
      <Route element={<ResultPage />} path="/result" />
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
