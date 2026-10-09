import React from "react";

export function SearchFeedback({ query, matchCount, totalCount }) {
    if (!query.trim()) return null;

    return (
        <div className="hn-search-feedback">
            Showing <strong>{matchCount}</strong> of{" "}
            <strong>{totalCount}</strong> partners matching &ldquo;{query}&rdquo;
        </div>
    );
}
