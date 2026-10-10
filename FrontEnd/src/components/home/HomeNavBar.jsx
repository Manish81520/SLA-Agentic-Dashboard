import React from "react";
import { ArrowUpFromLine, BarChart3, Download, Users } from "lucide-react";
import { ExpandingSearch } from "./ExpandingSearch";

export function HomeNavBar({ searchQuery, onSearchChange, onUpload, onExport, onManage, hasData }) {
    return (
        <header className="hn-nav" role="banner">
            <div className="hn-nav__inner">
                <div className="hn-nav__brand">
                    <span className="hn-nav__brand-icon" aria-hidden="true">
                        <BarChart3 size={15} strokeWidth={2.2} />
                    </span>
                    <span className="hn-nav__brand-name">Onboarding</span>
                </div>

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
                    <button type="button" id="hn-manage-btn" className="hn-btn hn-btn--ghost" onClick={onManage} aria-label="Manage partners" title="Add or edit partners"><Users size={14} strokeWidth={2} /><span>Manage</span></button>

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
