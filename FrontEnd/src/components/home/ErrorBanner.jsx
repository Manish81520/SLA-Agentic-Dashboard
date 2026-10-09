import React from "react";
import { RefreshCw } from "lucide-react";

export function ErrorBanner({ message, onRetry }) {
    return (
        <div className="hn-error-banner" role="alert">
            <span>{message}</span>
            {onRetry && (
                <button type="button" className="hn-retry-btn" onClick={onRetry}>
                    <RefreshCw size={13} />
                    <span>Retry</span>
                </button>
            )}
        </div>
    );
}
