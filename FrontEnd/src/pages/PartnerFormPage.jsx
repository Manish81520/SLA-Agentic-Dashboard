import React, { useCallback, useEffect, useMemo, useState } from "react";
import { ArrowLeft, BarChart3, ChevronDown, Loader2 } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import { ErrorBanner } from "../components/home";
import FieldInput, { toInputValue } from "../components/partners/FieldInput";
import { usePartnerManager } from "../hooks/usePartnerManager";
import { createPartner, updatePartner } from "../services/dashboardApi";
import "./HomePage.css";
import "./PartnersManagePage.css";
import "./PartnerFormPage.css";

const LIST_PATH = "/partners/manage";
const prefersReducedMotion = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function PageChrome({ onBack, children }) {
    return (
        <div className="hn-page pm-page pf-page">
            <header className="hn-nav" role="banner">
                <div className="hn-nav__inner">
                    <div className="hn-nav__brand"><span className="hn-nav__brand-icon"><BarChart3 size={15} /></span><span>Onboarding</span></div>
                </div>
            </header>
            <main className="hn-main pf-main">
                <button type="button" className="pm-back" onClick={onBack}><ArrowLeft size={15} /> Partners</button>
                {children}
            </main>
        </div>
    );
}

function PartnerForm({ schema, mode, row, onLeave }) {
    const initial = useMemo(
        () => Object.fromEntries(schema.fields.map((field) => [field.key, mode === "edit" ? toInputValue(field, row.fields[field.key]) : ""])),
        [schema, mode, row],
    );
    const [values, setValues] = useState(initial);
    const [errors, setErrors] = useState({});
    const [formError, setFormError] = useState("");
    const [saving, setSaving] = useState(false);
    const [confirming, setConfirming] = useState(false);
    const [otherOpen, setOtherOpen] = useState(false);
    const [active, setActive] = useState(schema.sections[0]?.id ?? "");
    const [focusKey, setFocusKey] = useState(null);

    const dirty = Object.keys(values).some((key) => values[key] !== initial[key]);
    const completed = row?.derived.status === "Completed";
    const identifier = row && schema.identifierKey ? row.fields[schema.identifierKey] : null;
    const railed = schema.sections.length > 1;
    const fieldIndex = useMemo(() => new Map(schema.fields.map((field, index) => [field.key, index])), [schema]);
    const otherKeys = useMemo(() => new Set(schema.sections.find((section) => section.id === "other")?.fieldKeys ?? []), [schema]);

    useEffect(() => {
        if (!dirty) return undefined;
        const warn = (event) => { event.preventDefault(); event.returnValue = ""; };
        window.addEventListener("beforeunload", warn);
        return () => window.removeEventListener("beforeunload", warn);
    }, [dirty]);

    useEffect(() => {
        if (!confirming) return undefined;
        const onKeyDown = (event) => { if (event.key === "Escape") setConfirming(false); };
        document.addEventListener("keydown", onKeyDown);
        return () => document.removeEventListener("keydown", onKeyDown);
    }, [confirming]);

    useEffect(() => {
        const nodes = document.querySelectorAll("[data-section-id]");
        if (!nodes.length || !("IntersectionObserver" in window)) return undefined;
        const observer = new IntersectionObserver((entries) => {
            const hit = entries
                .filter((entry) => entry.isIntersecting)
                .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
            if (hit) setActive(hit.target.getAttribute("data-section-id"));
        }, { rootMargin: "-20% 0px -65% 0px", threshold: 0 });
        nodes.forEach((node) => observer.observe(node));
        return () => observer.disconnect();
    }, [schema]);

    useEffect(() => {
        if (!focusKey) return;
        const input = document.querySelector(`[data-field-key="${CSS.escape(focusKey)}"] input`);
        input?.focus({ preventScroll: true });
        input?.scrollIntoView({ block: "center", behavior: prefersReducedMotion() ? "auto" : "smooth" });
        setFocusKey(null);
    }, [focusKey]);

    const requestLeave = () => {
        if (saving) return;
        if (dirty) setConfirming(true);
        else onLeave();
    };
    const change = (key, value) => {
        setValues((current) => ({ ...current, [key]: value }));
        setErrors((current) => (current[key] ? { ...current, [key]: undefined } : current));
    };
    const jump = (id) => {
        if (id === "other") setOtherOpen(true);
        setActive(id);
        document.getElementById(`pf-section-${id}`)?.scrollIntoView({ block: "start", behavior: prefersReducedMotion() ? "auto" : "smooth" });
    };
    const showErrors = (map, message) => {
        setErrors(map);
        setFormError(message);
        const first = schema.fields.find((field) => map[field.key]);
        if (!first) return;
        if (otherKeys.has(first.key)) setOtherOpen(true);
        setFocusKey(first.key);
    };
    const submit = async (event) => {
        event.preventDefault();
        if (saving) return;
        const missing = {};
        schema.fields.forEach((field) => {
            if (field.required && !(field.locked && mode === "edit") && !values[field.key]) missing[field.key] = "This field is required.";
        });
        if (Object.keys(missing).length) { showErrors(missing, "Please complete the required fields."); return; }
        const fields = {};
        schema.fields.forEach((field) => {
            if (field.auto || (field.locked && mode === "edit")) return;
            const changed = mode === "add" ? values[field.key] !== "" : values[field.key] !== initial[field.key];
            if (changed) fields[field.key] = values[field.key] === "" ? null : values[field.key];
        });
        setSaving(true);
        setFormError("");
        try {
            const result = mode === "add" ? await createPartner(fields) : await updatePartner(row.rowId, fields);
            onLeave({ toast: mode === "add" ? "Partner added" : "Partner updated", flashRowId: result.rowId });
        } catch (error) {
            const fieldErrors = error.fieldErrors && Object.keys(error.fieldErrors).length ? error.fieldErrors : null;
            if (fieldErrors) showErrors(fieldErrors, "Please fix the highlighted fields.");
            else { setErrors({}); setFormError(error.message || "The partner could not be saved."); }
        } finally {
            setSaving(false);
        }
    };
    const renderField = (key) => {
        const index = fieldIndex.get(key);
        const field = schema.fields[index];
        return <FieldInput key={key} field={field} value={values[key]} error={errors[key]} onChange={change} readOnly={field.locked && mode === "edit"} dateMin={field.notBefore ? values[field.notBefore] || undefined : undefined} id={`pm-field-${index}`} autoValue={row?.fields[key]} />;
    };
    const trapTab = (event) => {
        if (event.key !== "Tab") return;
        const items = event.currentTarget.querySelectorAll("button");
        const first = items[0];
        const last = items[items.length - 1];
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    };

    return (
        <PageChrome onBack={requestLeave}>
            <section className="pf-hero">
                <p className="hn-eyebrow">{mode === "add" ? "New partner" : "Partner record"}</p>
                <h1 className="pf-title">{mode === "add" ? "Add partner" : row.derived.partnerName}</h1>
                {mode === "edit" ? <div className="pf-meta"><span className={`pm-status ${completed ? "pm-status--completed" : "pm-status--progress"}`}>{row.derived.status}</span><span>{row.derived.currentStage}</span>{identifier != null && identifier !== "" && <span>ID {identifier}</span>}</div> : <p className="pf-hint">Enter the details below. Status and current stage are worked out from the dates.</p>}
                {mode === "edit" && schema.hasCompletion && <p className="pf-hint">{completed ? "Clear the completion date to reopen this partner." : "Set a completion date to mark this partner Completed."}</p>}
            </section>
            {schema.warnings.map((warning) => <p className="pm-warning" role="status" key={warning}>{warning}</p>)}
            {formError && <p className="pf-banner" role="alert">{formError}</p>}
            <form id="partner-form" className={`pf-layout${railed ? " pf-layout--rail" : ""}`} noValidate onSubmit={submit}>
                {railed && <nav className="pf-rail" aria-label="Form sections">{schema.sections.map((section) => { const hasError = section.fieldKeys.some((key) => errors[key]); return <button key={section.id} type="button" className={`pf-rail__item${active === section.id ? " is-active" : ""}`} aria-current={active === section.id ? "true" : undefined} onClick={() => jump(section.id)}><span className="pf-rail__label">{section.title}</span>{hasError ? <span className="pf-rail__dot" role="img" aria-label="Has errors" /> : <span className="pf-rail__count">{section.fieldKeys.length}</span>}</button>; })}</nav>}
                <div className="pf-sections">
                    {schema.sections.map((section) => {
                        const isOther = section.id === "other";
                        const open = !isOther || otherOpen;
                        return <section key={section.id} id={`pf-section-${section.id}`} data-section-id={section.id} className="pf-card" aria-labelledby={`pf-heading-${section.id}`}><h2 id={`pf-heading-${section.id}`} className={`pf-card__heading${open ? "" : " is-collapsed"}`}>{isOther ? <button type="button" className="pf-card__toggle" aria-expanded={otherOpen} aria-controls="pf-grid-other" onClick={() => setOtherOpen((value) => !value)}><span>{section.title}</span><em>{section.fieldKeys.length}</em><ChevronDown size={16} className={`pf-card__chev${otherOpen ? " is-open" : ""}`} /></button> : section.title}</h2>{open && <div className="pf-grid" id={`pf-grid-${section.id}`}>{section.fieldKeys.map(renderField)}</div>}</section>;
                    })}
                </div>
            </form>
            <div className="pf-actionbar" role="group" aria-label="Form actions"><span className="pf-actionbar__status" aria-live="polite">{dirty && <span className="pf-dot" aria-hidden="true" />}{dirty ? "Unsaved changes" : mode === "add" ? "Nothing entered yet" : "No changes"}</span><button type="button" className="pf-btn pf-btn--quiet" onClick={requestLeave}>Cancel</button><button type="submit" form="partner-form" className="pf-btn pf-btn--save" disabled={saving || (mode === "edit" && !dirty)}>{saving ? <><Loader2 size={15} className="pf-spin" /> Saving</> : mode === "add" ? "Add partner" : "Save changes"}</button></div>
            {confirming && <div className="pf-alert-layer"><div className="pf-alert-scrim" onClick={() => setConfirming(false)} /><div className="pf-alert" role="alertdialog" aria-modal="true" aria-labelledby="pf-alert-title" aria-describedby="pf-alert-text" onKeyDown={trapTab}><h2 id="pf-alert-title">Discard changes?</h2><p id="pf-alert-text">{mode === "add" ? "This partner hasn’t been added yet." : "Your edits to this partner haven’t been saved."}</p><div className="pf-alert__actions"><button type="button" className="pf-btn pf-btn--quiet" autoFocus onClick={() => setConfirming(false)}>Keep editing</button><button type="button" className="pf-btn pf-btn--danger" onClick={() => onLeave()}>Discard</button></div></div></div>}
        </PageChrome>
    );
}

