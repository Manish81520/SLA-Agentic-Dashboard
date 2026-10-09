import React, { useState } from "react";
import { ChevronDown } from "lucide-react";
import { formatDays } from "../../utils/formatDuration";
import { ErrorBanner } from "./ErrorBanner";

export function PartnersListSection({ data, loading, error, onRetry, datasetLoaded }) {
    const [isOpen, setIsOpen] = useState(false);

    const partners = data?.partners || [];

    return (
        <section className="hn-partners-list" aria-labelledby="hn-partners-list-title">
            <button
                type="button"
                className="hn-partners-list__header"
                onClick={() => setIsOpen((open) => !open)}
                aria-expanded={isOpen}
                aria-controls="hn-partners-list-content"
            >
                <div>
                    <p className="hn-eyebrow">Partners</p>
                    <h2 id="hn-partners-list-title">Partners list</h2>
                </div>
                <span className="hn-partners-list__toggle">
                    <ChevronDown size={20} className={isOpen ? "is-open" : ""} aria-hidden="true" />
                </span>
            </button>

            {isOpen && (
                <div className="hn-partners-list__content" id="hn-partners-list-content">
                    {loading ? (
                        <div className="hn-partners-list__skeleton" aria-busy="true">
                            <span className="hn-skeleton hn-skeleton--text" />
                            <span className="hn-skeleton hn-skeleton--text" />
                            <span className="hn-skeleton hn-skeleton--text" />
                        </div>
                    ) : error ? (
                        <ErrorBanner message={`Could not load partners list: ${error}`} onRetry={onRetry} />
                    ) : !datasetLoaded || !data ? (
                        <div className="hn-partners-list__empty">Upload a dataset to see the partners list.</div>
                    ) : partners.length === 0 ? (
                        <div className="hn-partners-list__empty">No partners found in the dataset.</div>
                    ) : (
                        <div className="hn-partners-list__table-wrap">
                            <table>
                                <thead>
                                    <tr>
                                        <th>Partner</th>
                                        <th>Team</th>
                                        <th>Current stage</th>
                                        <th>Onboarding days</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {partners.map((partner, index) => (
                                        <tr key={partner.partnerId || `${partner.partnerName}-${index}`}>
                                            <td>{partner.partnerName}</td>
                                            <td>{partner.team}</td>
                                            <td>{partner.currentStage}</td>
                                            <td>{formatDays(partner.onboardingDays)}</td>
                                            <td>
                                                <span className="hn-partner-status">
                                                    {partner.status}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            )}
        </section>
    );
}
