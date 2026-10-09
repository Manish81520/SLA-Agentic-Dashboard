import React from "react";
import { CheckCircle2, X } from "lucide-react";

export function DashboardToast({ toast, onDismiss }) {
    if (!toast) return null;

    return (
        <div className="hn-toast-container">
            <div className="hn-toast" role="status" aria-live="polite">
                <CheckCircle2 size={16} className="hn-toast__icon" />
                <span className="hn-toast__msg">{toast.message}</span>
                <button
                    type="button"
                    className="hn-toast__close"
                    onClick={onDismiss}
                    aria-label="Dismiss message"
                >
                    <X size={12} strokeWidth={2.5} />
                </button>
            </div>
        </div>
    );
}
