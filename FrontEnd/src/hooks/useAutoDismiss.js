import { useEffect } from "react";

export function useAutoDismiss(value, onDismiss, delayMs = 6000) {
    useEffect(() => {
        if (!value) return undefined;
        const timer = setTimeout(onDismiss, delayMs);
        return () => clearTimeout(timer);
    }, [value, onDismiss, delayMs]);
}
