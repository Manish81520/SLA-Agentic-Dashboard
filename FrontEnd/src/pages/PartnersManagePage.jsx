import React, { useEffect, useMemo, useState } from "react";
import { ArrowLeft, BarChart3, Layers3, UserPlus, UsersRound } from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";
import { DashboardToast, ErrorBanner, SearchFeedback } from "../components/home";
import { ExpandingSearch } from "../components/home/ExpandingSearch";
import { PartnerTable } from "../components/partners";
import { useAutoDismiss } from "../hooks/useAutoDismiss";
import { usePartnerManager } from "../hooks/usePartnerManager";
import "./HomePage.css";
import "./PartnersManagePage.css";

export default function PartnersManagePage() {
    const navigate = useNavigate();
    const location = useLocation();
    const { schema, rows, loading, error, datasetLoaded, reload } = usePartnerManager();
    const [query, setQuery] = useState("");
    const [toast, setToast] = useState(() => (location.state?.toast ? { message: location.state.toast } : null));
    const [flashId, setFlashId] = useState(() => location.state?.flashRowId ?? null);

    useEffect(() => {
        if (location.state?.toast || location.state?.flashRowId) navigate(location.pathname, { replace: true, state: null });
    }, []); // clear the one-shot state so a refresh does not replay the toast

    useAutoDismiss(toast, () => setToast(null));

    const filtered = useMemo(() => {
        const needle = query.trim().toLowerCase();
        if (!needle) return rows;
        return rows.filter((row) => {
            const values = Object.values(row.fields).filter((value) => value != null).join(" ");
            return `${values} ${Object.values(row.derived).join(" ")}`.toLowerCase().includes(needle);
        });
    }, [query, rows]);

    useEffect(() => {
        if (!flashId) return undefined;
        const timer = setTimeout(() => setFlashId(null), 1700);
        const target = document.querySelector(`[data-row-id="${flashId}"]`);
        target?.scrollIntoView({ block: "nearest", behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
        return () => clearTimeout(timer);
    }, [flashId, rows]);

    const openAdd = () => navigate("/partners/manage/new");
    const openEdit = (row) => navigate(`/partners/manage/${row.rowId}`);

    return (
        <div className="hn-page pm-page">
            <header className="hn-nav pm-nav" role="banner">
                <div className="hn-nav__inner">
                    <div className="hn-nav__brand"><span className="hn-nav__brand-icon"><BarChart3 size={15} /></span><span>Onboarding</span></div>
                    <nav className="hn-nav__actions" aria-label="Partner actions">
                        <ExpandingSearch value={query} onChange={setQuery} />
                        <button type="button" className="hn-btn hn-btn--primary" disabled={!schema} onClick={openAdd}>
                            <UserPlus size={15} strokeWidth={2.3} /><span>Add partner</span>
                        </button>
                    </nav>
                </div>
            </header>
            <DashboardToast toast={toast} onDismiss={() => setToast(null)} />
            <main className="hn-main pm-main">
                <button type="button" className="pm-back" onClick={() => navigate("/home")}><ArrowLeft size={15} /> Dashboard</button>
                <section className="pm-hero">
                    <div className="pm-hero__copy"><p className="hn-eyebrow">Partner directory</p><h1>People, progress, and the next move.</h1><p>Keep onboarding records accurate without losing sight of the work in motion.</p></div>
                    <div className="pm-hero__metric" aria-label={`${rows.length} partners`}><UsersRound size={19} /><strong>{rows.length}</strong><span>partners</span></div>
                </section>
                {schema?.warnings.map((warning) => <p className="pm-warning" role="status" key={warning}>{warning}</p>)}
                {error && <ErrorBanner message={`Could not load partners: ${error}`} onRetry={reload} />}
                {datasetLoaded && <SearchFeedback query={query} matchCount={filtered.length} totalCount={rows.length} />}
                <section className="pm-card" aria-label="Partners">
                    <header className="pm-card__header"><div><p className="pm-card__eyebrow">Directory</p><h2>{query ? "Search results" : "All partners"}</h2></div>{datasetLoaded && <span className="pm-card__count"><Layers3 size={14} /> {filtered.length} shown</span>}</header>
                    {loading ? <div className="pm-loading" aria-label="Loading partners"><span /><span /><span /><span /><span /></div> : !datasetLoaded ? <div className="pm-empty"><p>No dataset yet. Upload a CSV to start managing partners.</p><button className="hn-btn hn-btn--primary" onClick={() => navigate("/upload")}>Upload CSV</button></div> : filtered.length === 0 ? <div className="pm-empty"><p>{query ? `No partners match “${query}”.` : "No partners found."}</p></div> : <PartnerTable rows={filtered} flashRowId={flashId} onEdit={openEdit} identifierKey={schema.identifierKey} />}
                </section>
            </main>
        </div>
    );
}
