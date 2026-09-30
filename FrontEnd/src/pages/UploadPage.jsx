import React, { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
    BarChart3,
    Check,
    FileSpreadsheet,
    Loader2,
    ShieldCheck,
    Upload,
    Users,
    X,
} from "lucide-react";
import { AppleGlassButton } from "../components/ui/apple-glass-button";
import "./UploadPage.css";

const API_URL = "/api/uploads/csv";
// Backend currently accepts CSV only (main.py). Add ".xlsx", ".xls" here
// once the backend supports them.
const ACCEPTED_EXTENSIONS = [".csv"];
const MAX_SIZE_BYTES = 10 * 1024 * 1024;

const STEPS = ["Upload", "Validate", "Analyze"];
const STATUS_MESSAGES = [
    "Reading your spreadsheet…",
    "Cleaning and validating data…",
    "Detecting onboarding stages…",
    "Mapping columns…",
    "Preparing results…",
];

function ExcelIcon() {
    return (
        <svg className="up-excel" viewBox="0 0 64 64" aria-hidden="true">
            <path d="M22 6h22l14 14v34a4 4 0 0 1-4 4H22a4 4 0 0 1-4-4V10a4 4 0 0 1 4-4z" fill="#f1f7f4" stroke="#1d8f5a" strokeWidth="1.5" />
            <path d="M44 6v10a4 4 0 0 0 4 4h10" fill="#c9e6d8" />
            <rect x="4" y="18" width="30" height="30" rx="4" fill="#1d8f5a" />
            <path d="M13 26l12 14M25 26L13 40" stroke="#fff" strokeWidth="3.5" strokeLinecap="round" />
            <path d="M40 30h12M40 37h12M40 44h12" stroke="#b7d4c6" strokeWidth="2.5" strokeLinecap="round" />
        </svg>
    );
}

function Stepper({ current }) {
    return (
        <ol className="up-stepper" aria-label="Progress">
            {STEPS.map((label, i) => {
                const n = i + 1;
                const state = n < current ? "done" : n === current ? "active" : "todo";
                return (
                    <React.Fragment key={label}>
                        <li className={`up-step up-step--${state}`} aria-current={state === "active" ? "step" : undefined}>
                            <span className="up-step__dot">{state === "done" ? <Check size={16} /> : n}</span>
                            <span className="up-step__label">{label}</span>
                        </li>
                        {n < STEPS.length && <span className={`up-step__line ${n < current ? "is-done" : ""}`} />}
                    </React.Fragment>
                );
            })}
        </ol>
    );
}

function useCyclingMessage(active, messages, intervalMs = 1300) {
    const [index, setIndex] = useState(0);
    useEffect(() => {
        if (!active) {
            setIndex(0);
            return undefined;
        }
        const id = setInterval(() => setIndex((i) => Math.min(i + 1, messages.length - 1)), intervalMs);
        return () => clearInterval(id);
    }, [active, messages.length, intervalMs]);
    return messages[index];
}

function validateFile(file) {
    const name = file.name.toLowerCase();
    if (!ACCEPTED_EXTENSIONS.some((ext) => name.endsWith(ext))) {
        return `Unsupported file type. Please upload ${ACCEPTED_EXTENSIONS.join(", ")}.`;
    }
    if (file.size === 0) return "The selected file is empty.";
    if (file.size > MAX_SIZE_BYTES) return "The file must be 10 MB or smaller.";
    return "";
}

