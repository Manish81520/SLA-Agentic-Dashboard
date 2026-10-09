import React, { useCallback, useEffect, useState } from "react";
import { ChevronDown } from "lucide-react";
import { formatDayDifference, formatDays } from "../../utils/formatDuration";
import { fetchFocusArea } from "../../services/dashboardApi";
import { ErrorBanner } from "./ErrorBanner";

function partnerStatusLabel(partner) {
    if (partner.isAnomaly) return "Potential anomaly";
    if (partner.attentionStatus === "past_stage_average") return "Past stage average";
    return "Approaching average";
}

export function FocusAreaSection() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [detailsOpen, setDetailsOpen] = useState(false);

    const loadFocusArea = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetchFocusArea();
            setData(response);
        } catch (err) {
            console.error("Failed to load focus area:", err);
            setError(err.message || "Failed to load focus area");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadFocusArea();
    }, [loadFocusArea]);

    if (loading) {
        return (
            <section className="hn-focus-area" aria-labelledby="hn-focus-area-title" aria-busy="true">
                <div className="hn-focus-area__header">
                    <div>
                        <p className="hn-eyebrow">Focus area</p>
                        <h3 id="hn-focus-area-title">Partner follow-up</h3>
                    </div>
                </div>
                <div className="hn-focus-area__summary">
                    <div><span className="hn-skeleton hn-skeleton--text" aria-hidden="true" /></div>
                    <div><span className="hn-skeleton hn-skeleton--text" aria-hidden="true" /></div>
                    <div><span className="hn-skeleton hn-skeleton--text" aria-hidden="true" /></div>
                </div>
            </section>
        );
    }

    if (error) {
        return (
            <section className="hn-focus-area" aria-labelledby="hn-focus-area-title">
                <div className="hn-focus-area__header">
                    <div>
                        <p className="hn-eyebrow">Focus area</p>
                        <h3 id="hn-focus-area-title">Partner follow-up</h3>
                    </div>
                </div>
                <ErrorBanner message={`Could not load focus area: ${error}`} onRetry={loadFocusArea} />
            </section>
        );
    }

    if (!data) {
        return (
            <section className="hn-focus-area" aria-labelledby="hn-focus-area-title">
                <div className="hn-focus-area__header">
                    <div>
                        <p className="hn-eyebrow">Focus area</p>
                        <h3 id="hn-focus-area-title">Partner follow-up</h3>
                    </div>
                </div>
                <div className="hn-focus-area__empty">Upload a dataset to see partners needing attention.</div>
            </section>
        );
    }

    const partners = data.focusArea?.partners || [];
    const focusSummary = data.focusArea?.summary || {};

    return (
        <section className="hn-focus-area" aria-labelledby="hn-focus-area-title">
            <div className="hn-focus-area__header">
                <div>
                    <p className="hn-eyebrow">Focus area</p>
                    <h3 id="hn-focus-area-title">Partner follow-up</h3>
                </div>
                <button
                    type="button"
                    className="hn-focus-area__toggle"
                    onClick={() => setDetailsOpen((open) => !open)}
                    aria-expanded={detailsOpen}
                >
                    <span>{detailsOpen ? "Show less" : "See more"}</span>
                    <ChevronDown size={16} className={detailsOpen ? "is-open" : ""} />
                </button>
            </div>
            <div className="hn-focus-area__summary">
                <div>
                    <strong>{focusSummary.partnersNeedingAttention ?? 0}</strong>
                    <span>partners needing attention</span>
                </div>
                <div>
                    <strong>{focusSummary.approachingStageAverage ?? 0}</strong>
                    <span>approaching stage average</span>
                </div>
                <div className="hn-focus-area__summary-warning">
                    <strong>{focusSummary.potentialAnomalies ?? 0}</strong>
                    <span>potential anomalies</span>
                </div>
            </div>
            {detailsOpen && (
                <div className="hn-focus-area__details" role="region" aria-label="Partner comparison details">
                    {partners.length > 0 ? (
                        <div className="hn-focus-area__table-wrap">
                            <table>
                                <thead>
                                    <tr>
                                        <th>Partner</th>
                                        <th>Team</th>
                                        <th>Stuck at stage</th>
                                        <th>Actual</th>
                                        <th>Average</th>
                                        <th>Difference</th>
                                        <th>Onboarding status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {partners.map((partner, index) => (
                                        <tr
                                            key={`${partner.partnerName}-${partner.team}-${index}`}
                                            className={partner.isAnomaly ? "is-anomaly" : ""}
                                        >
                                            <td>{partner.partnerName}</td>
                                            <td>{partner.team}</td>
                                            <td>{partner.stuckAtStage}</td>
                                            <td>{formatDays(partner.actualOnboardingDays)}</td>
                                            <td>{formatDays(partner.expectedAverageDays)}</td>
                                            <td>{formatDayDifference(partner.differenceFromAverage)}</td>
                                            <td>
                                                <span className={`hn-partner-status ${partner.isAnomaly ? "is-anomaly" : ""}`}>
                                                    {partnerStatusLabel(partner)}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    ) : (
                        <p className="hn-focus-area__none">No active, named partners need attention at this stage.</p>
                    )}
                </div>
            )}
        </section>
    );
}
