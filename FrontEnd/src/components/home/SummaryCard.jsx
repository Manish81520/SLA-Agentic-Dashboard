import React from "react";

export function SummaryCard({ id, icon: Icon, label, value, unit, accent, loading }) {
    return (
        <article className={`hn-card hn-card--${accent}`} id={id}>
            <div className="hn-card__icon-wrap" aria-hidden="true">
                <Icon size={18} strokeWidth={1.8} />
            </div>
            <div className="hn-card__body">
                <p className="hn-card__label">{label}</p>
                <p className="hn-card__value">
                    {loading ? (
                        <span className="hn-skeleton" aria-hidden="true" />
                    ) : value != null ? (
                        <>
                            {Number(value).toLocaleString()}
                            {unit && <span className="hn-card__unit">{unit}</span>}
                        </>
                    ) : (
                        <span className="hn-card__empty">—</span>
                    )}
                </p>
            </div>
        </article>
    );
}
