import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
    ArrowUpFromLine,
    Download,
    Search,
    Users,
    Clock,
    TrendingUp,
    BarChart3,
    FileSpreadsheet,
    CheckCircle2,
    RefreshCw,
    ChevronDown,
    X,
} from "lucide-react";
import "./HomePage.css";

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
        <div className={`hn-search ${open ? "is-open" : ""}`} role="search">
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
                    placeholder="Search partners, teams, IDs…"
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
                        onMouseDown={(e) => e.preventDefault()}
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
   Top Glass NavBar
   ───────────────────────────────────────────────────────────── */
function NavBar({ searchQuery, onSearchChange, onUpload, onExport, hasData }) {
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
                        title={hasData ? "Export dataset as CSV" : "Export summary as CSV"}
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
function SummaryCard({ id, icon: Icon, label, value, unit, accent, loading }) {
    return (
        <article className={`hn-card hn-card--${accent}`} id={id}>
            <div className="hn-card__icon-wrap" aria-hidden="true">
                <Icon size={18} strokeWidth={1.8} />
            </div>
            <div className="hn-card__body">
                <p className="hn-card__label">{label}</p>
                <p className="hn-card__value">
                    {loading ? (
                        <span className="hn-skeleton" aria-hidden="true" />
                    ) : value != null ? (
                        <>
                            {Number(value).toLocaleString()}
                            {unit && <span className="hn-card__unit">{unit}</span>}
                        </>
                    ) : (
                        <span className="hn-card__empty">—</span>
                    )}
                </p>
            </div>
        </article>
    );
}

/* ─── CSV Exporter Helper ──────────────────────────────────── */
function exportDatasetCsv(records, datasetInfo, summary) {
    if (records && records.length > 0) {
        const allFieldKeys = Array.from(
            new Set(records.flatMap((r) => Object.keys(r.fields || {})))
        );
        const headers = ["Record ID", "Group", "Is Complete", ...allFieldKeys];
        const escapeCsv = (val) => {
            if (val == null) return "";
            const s = String(val).replace(/"/g, '""');
            return /[",\n]/.test(s) ? `"${s}"` : s;
        };
        const rows = records.map((r) => [
            escapeCsv(r.recordId),
            escapeCsv(r.group),
            escapeCsv(r.isComplete ? "Yes" : "No"),
            ...allFieldKeys.map((k) => escapeCsv(r.fields?.[k] ?? "")),
        ]);
        const csvContent = [headers.join(","), ...rows.map((row) => row.join(","))].join("\n");
        const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `${(datasetInfo || "onboarding_analysis").replace(/\.[^/.]+$/, "")}_export.csv`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    } else if (summary) {
        const summaryRows = [
            ["Metric", "Value"],
            ["Total Partners Onboarded", summary.totalPartners ?? 0],
            ["Minimum Onboarding Days", summary.minDays ?? ""],
            ["Maximum Onboarding Days", summary.maxDays ?? ""],
            ["Average Onboarding Days", summary.avgDays ?? ""],
        ];
        const csvContent = summaryRows.map((r) => r.join(",")).join("\n");
        const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = "onboarding_summary.csv";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }
}

/* ─── Delivery Pipeline Section ───────────────────────────── */
function PipelineSection({ data, loading, error, onRetry, datasetLoaded }) {
    // Hooks must run before any early return. Collapsed by default.
    const [expanded, setExpanded] = useState(() => new Set());
    const toggleStage = useCallback((key) => {
        setExpanded((prev) => {
            const next = new Set(prev);
            if (next.has(key)) next.delete(key);
            else next.add(key);
            return next;
        });
    }, []);

    if (loading) {
        return (
            <section className="hn-pipeline" aria-label="Onboarding Pipeline">
                <div className="hn-pipeline__header">
                    <p className="hn-eyebrow">Pipeline</p>
                    <h2 className="hn-pipeline__title">Onboarding Pipeline</h2>
                    <p className="hn-pipeline__sub">
                        End-to-end milestone progression and substage duration tracking.
                    </p>
                </div>
                <div className="hn-pipeline__track" aria-hidden="true">
                    {[1, 2, 3].map((step) => (
                        <React.Fragment key={step}>
                            <div className="hn-pipeline__card hn-pipeline__card--skeleton">
                                <div className="hn-pipeline__card-top">
                                    <span className="hn-skeleton hn-skeleton--pill" />
                                    <span className="hn-skeleton hn-skeleton--pill" style={{ width: "3.5rem" }} />
                                </div>
                                <div className="hn-skeleton hn-skeleton--title" />
                                <div className="hn-skeleton hn-skeleton--metric" />
                                <div className="hn-pipeline__substages">
                                    <div className="hn-skeleton hn-skeleton--substage" />
                                    <div className="hn-skeleton hn-skeleton--substage" />
                                </div>
                            </div>
                            {step < 3 && (
                                <div className="hn-pipeline__connector" aria-hidden="true">
                                    <span className="hn-pipeline__connector-line" />
                                    <span className="hn-pipeline__connector-node" />
                                </div>
                            )}
                        </React.Fragment>
                    ))}
                </div>
            </section>
        );
    }

    if (error) {
        return (
            <section className="hn-pipeline" aria-label="Onboarding Pipeline">
                <div className="hn-pipeline__header">
                    <p className="hn-eyebrow">Pipeline</p>
                    <h2 className="hn-pipeline__title">Onboarding Pipeline</h2>
                </div>
                <div className="hn-error-banner" role="alert">
                    <span>Could not load pipeline data: {error}</span>
                    <button type="button" className="hn-retry-btn" onClick={onRetry}>
                        <RefreshCw size={13} />
                        <span>Retry</span>
                    </button>
                </div>
            </section>
        );
    }

    if (!datasetLoaded || !data || !data.mainStages || data.mainStages.length === 0) {
        return (
            <section className="hn-pipeline" aria-label="Onboarding Pipeline">
                <div className="hn-pipeline__header">
                    <p className="hn-eyebrow">Pipeline</p>
                    <h2 className="hn-pipeline__title">Onboarding Pipeline</h2>
                    <p className="hn-pipeline__sub">
                        End-to-end milestone progression and substage duration tracking.
                    </p>
                </div>
                <div className="hn-pipeline__empty">
                    <p>No pipeline data available. Upload an onboarding spreadsheet to view stage breakdowns.</p>
                </div>
            </section>
        );
    }

    const { mainStages, unassigned } = data;

    return (
        <section className="hn-pipeline" aria-label="Onboarding Pipeline">
            <div className="hn-pipeline__header">
                <p className="hn-eyebrow">Pipeline</p>
                <h2 className="hn-pipeline__title">Onboarding Pipeline</h2>
                <p className="hn-pipeline__sub">
                    Chronological progression across key milestone phases and underlying substage durations.
                </p>
            </div>

            <div className="hn-pipeline__track" role="list">
                {mainStages.map((stage, idx) => (
                    <React.Fragment key={stage.id || idx}>
                        <article className="hn-pipeline__card" role="listitem">
                            {/* Step index badge + label */}
                            <div className="hn-pipeline__card-top">
                                <span className="hn-pipeline__step-pill">
                                    Step {String(stage.order ?? idx + 1).padStart(2, "0")}
                                </span>
                                {stage.trackedCount > 0 && (
                                    <span className="hn-pipeline__tracked">
                                        {stage.trackedCount} tracked
                                    </span>
                                )}
                            </div>

                            {/* Main Stage Label */}
                            <h3 className="hn-pipeline__stage-title">{stage.label}</h3>

                            {/* Main Stage Average Days (Prominent) */}
                            <div className="hn-pipeline__metric">
                                <span className="hn-pipeline__metric-value">
                                    {stage.averageDays != null ? stage.averageDays.toFixed(1) : "—"}
                                </span>
                                {stage.averageDays != null && (
                                    <span className="hn-pipeline__metric-unit">days avg</span>
                                )}
                            </div>

                            {/* Substages: collapsed by default, toggled by the chevron */}
                            {(() => {
                                const key = stage.id || String(idx);
                                const isOpen = expanded.has(key);
                                const panelId = `hn-pipeline-panel-${key}`;
                                const subCount = stage.subStages ? stage.subStages.length : 0;
                                return (
                                    <div className="hn-pipeline__substages">
                                        <button
                                            type="button"
                                            className="hn-pipeline__toggle"
                                            aria-expanded={isOpen}
                                            aria-controls={panelId}
                                            onClick={() => toggleStage(key)}
                                        >
                                            <span className="hn-pipeline__substages-label">
                                                Substages ({subCount})
                                            </span>
                                            <ChevronDown
                                                size={16}
                                                strokeWidth={2.2}
                                                className={`hn-pipeline__chevron ${isOpen ? "is-open" : ""}`}
                                                aria-hidden="true"
                                            />
                                        </button>
                                        <div
                                            id={panelId}
                                            className={`hn-pipeline__panel ${isOpen ? "is-open" : ""}`}
                                            role="region"
                                            aria-label={`${stage.label} substages`}
                                        >
                                            <div className="hn-pipeline__panel-inner">
                                                {subCount > 0 ? (
                                                    <ul className="hn-pipeline__substages-list">
                                                        {stage.subStages.map((sub, sIdx) => (
                                                            <li key={sIdx} className="hn-pipeline__substage-item">
                                                                <span className="hn-pipeline__substage-name" title={sub.label}>
                                                                    {sub.label}
                                                                </span>
                                                                <span className="hn-pipeline__substage-days">
                                                                    {sub.averageDays != null ? `${sub.averageDays.toFixed(1)} d` : "\u2014"}
                                                                </span>
                                                            </li>
                                                        ))}
                                                    </ul>
                                                ) : (
                                                    <p className="hn-pipeline__substages-none">No substages mapped</p>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                );
                            })()}
                        </article>

                        {/* Sequence Connector Bar (indicates order only, no data value) */}
                        {idx < mainStages.length - 1 && (
                            <div className="hn-pipeline__connector" aria-hidden="true">
                                <span className="hn-pipeline__connector-line" />
                                <span className="hn-pipeline__connector-node" />
                            </div>
                        )}
                    </React.Fragment>
                ))}
            </div>

            {/* Unassigned Substages (shown only if non-empty) */}
            {unassigned && unassigned.subStages && unassigned.subStages.length > 0 && (
                <div className="hn-pipeline__unassigned">
                    <div className="hn-pipeline__unassigned-header">
                        <span className="hn-pipeline__unassigned-badge">Unassigned</span>
                        <span className="hn-pipeline__unassigned-title">
                            Substages not mapped to a main pipeline phase ({unassigned.subStages.length})
                        </span>
                    </div>
                    <ul className="hn-pipeline__unassigned-list">
                        {unassigned.subStages.map((sub, uIdx) => (
                            <li key={uIdx} className="hn-pipeline__unassigned-item">
                                <span className="hn-pipeline__substage-name">{sub.label}</span>
                                <span className="hn-pipeline__substage-days">
                                    {sub.averageDays != null ? `${sub.averageDays.toFixed(1)} d` : "—"}
                                </span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </section>
    );
}

/* ─── Team Comparison ─────────────────────────────────────── */
function TeamComparisonSection({ data, loading, error, onRetry, onStageChange, datasetLoaded }) {
    const [detailsOpen, setDetailsOpen] = useState(false);

    useEffect(() => setDetailsOpen(false), [data?.selectedStage]);

    if (loading) {
        return (
            <section className="hn-team-comparison" aria-label="Team Comparison" aria-busy="true">
                <div className="hn-team-comparison__header">
                    <div><p className="hn-eyebrow">Team comparison</p><h2>Onboarding time by team</h2></div>
                    <span className="hn-skeleton hn-skeleton--select" aria-hidden="true" />
                </div>
                <div className="hn-team-chart hn-team-chart--skeleton" aria-hidden="true">
                    {[1, 2, 3, 4].map((bar) => <span key={bar} className="hn-skeleton hn-skeleton--bar" />)}
                </div>
            </section>
        );
    }

    if (error) {
        return (
            <section className="hn-team-comparison" aria-label="Team Comparison">
                <div className="hn-team-comparison__header"><div><p className="hn-eyebrow">Team comparison</p><h2>Onboarding time by team</h2></div></div>
                <div className="hn-error-banner" role="alert">
                    <span>Could not load team comparison: {error}</span>
                    <button type="button" className="hn-retry-btn" onClick={onRetry}><RefreshCw size={13} /><span>Retry</span></button>
                </div>
            </section>
        );
    }

    if (!datasetLoaded || !data) {
        return (
            <section className="hn-team-comparison" aria-label="Team Comparison">
                <div className="hn-team-comparison__header"><div><p className="hn-eyebrow">Team comparison</p><h2>Onboarding time by team</h2></div></div>
                <div className="hn-team-comparison__empty">Upload a dataset to compare onboarding time across teams.</div>
            </section>
        );
    }

    const teams = data.teams || [];
    const partners = data.focusArea?.partners || [];
    const focusSummary = data.focusArea?.summary || {};
    const overallAverage = data.overallAverageDays;
    const maxValue = Math.max(...teams.map((team) => team.averageOnboardingDays || 0), overallAverage || 0, 1);
    const averagePosition = Math.min(100, Math.max(0, ((overallAverage || 0) / maxValue) * 100));
    const days = (value) => value == null ? "—" : `${Number(value).toFixed(1)} days`;
    const difference = (value) => value == null ? "—" : `${value > 0 ? "+" : ""}${Number(value).toFixed(1)} days`;

    return (
        <section className="hn-team-comparison" aria-label="Team Comparison">
            <div className="hn-team-comparison__header">
                <div>
                    <p className="hn-eyebrow">Team comparison</p>
                    <h2>Onboarding time by team</h2>
                    <p>Average days for the selected stage. The benchmark is calculated across all tracked partners.</p>
                </div>
                <label className="hn-stage-filter">
                    <span>Stage</span>
                    <select value={data.selectedStage || ""} onChange={(event) => onStageChange(event.target.value)}>
                        {(data.stages || []).map((stage) => <option key={stage.label} value={stage.label}>{stage.label}</option>)}
                    </select>
                    <ChevronDown size={15} aria-hidden="true" />
                </label>
            </div>

            {teams.length > 0 ? (
                <div className="hn-team-chart" role="img" aria-label={`Average onboarding days by team for ${data.selectedStage}`}>
                    <div className="hn-team-chart__axis-title">Average onboarding days</div>
                    <div className="hn-team-chart__content">
                        <div className="hn-team-chart__plot">
                            <div className="hn-team-chart__grid" aria-hidden="true"><span /><span /><span /><span /></div>
                            {overallAverage != null && <div className="hn-team-chart__average" style={{ bottom: `${averagePosition}%` }}><span>Overall average · {days(overallAverage)}</span></div>}
                            <div className="hn-team-chart__bars">
                                {teams.map((team) => {
                                    const height = Math.max(5, ((team.averageOnboardingDays || 0) / maxValue) * 100);
                                    return (
                                        <div className="hn-team-chart__bar-group" key={team.team}>
                                            <span className="hn-team-chart__value">{days(team.averageOnboardingDays)}</span>
                                            <div className="hn-team-chart__bar-track"><span className="hn-team-chart__bar" style={{ "--bar-height": `${height}%` }} /></div>
                                            <span className="hn-team-chart__label" title={team.team}>{team.team}</span>
                                            <span className="hn-team-chart__count">{team.partnerCount} partners</span>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                        <div className="hn-team-chart__x-axis-title">Teams</div>
                    </div>
                </div>
            ) : (
                <div className="hn-team-comparison__empty">No valid onboarding-day values were found for this stage.</div>
            )}

            <section className="hn-focus-area" aria-labelledby="hn-focus-area-title">
                <div className="hn-focus-area__header">
                    <div><p className="hn-eyebrow">Focus area</p><h3 id="hn-focus-area-title">Partner follow-up</h3></div>
                    <button type="button" className="hn-focus-area__toggle" onClick={() => setDetailsOpen((open) => !open)} aria-expanded={detailsOpen}>
                        <span>{detailsOpen ? "Show less" : "See more"}</span><ChevronDown size={16} className={detailsOpen ? "is-open" : ""} />
                    </button>
                </div>
                <div className="hn-focus-area__summary">
                    <div><strong>{focusSummary.partnersNeedingAttention ?? 0}</strong><span>partners needing attention</span></div>
                    <div><strong>{focusSummary.approachingStageAverage ?? 0}</strong><span>approaching stage average</span></div>
                    <div className="hn-focus-area__summary-warning"><strong>{focusSummary.potentialAnomalies ?? 0}</strong><span>potential anomalies</span></div>
                </div>
                {detailsOpen && (
                    <div className="hn-focus-area__details" role="region" aria-label="Partner comparison details">
                        {partners.length > 0 ? (
                            <div className="hn-focus-area__table-wrap"><table><thead><tr><th>Partner</th><th>Team</th><th>Stuck at stage</th><th>Actual</th><th>Average</th><th>Difference</th><th>Onboarding status</th></tr></thead><tbody>{partners.map((partner, index) => <tr key={`${partner.partnerName}-${partner.team}-${index}`} className={partner.isAnomaly ? "is-anomaly" : ""}><td>{partner.partnerName}</td><td>{partner.team}</td><td>{partner.stuckAtStage}</td><td>{days(partner.actualOnboardingDays)}</td><td>{days(partner.expectedAverageDays)}</td><td>{difference(partner.differenceFromAverage)}</td><td><span className={`hn-partner-status ${partner.isAnomaly ? "is-anomaly" : ""}`}>{partner.isAnomaly ? "Potential anomaly" : partner.attentionStatus === "past_stage_average" ? "Past stage average" : "Approaching average"}</span></td></tr>)}</tbody></table></div>
                        ) : <p className="hn-focus-area__none">No active, named partners need attention at this stage.</p>}
                    </div>
                )}
            </section>
        </section>
    );
}

/* ─── Page Component ───────────────────────────────────────── */
export default function HomePage() {
    const navigate = useNavigate();
    const location = useLocation();

    const [summary, setSummary] = useState(null);
    const [records, setRecords] = useState([]);
    const [datasetInfo, setDatasetInfo] = useState(null);
    const [datasetLoaded, setDatasetLoaded] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [toast, setToast] = useState(null);
    const [searchQuery, setSearchQuery] = useState("");

    // Pipeline state (fetched independently of summary)
    const [pipelineData, setPipelineData] = useState(null);
    const [pipelineLoading, setPipelineLoading] = useState(true);
    const [pipelineError, setPipelineError] = useState(null);
    const [teamComparison, setTeamComparison] = useState(null);
    const [teamComparisonLoading, setTeamComparisonLoading] = useState(true);
    const [teamComparisonError, setTeamComparisonError] = useState(null);

    // Load active analysis summary from backend
    const loadSummary = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await fetch("/api/summary");
            if (res.status === 404) {
                setDatasetLoaded(false);
                setSummary(null);
                setRecords([]);
                setDatasetInfo(null);
                return;
            }
            if (!res.ok) {
                throw new Error(`Server returned status ${res.status}`);
            }
            const data = await res.json();
            const kpis = data.kpis || {};
            setSummary({
                totalPartners: kpis.totalCandidates ?? kpis.totalRecords ?? 0,
                minDays: kpis.minTotalOnboardingDays ?? kpis.minimumTotalDuration ?? null,
                maxDays: kpis.maxTotalOnboardingDays ?? kpis.maximumTotalDuration ?? null,
                avgDays: kpis.avgTotalOnboardingDays ?? kpis.averageTotalDuration ?? null,
                totalAnomalies: kpis.totalAnomalies ?? 0,
                groupCount: kpis.projectGroups ?? kpis.groupCount ?? 0,
            });
            setDatasetInfo(data.dataset?.filename || "Uploaded dataset");
            setRecords(data.records || []);
            setDatasetLoaded(true);
        } catch (err) {
            console.error("Failed to load summary from backend:", err);
            setError(err.message || "Failed to load summary");
        } finally {
            setLoading(false);
        }
    }, []);

    // Load pipeline roll-up from backend
    const loadPipeline = useCallback(async () => {
        setPipelineLoading(true);
        setPipelineError(null);
        try {
            const res = await fetch("/api/pipeline");
            if (res.status === 404) {
                setPipelineData(null);
                return;
            }
            if (!res.ok) {
                throw new Error(`Server returned status ${res.status}`);
            }
            const data = await res.json();
            setPipelineData(data);
        } catch (err) {
            console.error("Failed to load pipeline from backend:", err);
            setPipelineError(err.message || "Failed to load pipeline");
        } finally {
            setPipelineLoading(false);
        }
    }, []);

    const loadTeamComparison = useCallback(async (stage) => {
        setTeamComparisonLoading(true);
        setTeamComparisonError(null);
        try {
            const query = stage ? `?${new URLSearchParams({ stage }).toString()}` : "";
            const res = await fetch(`/api/team-comparison${query}`);
            if (res.status === 404) {
                setTeamComparison(null);
                return;
            }
            if (!res.ok) throw new Error(`Server returned status ${res.status}`);
            setTeamComparison(await res.json());
        } catch (err) {
            console.error("Failed to load team comparison:", err);
            setTeamComparisonError(err.message || "Failed to load team comparison");
        } finally {
            setTeamComparisonLoading(false);
        }
    }, []);

    // Initial load and handling navigation state from UploadPage
    useEffect(() => {
        if (location.state?.uploaded && location.state?.response) {
            const calc = location.state.response.calculations || location.state.response;
            const kpis = calc.kpis || {};
            setSummary({
                totalPartners: kpis.totalCandidates ?? kpis.totalRecords ?? 0,
                minDays: kpis.minTotalOnboardingDays ?? kpis.minimumTotalDuration ?? null,
                maxDays: kpis.maxTotalOnboardingDays ?? kpis.maximumTotalDuration ?? null,
                avgDays: kpis.avgTotalOnboardingDays ?? kpis.averageTotalDuration ?? null,
                totalAnomalies: kpis.totalAnomalies ?? 0,
                groupCount: kpis.projectGroups ?? kpis.groupCount ?? 0,
            });
            const filename = location.state.filename || calc.dataset?.filename || "Uploaded dataset";
            setDatasetInfo(filename);
            setRecords(calc.records || []);
            setDatasetLoaded(true);
            setLoading(false);
            setToast({
                message: `Analysis complete: ${filename} processed successfully`,
                type: "success",
            });

            // Refetch pipeline so it reflects the freshly uploaded dataset
            loadPipeline();
            loadTeamComparison();

            // Clear navigation state so browser refresh doesn't trigger repeat notification
            window.history.replaceState({}, document.title);
        } else {
            loadSummary();
            loadPipeline();
            loadTeamComparison();
        }
    }, [location.state, loadSummary, loadPipeline, loadTeamComparison]);

    // Auto-dismiss toast after 6s
    useEffect(() => {
        if (!toast) return;
        const timer = setTimeout(() => setToast(null), 6000);
        return () => clearTimeout(timer);
    }, [toast]);

    const handleUpload = () => navigate("/upload");

    const handleExport = () => {
        exportDatasetCsv(records, datasetInfo, summary);
    };

    // Client-side search filtering across records
    const filteredRecords = useMemo(() => {
        if (!searchQuery.trim() || !records.length) return records;
        const q = searchQuery.toLowerCase().trim();
        return records.filter((rec) => {
            const id = String(rec.recordId || "").toLowerCase();
            const grp = String(rec.group || "").toLowerCase();
            const fields = Object.values(rec.fields || {}).join(" ").toLowerCase();
            return id.includes(q) || grp.includes(q) || fields.includes(q);
        });
    }, [searchQuery, records]);

    // If search is active, compute metrics for the matched subset
    const displayMetrics = useMemo(() => {
        if (!summary) return null;
        if (!searchQuery.trim()) return summary;

        const count = filteredRecords.length;
        return {
            ...summary,
            totalPartners: count,
        };
    }, [summary, searchQuery, filteredRecords]);

    return (
        <div className="hn-page">
            <NavBar
                searchQuery={searchQuery}
                onSearchChange={setSearchQuery}
                onUpload={handleUpload}
                onExport={handleExport}
                hasData={records.length > 0}
            />

            {/* Apple Toast notification */}
            {toast && (
                <div className="hn-toast-container">
                    <div className="hn-toast" role="status" aria-live="polite">
                        <CheckCircle2 size={16} className="hn-toast__icon" />
                        <span className="hn-toast__msg">{toast.message}</span>
                        <button
                            type="button"
                            className="hn-toast__close"
                            onClick={() => setToast(null)}
                            aria-label="Dismiss message"
                        >
                            <X size={12} strokeWidth={2.5} />
                        </button>
                    </div>
                </div>
            )}

            <main className="hn-main" id="main-content">
                <section className="hn-hero">
                    <div className="hn-hero__meta">
                        <p className="hn-eyebrow">Overview</p>
                        {datasetLoaded && datasetInfo && (
                            <span className="hn-badge hn-badge--live" title="Active dataset loaded on backend">
                                <span className="hn-badge__dot" />
                                {datasetInfo}
                            </span>
                        )}
                        {!loading && !datasetLoaded && (
                            <span className="hn-badge hn-badge--pending">
                                Waiting for upload
                            </span>
                        )}
                    </div>

                    <h1 className="hn-hero__title">Onboarding Dashboard</h1>
                    <p className="hn-hero__sub">
                        Real-time visibility into partner onboarding stages, SLA health, and completion timelines derived from Excel analysis.
                    </p>
                </section>

                {/* Empty State Banner when no dataset has been analyzed yet */}
                {!loading && !datasetLoaded && (
                    <section className="hn-empty-banner" aria-label="No data analyzed">
                        <div className="hn-empty-banner__icon">
                            <FileSpreadsheet size={26} strokeWidth={1.8} />
                        </div>
                        <div className="hn-empty-banner__body">
                            <h2 className="hn-empty-banner__title">No spreadsheet analyzed yet</h2>
                            <p className="hn-empty-banner__desc">
                                Upload your onboarding Excel or CSV file. The ExcelAnalyst agent will identify columns, detect stage durations, calculate SLA milestones, and populate this dashboard.
                            </p>
                        </div>
                        <button
                            type="button"
                            className="hn-btn hn-btn--primary hn-empty-banner__cta"
                            onClick={handleUpload}
                        >
                            <ArrowUpFromLine size={14} strokeWidth={2.2} />
                            <span>Upload Spreadsheet</span>
                        </button>
                    </section>
                )}

                {/* Error Banner with retry */}
                {error && (
                    <div className="hn-error-banner" role="alert">
                        <span>Could not connect to backend analysis: {error}</span>
                        <button type="button" className="hn-retry-btn" onClick={loadSummary}>
                            <RefreshCw size={13} />
                            <span>Retry</span>
                        </button>
                    </div>
                )}

                {/* Search match status if filtering */}
                {Boolean(searchQuery.trim()) && datasetLoaded && (
                    <div className="hn-search-feedback">
                        Showing <strong>{filteredRecords.length}</strong> of{" "}
                        <strong>{summary?.totalPartners ?? 0}</strong> partners matching &ldquo;{searchQuery}&rdquo;
                    </div>
                )}

                {/* Summary Cards */}
                <section className="hn-cards" aria-label="Onboarding summary">
                    <SummaryCard
                        id="card-total-partners"
                        icon={Users}
                        label={searchQuery.trim() ? "Matching Partners" : "Total Partners Onboarded"}
                        value={displayMetrics?.totalPartners}
                        accent="teal"
                        loading={loading}
                    />
                    <SummaryCard
                        id="card-min-days"
                        icon={Clock}
                        label="Minimum Onboarding Days"
                        value={displayMetrics?.minDays}
                        unit=" days"
                        accent="blue"
                        loading={loading}
                    />
                    <SummaryCard
                        id="card-max-days"
                        icon={TrendingUp}
                        label="Maximum Onboarding Days"
                        value={displayMetrics?.maxDays}
                        unit=" days"
                        accent="amber"
                        loading={loading}
                    />
                    <SummaryCard
                        id="card-avg-days"
                        icon={BarChart3}
                        label="Average Onboarding Days"
                        value={displayMetrics?.avgDays}
                        unit=" days"
                        accent="slate"
                        loading={loading}
                    />
                </section>

                {/* Onboarding Delivery Pipeline Section */}
                <PipelineSection
                    data={pipelineData}
                    loading={pipelineLoading}
                    error={pipelineError}
                    onRetry={loadPipeline}
                    datasetLoaded={datasetLoaded}
                />

                <TeamComparisonSection
                    data={teamComparison}
                    loading={teamComparisonLoading}
                    error={teamComparisonError}
                    onRetry={() => loadTeamComparison(teamComparison?.selectedStage)}
                    onStageChange={loadTeamComparison}
                    datasetLoaded={datasetLoaded}
                />
            </main>
        </div>
    );
}