export default function PartnerFormPage({ mode }) {
    const navigate = useNavigate();
    const { rowId } = useParams();
    const { schema, rows, loading, error, datasetLoaded, reload } = usePartnerManager();
    const row = useMemo(() => (mode === "edit" ? rows.find((item) => String(item.rowId) === rowId) ?? null : null), [mode, rows, rowId]);
    const leave = useCallback((state) => navigate(LIST_PATH, state ? { state } : undefined), [navigate]);
    if (loading) return <PageChrome onBack={() => leave()}><div className="pf-card" aria-busy="true"><div className="pm-loading" aria-label="Loading partner form"><span /><span /><span /><span /></div></div></PageChrome>;
    if (error) return <PageChrome onBack={() => leave()}><ErrorBanner message={`Could not load the partner form: ${error}`} onRetry={reload} /></PageChrome>;
    if (!datasetLoaded || !schema) return <PageChrome onBack={() => leave()}><div className="pf-card"><div className="pm-empty"><p>No dataset yet. Upload a CSV to start managing partners.</p><button type="button" className="hn-btn hn-btn--primary" onClick={() => navigate("/upload")}>Upload CSV</button></div></div></PageChrome>;
    if (mode === "edit" && !row) return <PageChrome onBack={() => leave()}><div className="pf-card"><div className="pm-empty"><p>This partner could not be found. It may have been replaced by a newer upload.</p><button type="button" className="hn-btn hn-btn--primary" onClick={() => leave()}>Back to partners</button></div></div></PageChrome>;
    return <PartnerForm key={mode === "edit" ? `edit:${row.rowId}` : "add"} schema={schema} mode={mode} row={row} onLeave={leave} />;
}
