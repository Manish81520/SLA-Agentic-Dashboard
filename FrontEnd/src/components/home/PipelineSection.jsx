import React, { useCallback, useState } from "react";
import { ChevronDown } from "lucide-react";
import { formatAverageDays, formatDaysShort } from "../../utils/formatDuration";
import { ErrorBanner } from "./ErrorBanner";

function PipelineHeader({ subtitle }) {
    return (
        <div className="hn-pipeline__header">
            <p className="hn-eyebrow">Pipeline</p>
            <h2 className="hn-pipeline__title">Onboarding Pipeline</h2>
            {subtitle && <p className="hn-pipeline__sub">{subtitle}</p>}
        </div>
    );
}

function PipelineConnector() {
    return (
        <div className="hn-pipeline__connector" aria-hidden="true">
            <span className="hn-pipeline__connector-line" />
            <span className="hn-pipeline__connector-node" />
        </div>
    );
}

function PipelineSkeleton() {
    return (
        <section className="hn-pipeline" aria-label="Onboarding Pipeline">
            <PipelineHeader subtitle="End-to-end milestone progression and substage duration tracking." />
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
                        {step < 3 && <PipelineConnector />}
                    </React.Fragment>
                ))}
            </div>
        </section>
    );
}

function PipelineSubstages({ stage, stageKey, isOpen, onToggle }) {
    const panelId = `hn-pipeline-panel-${stageKey}`;
    const subCount = stage.subStages ? stage.subStages.length : 0;

    return (
        <div className="hn-pipeline__substages">
            <button
                type="button"
                className="hn-pipeline__toggle"
                aria-expanded={isOpen}
                aria-controls={panelId}
                onClick={() => onToggle(stageKey)}
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
                            {stage.subStages.map((sub, index) => (
                                <li key={index} className="hn-pipeline__substage-item">
                                    <span className="hn-pipeline__substage-name" title={sub.label}>
                                        {sub.label}
                                    </span>
                                    <span className="hn-pipeline__substage-days">
                                        {formatDaysShort(sub.averageDays)}
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
}

function PipelineStageCard({ stage, index, expanded, onToggle }) {
    const stageKey = stage.id || String(index);
    const isOpen = expanded.has(stageKey);

    return (
        <article className="hn-pipeline__card" role="listitem">
            <div className="hn-pipeline__card-top">
                <span className="hn-pipeline__step-pill">
                    Step {String(stage.order ?? index + 1).padStart(2, "0")}
                </span>
                {stage.trackedCount > 0 && (
                    <span className="hn-pipeline__tracked">
                        {stage.trackedCount} tracked
                    </span>
                )}
            </div>

            <h3 className="hn-pipeline__stage-title">{stage.label}</h3>

            <div className="hn-pipeline__metric">
                <span className="hn-pipeline__metric-value">
                    {formatAverageDays(stage.averageDays)}
                </span>
                {stage.averageDays != null && (
                    <span className="hn-pipeline__metric-unit">days avg</span>
                )}
            </div>

            <PipelineSubstages
                stage={stage}
                stageKey={stageKey}
                isOpen={isOpen}
                onToggle={onToggle}
            />
        </article>
    );
}

function UnassignedSubstages({ unassigned }) {
    if (!unassigned?.subStages?.length) return null;

    return (
        <div className="hn-pipeline__unassigned">
            <div className="hn-pipeline__unassigned-header">
                <span className="hn-pipeline__unassigned-badge">Unassigned</span>
                <span className="hn-pipeline__unassigned-title">
                    Substages not mapped to a main pipeline phase ({unassigned.subStages.length})
                </span>
            </div>
            <ul className="hn-pipeline__unassigned-list">
                {unassigned.subStages.map((sub, index) => (
                    <li key={index} className="hn-pipeline__unassigned-item">
                        <span className="hn-pipeline__substage-name">{sub.label}</span>
                        <span className="hn-pipeline__substage-days">
                            {formatDaysShort(sub.averageDays)}
                        </span>
                    </li>
                ))}
            </ul>
        </div>
    );
}

export function PipelineSection({ data, loading, error, onRetry, datasetLoaded }) {
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
        return <PipelineSkeleton />;
    }

    if (error) {
        return (
            <section className="hn-pipeline" aria-label="Onboarding Pipeline">
                <PipelineHeader />
                <ErrorBanner message={`Could not load pipeline data: ${error}`} onRetry={onRetry} />
            </section>
        );
    }

    if (!datasetLoaded || !data || !data.mainStages || data.mainStages.length === 0) {
        return (
            <section className="hn-pipeline" aria-label="Onboarding Pipeline">
                <PipelineHeader subtitle="End-to-end milestone progression and substage duration tracking." />
                <div className="hn-pipeline__empty">
                    <p>No pipeline data available. Upload an onboarding spreadsheet to view stage breakdowns.</p>
                </div>
            </section>
        );
    }

    const { mainStages, unassigned } = data;

    return (
        <section className="hn-pipeline" aria-label="Onboarding Pipeline">
            <PipelineHeader subtitle="Chronological progression across key milestone phases and underlying substage durations." />

            <div className="hn-pipeline__track" role="list">
                {mainStages.map((stage, index) => (
                    <React.Fragment key={stage.id || index}>
                        <PipelineStageCard
                            stage={stage}
                            index={index}
                            expanded={expanded}
                            onToggle={toggleStage}
                        />
                        {index < mainStages.length - 1 && <PipelineConnector />}
                    </React.Fragment>
                ))}
            </div>

            <UnassignedSubstages unassigned={unassigned} />
        </section>
    );
}
