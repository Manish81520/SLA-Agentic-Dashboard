import React, { useCallback, useEffect, useRef, useState } from "react";
import { Search, X } from "lucide-react";

export function ExpandingSearch({ value, onChange }) {
    const [open, setOpen] = useState(false);
    const inputRef = useRef(null);

    const openSearch = useCallback(() => {
        setOpen(true);
        requestAnimationFrame(() => inputRef.current?.focus());
    }, []);

    const closeSearch = useCallback(() => {
        if (!value) setOpen(false);
    }, [value]);

    const clearAndClose = useCallback(() => {
        onChange("");
        setOpen(false);
    }, [onChange]);

    useEffect(() => {
        if (!open) return undefined;
        const onKey = (event) => {
            if (event.key === "Escape") {
                clearAndClose();
            }
        };
        window.addEventListener("keydown", onKey);
        return () => window.removeEventListener("keydown", onKey);
    }, [open, clearAndClose]);

    return (
        <div className={`hn-search ${open ? "is-open" : ""}`} role="search">
            <button
                type="button"
                className="hn-search__trigger"
                aria-label="Open search"
                aria-expanded={open}
                onClick={openSearch}
                tabIndex={open ? -1 : 0}
            >
                <Search size={15} strokeWidth={2.2} />
            </button>

            <div className="hn-search__body" aria-hidden={!open}>
                <input
                    ref={inputRef}
                    id="hn-search-input"
                    type="search"
                    className="hn-search__input"
                    placeholder="Search partners, teams, IDs…"
                    value={value}
                    autoComplete="off"
                    tabIndex={open ? 0 : -1}
                    onBlur={closeSearch}
                    onChange={(event) => onChange(event.target.value)}
                    aria-label="Search partners"
                />
                {value && (
                    <button
                        type="button"
                        className="hn-search__clear"
                        aria-label="Clear search"
                        tabIndex={open ? 0 : -1}
                        onMouseDown={(event) => event.preventDefault()}
                        onClick={clearAndClose}
                    >
                        <X size={12} strokeWidth={2.8} />
                    </button>
                )}
            </div>
        </div>
    );
}
