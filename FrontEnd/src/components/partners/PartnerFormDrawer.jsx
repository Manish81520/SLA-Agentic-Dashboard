import React, { useEffect, useMemo, useRef, useState } from "react";
import { ChevronDown, Loader2, Sparkles, X } from "lucide-react";
import FieldInput, { toInputValue } from "./FieldInput";

export default function PartnerFormDrawer({ schema, mode, row, open, onSubmit, onClose }) {
    const panelRef = useRef(null);
    const initial = useMemo(() => Object.fromEntries(schema.fields.map((field) => [field.key, mode === "edit" ? toInputValue(field, row.fields[field.key]) : ""])), [mode, row, schema]);
    const [values, setValues] = useState(initial);
    const [errors, setErrors] = useState({});
    const [formError, setFormError] = useState("");
    const [saving, setSaving] = useState(false);
    const [confirming, setConfirming] = useState(false);
    const [otherOpen, setOtherOpen] = useState(false);
    const dirty = Object.keys(values).some((key) => values[key] !== initial[key]);
    const completed = row?.derived.status === "Completed";

    useEffect(() => {
        const previous = document.body.style.overflow;
        document.body.style.overflow = "hidden";
        return () => { document.body.style.overflow = previous; };
    }, []);
    useEffect(() => {
        if (open) requestAnimationFrame(() => panelRef.current?.querySelector("input:not([readonly])")?.focus());
    }, [open]);
    useEffect(() => {
        const onKeyDown = (event) => { if (event.key === "Escape") confirming ? setConfirming(false) : requestClose(); };
        document.addEventListener("keydown", onKeyDown);
        return () => document.removeEventListener("keydown", onKeyDown);
    });

    const requestClose = () => { if (!saving) dirty ? setConfirming(true) : onClose(); };
    const change = (key, value) => { setValues((current) => ({ ...current, [key]: value })); setErrors((current) => ({ ...current, [key]: undefined })); };
    const submit = async (event) => {
        event.preventDefault();
        const required = {};
        schema.fields.forEach((field) => { if (field.required && !(field.locked && mode === "edit") && !values[field.key]) required[field.key] = "This field is required."; });
        if (Object.keys(required).length) { setErrors(required); setFormError("Please complete the required fields."); return; }
        const fields = {};
        schema.fields.forEach((field) => {
            if (!field.auto && !(field.locked && mode === "edit") && (mode === "add" ? values[field.key] !== "" : values[field.key] !== initial[field.key])) fields[field.key] = values[field.key] === "" ? null : values[field.key];
        });
        setSaving(true); setFormError("");
        try { await onSubmit(fields); }
        catch (error) { setErrors(error.fieldErrors || {}); setFormError(error.fieldErrors ? "Please fix the highlighted fields." : error.message || "The partner could not be saved."); }
        finally { setSaving(false); }
    };
    const sections = schema.sections.filter((section) => section.id !== "other");
    const other = schema.sections.find((section) => section.id === "other");
    const field = (key) => schema.fields.find((item) => item.key === key);
    const renderField = (key) => {
        const definition = field(key);
        return <FieldInput key={key} field={definition} value={values[key]} error={errors[key]} onChange={change} readOnly={definition.locked && mode === "edit"} dateMin={definition.notBefore ? values[definition.notBefore] || undefined : undefined} id={`pm-field-${schema.fields.indexOf(definition)}`} autoValue={row?.fields[key]} />;
    };

    return <div className="pm-layer">
        <button className={`pm-scrim ${open ? "is-open" : ""}`} aria-label="Close partner editor" onClick={requestClose} />
        <aside className={`pm-drawer ${open ? "is-open" : ""}`} role="dialog" aria-modal="true" aria-labelledby="pm-drawer-title" ref={panelRef}>
            <div className="pm-drawer__topline" />
            <header className="pm-drawer__header"><div><p className="hn-eyebrow">{mode === "add" ? "New partner" : "Partner record"}</p><h2 id="pm-drawer-title">{mode === "add" ? "Add partner" : "Edit partner"}</h2>{mode === "edit" && <p className="pm-drawer__meta">{row.derived.partnerName} <span>•</span> {row.derived.currentStage}</p>}</div><button type="button" className="pm-icon-btn" aria-label="Close" onClick={requestClose}><X size={16} /></button></header>
            <form className="pm-drawer__body" id="partner-form" noValidate onSubmit={submit}>
                {formError && <p className="pm-form-error" role="alert">{formError}</p>}
                {mode === "edit" && schema.hasCompletion && <p className="pm-statusline"><Sparkles size={14} /> <strong>{completed ? "Completed" : "In progress"}</strong><span>{completed ? "Clear completion to reopen." : "Set completion when onboarding is finished."}</span></p>}
                {sections.map((section) => <section className="pm-section" key={section.id}><h3>{section.title}</h3><div className="pm-grid">{section.fieldKeys.map(renderField)}</div></section>)}
                {other && <section className="pm-section pm-other"><button type="button" className="pm-other__toggle" aria-expanded={otherOpen} onClick={() => setOtherOpen((value) => !value)}><span>Other fields <em>{other.fieldKeys.length}</em></span><ChevronDown size={16} className={otherOpen ? "is-open" : ""} /></button>{otherOpen && <div className="pm-grid">{other.fieldKeys.map(renderField)}</div>}</section>}
            </form>
            <footer className="pm-drawer__footer">{confirming ? <><span>Discard unsaved changes?</span><button type="button" className="pm-btn pm-btn--quiet" onClick={() => setConfirming(false)}>Keep editing</button><button type="button" className="pm-btn pm-btn--danger" onClick={onClose}>Discard</button></> : <><button type="button" className="pm-btn pm-btn--quiet" onClick={requestClose}>Cancel</button><button type="submit" form="partner-form" className="pm-btn pm-btn--save" disabled={saving || (mode === "edit" && !dirty)}>{saving ? <><Loader2 size={15} className="pm-spin" /> Saving</> : mode === "add" ? "Add partner" : "Save changes"}</button></>}</footer>
        </aside>
    </div>;
}