function formatSize(bytes) {
    return bytes < 1024 * 1024 ? `${Math.max(1, Math.round(bytes / 1024))} KB` : `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export default function UploadPage() {
    const navigate = useNavigate();
    const inputRef = useRef(null);
    const [file, setFile] = useState(null);
    const [error, setError] = useState("");
    const [isProcessing, setIsProcessing] = useState(false);
    const [isDragging, setIsDragging] = useState(false);

    const statusMessage = useCyclingMessage(isProcessing, STATUS_MESSAGES);

    const selectFile = useCallback((candidate) => {
        if (!candidate) return;
        const problem = validateFile(candidate);
        setError(problem);
        setFile(problem ? null : candidate);
    }, []);

    const upload = useCallback(async () => {
        if (!file || isProcessing) return;
        setError("");
        setIsProcessing(true);
        try {
            const formData = new FormData();
            formData.append("file", file);
            const response = await fetch(API_URL, { method: "POST", body: formData });
            const isJson = (response.headers.get("content-type") || "").includes("application/json");
            const payload = isJson ? await response.json() : {};
            if (!response.ok) throw new Error(payload.detail || "The upload could not be processed.");
            navigate("/result", { state: { response: payload } });
        } catch (err) {
            setError(
                err instanceof TypeError
                    ? "The API could not be reached. Confirm that the backend is running on port 8000."
                    : err.message || "The upload could not be processed.",
            );
            setIsProcessing(false);
        }
    }, [file, isProcessing, navigate]);

    const handleButtonClick = () => {
        if (isProcessing) return;
        if (file) upload();
        else inputRef.current?.click();
    };

    const handleDrop = (event) => {
        event.preventDefault();
        setIsDragging(false);
        if (isProcessing) return;
        selectFile(event.dataTransfer.files?.[0]);
    };



    return (
        <main className="up-page">
            <Stepper current={isProcessing ? 2 : 1} />

            <header className="up-header">
                <p className="up-eyebrow">Onboarding intelligence</p>
                <h1>See the story in your onboarding data.</h1>
                <p>Upload a CSV and let ExcelAnalyst prepare a clear view of stages, SLA performance, and data quality.</p>
            </header>

            <section className="up-card">
                <div
                    className={`up-dropzone ${isDragging ? "is-dragging" : ""} ${isProcessing ? "is-processing" : ""}`}
                    onDragEnter={(e) => { e.preventDefault(); if (!isProcessing) setIsDragging(true); }}
                    onDragOver={(e) => e.preventDefault()}
                    onDragLeave={(e) => { if (!e.currentTarget.contains(e.relatedTarget)) setIsDragging(false); }}
                    onDrop={handleDrop}
                >
                    <div className="up-hero">
                        <div className={`up-orbit ${isProcessing ? "is-fast" : ""}`}>
                            <span className="up-orbit__chip up-orbit__chip--a"><BarChart3 size={18} /></span>
                            <span className="up-orbit__chip up-orbit__chip--b"><Users size={18} /></span>
                            <span className="up-orbit__chip up-orbit__chip--c"><FileSpreadsheet size={16} /></span>
                            <div className="up-orbit__core"><ExcelIcon /></div>
                        </div>
                    </div>

                    {isProcessing ? (
                        <div className="up-loading" role="status" aria-live="polite">
                            <h2>Analyzing your file</h2>
                            <p key={statusMessage} className="up-loading__msg">{statusMessage}</p>
                            <div className="up-bar" aria-hidden="true"><span /></div>
                        </div>
                    ) : (
                        <>
                            <h2>Drop your CSV here</h2>
                            <p className="up-sub">
                                or{" "}
                                <button type="button" className="up-link" onClick={() => inputRef.current?.click()}>
                                    browse
                                </button>{" "}
                                from your computer
                            </p>
                            <p className="up-meta">CSV · Up to 10 MB · Dates: YYYY-MM-DD</p>
                        </>
                    )}

                    {file && !isProcessing && (
                        <div className="up-file" role="group" aria-label="Selected file">
                            <FileSpreadsheet size={18} />
                            <span className="up-file__name">{file.name}</span>
                            <span className="up-file__size">{formatSize(file.size)}</span>
                            <button type="button" className="up-file__remove" aria-label="Remove file" onClick={() => setFile(null)}>
                                <X size={16} />
                            </button>
                        </div>
                    )}

                    {error && <p className="up-error" role="alert">{error}</p>}

                    <div className="up-cta">
                        <AppleGlassButton
                            type="button"
                            size="md"
                            aria-busy={isProcessing}
                            onClick={handleButtonClick}
                            icon={isProcessing ? <Loader2 size={20} className="up-spin" /> : <Upload size={20} />}
                            className={isProcessing ? "up-cta__btn is-busy" : "up-cta__btn"}
                        >
                            {isProcessing ? "Analyzing…" : file ? "Analyze CSV" : "Choose CSV"}
                        </AppleGlassButton>
                    </div>

                    <input
                        ref={inputRef}
                        type="file"
                        hidden
                        accept={ACCEPTED_EXTENSIONS.join(",")}
                        onChange={(e) => { selectFile(e.target.files?.[0]); e.target.value = ""; }}
                    />
                </div>

                <ul className="up-features">
                    <li>
                        <span className="up-features__icon"><BarChart3 size={20} /></span>
                        <div><strong>Ready for analysis</strong><span>Metrics and insights are prepared automatically.</span></div>
                    </li>
                    <li>
                        <span className="up-features__icon"><Users size={20} /></span>
                        <div><strong>Works across teams</strong><span>One dataset can include every team and stage.</span></div>
                    </li>
                    <li>
                        <span className="up-features__icon"><ShieldCheck size={20} /></span>
                        <div><strong>Private by design</strong><span>Your file remains within this local project.</span></div>
                    </li>
                </ul>
            </section>
        </main>
    );
}
