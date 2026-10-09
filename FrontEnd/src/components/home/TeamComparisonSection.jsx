import React from "react";
import { ChevronDown } from "lucide-react";
import { formatDays } from "../../utils/formatDuration";
import { ErrorBanner } from "./ErrorBanner";



function TeamChart({ teams, overallAverage, selectedStage }) {
    const maxValue = Math.max(
        ...teams.map((team) => team.averageOnboardingDays || 0),
        overallAverage || 0,
        1,
    );
    const averagePosition = Math.min(100, Math.max(0, ((overallAverage || 0) / maxValue) * 100));

    return (
        <div className="hn-team-chart" role="img" aria-label={`Average onboarding days by team for ${selectedStage}`}>
            <div className="hn-team-chart__axis-title">Average onboarding days</div>
            <div className="hn-team-chart__content">
                <div className="hn-team-chart__plot">
                    <div className="hn-team-chart__grid" aria-hidden="true"><span /><span /><span /><span /></div>
                    {overallAverage != null && (
                        <div className="hn-team-chart__average" style={{ bottom: `${averagePosition}%` }}>
                            <span>Overall average · {formatDays(overallAverage)}</span>
                        </div>
                    )}
                    <div className="hn-team-chart__bars">
                        {teams.map((team) => {
                            const height = Math.max(5, ((team.averageOnboardingDays || 0) / maxValue) * 100);
                            return (
                                <div className="hn-team-chart__bar-group" key={team.team}>
                                    <span className="hn-team-chart__value">{formatDays(team.averageOnboardingDays)}</span>
                                    <div className="hn-team-chart__bar-track">
                                        <span className="hn-team-chart__bar" style={{ "--bar-height": `${height}%` }} />
                                    </div>
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
    );
}



export function TeamComparisonSection({ data, loading, error, onRetry, onStageChange, datasetLoaded }) {

    if (loading) {
        return (
            <section className="hn-team-comparison" aria-label="Team Comparison" aria-busy="true">
                <div className="hn-team-comparison__header">
                    <div>
                        <p className="hn-eyebrow">Team comparison</p>
                        <h2>Onboarding time by team</h2>
                    </div>
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
                <div className="hn-team-comparison__header">
                    <div>
                        <p className="hn-eyebrow">Team comparison</p>
                        <h2>Onboarding time by team</h2>
                    </div>
                </div>
                <ErrorBanner message={`Could not load team comparison: ${error}`} onRetry={onRetry} />
            </section>
        );
    }

    if (!datasetLoaded || !data) {
        return (
            <section className="hn-team-comparison" aria-label="Team Comparison">
                <div className="hn-team-comparison__header">
                    <div>
                        <p className="hn-eyebrow">Team comparison</p>
                        <h2>Onboarding time by team</h2>
                    </div>
                </div>
                <div className="hn-team-comparison__empty">Upload a dataset to compare onboarding time across teams.</div>
            </section>
        );
    }

    const teams = data.teams || [];

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
                        {(data.stages || []).map((stage) => (
                            <option key={stage.label} value={stage.label}>{stage.label}</option>
                        ))}
                    </select>
                    <ChevronDown size={15} aria-hidden="true" />
                </label>
            </div>

            {teams.length > 0 ? (
                <TeamChart
                    teams={teams}
                    overallAverage={data.overallAverageDays}
                    selectedStage={data.selectedStage}
                />
            ) : (
                <div className="hn-team-comparison__empty">No valid onboarding-day values were found for this stage.</div>
            )}

        </section>
    );
}
