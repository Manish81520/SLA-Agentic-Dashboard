import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import "./styles.css";

const API_URL = "/api/uploads/csv";

function UploadPage() {
  const [file, setFile] = useState(null);
  const [error, setError] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(event) {
    event.preventDefault();
    if (!file) {
      setError("Choose a CSV file before uploading.");
      return;
    }

    setError("");
    setIsProcessing(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const response = await fetch(API_URL, { method: "POST", body: formData });
      const contentType = response.headers.get("content-type") || "";
      const payload = contentType.includes("application/json")
        ? await response.json()
        : {};
      if (!response.ok) {
        throw new Error(payload.detail || "The upload could not be processed.");
      }
      navigate("/result", { state: { response: payload } });
    } catch (requestError) {
      setError(
        requestError instanceof TypeError
          ? "The API could not be reached. Confirm that the backend is running on port 8000."
          : requestError.message || "The upload could not be processed.",
      );
    } finally {
      setIsProcessing(false);
    }
  }

  return (
    <main className="page">
      <section className="card">
        <h1>ExcelAnalyst upload</h1>
        <p>Upload a CSV to validate the upload-to-agent flow.</p>
        <form onSubmit={handleSubmit}>
          <label htmlFor="csv-file">CSV file</label>
          <input
            accept=".csv,text/csv"
            disabled={isProcessing}
            id="csv-file"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            type="file"
          />
          {error && <p className="error" role="alert">{error}</p>}
          <button disabled={isProcessing} type="submit">
            {isProcessing ? "Uploading and processing…" : "Upload CSV"}
          </button>
        </form>
      </section>
    </main>
  );
}

function ResultPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const response = location.state?.response;

  if (!response) {
    return <Navigate replace to="/" />;
  }

  return (
    <main className="page">
      <section className="card result-card">
        <h1>ExcelAnalyst response</h1>
        <pre>{JSON.stringify(response, null, 2)}</pre>
        <button onClick={() => navigate("/")}>Upload another CSV</button>
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
