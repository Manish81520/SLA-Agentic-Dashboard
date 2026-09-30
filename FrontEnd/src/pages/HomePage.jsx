import React, { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
    ArrowUpFromLine,
    Download,
    Search,
    Users,
    Clock,
    TrendingUp,
    BarChart3,
    X,
} from "lucide-react";
import "./HomePage.css";

/* ─── Static mock data ─────────────────────────────────────── */
const SUMMARY = {
    totalPartners: 248,
    minDays: 4,
    maxDays: 127,
    avgDays: 31,
};

/* ─────────────────────────────────────────────────────────────
   ExpandingSearch
   · Starts as a compact circular icon button
   · Springs open into a full pill input on click
   · Closes on Escape or blur (when empty)
   · Instant pointer-down feedback per Apple §1
   ───────────────────────────────────────────────────────────── */
function ExpandingSearch({ value, onChange }) {
    const [open, setOpen] = useState(false);
    const inputRef = useRef(null);

    const openSearch = useCallback(() => {
        setOpen(true);
        // Focus after the CSS transition starts so the layout is ready
        requestAnimationFrame(() => inputRef.current?.focus());
    }, []);

    const closeSearch = useCallback(() => {
        if (!value) setOpen(false);
    }, [value]);

    const clearAndClose = useCallback(() => {
        onChange("");
        setOpen(false);
    }, [onChange]);

    // Close on Escape
    useEffect(() => {
        if (!open) return;
        const onKey = (e) => {
            if (e.key === "Escape") {
                clearAndClose();
            }
        };
        window.addEventListener("keydown", onKey);
        return () => window.removeEventListener("keydown", onKey);
    }, [open, clearAndClose]);

    return (
        <div
            className={`hn-search ${open ? "is-open" : ""}`}
            role="search"
        >
            {/* Icon trigger — always visible, becomes the left icon when open */}
            <button
                type="button"
                className="hn-search__trigger"
                aria-label="Open search"
                aria-expanded={open}
                onClick={openSearch}
                tabIndex={open ? -1 : 0}
            >
                <Search size={15} strokeWidth={2.2} />
            </button>

            {/* Expanding content */}
            <div className="hn-search__body" aria-hidden={!open}>
                <input
                    ref={inputRef}
                    id="hn-search-input"
                    type="search"
                    className="hn-search__input"
                    placeholder="Search partners…"
                    value={value}
                    autoComplete="off"
                    tabIndex={open ? 0 : -1}
                    onBlur={closeSearch}
                    onChange={(e) => onChange(e.target.value)}
                    aria-label="Search partners"
                />
                {value && (
                    <button
                        type="button"
                        className="hn-search__clear"
                        aria-label="Clear search"
                        tabIndex={open ? 0 : -1}
                        onMouseDown={(e) => e.preventDefault()} // keep focus in input
                        onClick={clearAndClose}
                    >
                        <X size={12} strokeWidth={2.8} />
                    </button>
                )}
            </div>
        </div>
    );
}

/* ─────────────────────────────────────────────────────────────
   Floating glass NavBar
   · Fixed position, horizontally centred with side inset
   · Full glass pill shape — rounded-2xl
   · Bright top-edge border = light catching the material
   ───────────────────────────────────────────────────────────── */
function NavBar({ searchQuery, onSearchChange, onUpload, onExport }) {
    return (
        <header className="hn-nav" role="banner">
            <div className="hn-nav__inner">
                {/* Wordmark */}
                <div className="hn-nav__brand">
                    <span className="hn-nav__brand-icon" aria-hidden="true">
                        <BarChart3 size={15} strokeWidth={2.2} />
                    </span>
                    <span className="hn-nav__brand-name">Onboarding</span>
                </div>

                {/* Right actions: Search → Export → Upload CSV */}
                <nav className="hn-nav__actions" aria-label="Navigation actions">
                    <ExpandingSearch value={searchQuery} onChange={onSearchChange} />

                    <button
                        type="button"
                        id="hn-export-btn"
                        className="hn-btn hn-btn--ghost"
                        onClick={onExport}
                        aria-label="Export CSV"
                    >
                        <Download size={14} strokeWidth={2} />
                        <span>Export</span>
                    </button>

                    <button
                        type="button"
                        id="hn-upload-btn"
                        className="hn-btn hn-btn--primary"
                        onClick={onUpload}
                        aria-label="Upload CSV"
                    >
                        <ArrowUpFromLine size={14} strokeWidth={2.2} />
                        <span>Upload CSV</span>
                    </button>
                </nav>
            </div>
        </header>
    );
}

/* ─── Summary card ─────────────────────────────────────────── */
function SummaryCard({ id, icon: Icon, label, value, unit, accent }) {
    return (
        <article className={`hn-card hn-card--${accent}`} id={id}>
            <div className="hn-card__icon-wrap" aria-hidden="true">
                <Icon size={18} strokeWidth={1.8} />
            </div>
            <div className="hn-card__body">
                <p className="hn-card__label">{label}</p>
                <p className="hn-card__value">
                    {value.toLocaleString()}
                    {unit && <span className="hn-card__unit">{unit}</span>}
                </p>
            </div>
        </article>
    );
}

/* ─── Page ─────────────────────────────────────────────────── */
export default function HomePage() {
    const navigate = useNavigate();
    const [searchQuery, setSearchQuery] = useState("");

    const handleUpload = () => navigate("/upload");
    const handleExport = () => console.info("Export CSV triggered");

    return (
        <div className="hn-page">
            <NavBar
                searchQuery={searchQuery}
                onSearchChange={setSearchQuery}
                onUpload={handleUpload}
                onExport={handleExport}
            />

            <main className="hn-main" id="main-content">
                <section className="hn-hero">
                    <p className="hn-eyebrow">Overview</p>
                    <h1 className="hn-hero__title">Onboarding Dashboard</h1>
                    <p className="hn-hero__sub">
                        Real-time visibility into partner onboarding stages, SLA health, and completion timelines.
                    </p>
                </section>

                <section className="hn-cards" aria-label="Onboarding summary">
                    <SummaryCard
                        id="card-total-partners"
                        icon={Users}
                        label="Total Partners Onboarded"
                        value={SUMMARY.totalPartners}
                        accent="teal"
                    />
                    <SummaryCard
                        id="card-min-days"
                        icon={Clock}
                        label="Minimum Onboarding Days"
                        value={SUMMARY.minDays}
                        unit=" days"
                        accent="blue"
                    />
                    <SummaryCard
                        id="card-max-days"
                        icon={TrendingUp}
                        label="Maximum Onboarding Days"
                        value={SUMMARY.maxDays}
                        unit=" days"
                        accent="amber"
                    />
                    <SummaryCard
                        id="card-avg-days"
                        icon={BarChart3}
                        label="Average Onboarding Days"
                        value={SUMMARY.avgDays}
                        unit=" days"
                        accent="slate"
                    />
                </section>
            </main>
        </div>
    );
}
