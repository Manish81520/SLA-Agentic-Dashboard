import React from "react";
import { ArrowUpFromLine, FileSpreadsheet } from "lucide-react";

export function EmptyDatasetBanner({ onUpload }) {
    return (
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
                onClick={onUpload}
            >
                <ArrowUpFromLine size={14} strokeWidth={2.2} />
                <span>Upload Spreadsheet</span>
            </button>
        </section>
    );
}
