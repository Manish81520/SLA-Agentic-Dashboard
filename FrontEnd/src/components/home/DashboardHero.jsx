import React from "react";

export function DashboardHero({ datasetLoaded, datasetInfo, loading }) {
    return (
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
    );
}
