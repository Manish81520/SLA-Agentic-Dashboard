import React, { forwardRef } from "react";

/**
 * AppleGlassButton — a frosted-glass pill button inspired by Apple's design language.
 */
export const AppleGlassButton = forwardRef(
    ({ children, icon, size = "md", className, disabled, style, ...props }, ref) => {
        const sizeMap = {
            sm: { padding: "0.45rem 1.35rem 0.45rem 0.45rem", gap: "0.65rem", fontSize: "0.855rem", iconSize: "1.75rem" },
            md: { padding: "0.62rem 1.8rem 0.62rem 0.62rem", gap: "0.85rem", fontSize: "0.97rem", iconSize: "2.25rem" },
            lg: { padding: "0.8rem 2.2rem 0.8rem 0.8rem", gap: "1.1rem", fontSize: "1.07rem", iconSize: "2.6rem" },
        };

        const { padding, gap, fontSize, iconSize } = sizeMap[size] ?? sizeMap.md;

        return (
            <button
                ref={ref}
                disabled={disabled}
                className={["agb", className].filter(Boolean).join(" ")}
                style={{
                    position: "relative",
                    display: "inline-flex",
                    alignItems: "center",
                    padding,
                    gap,
                    fontSize,
                    fontWeight: 590,
                    letterSpacing: "-0.012em",
                    color: "#1c2d3d",
                    background: "linear-gradient(160deg, rgba(255,255,255,0.84) 0%, rgba(236,244,251,0.70) 60%, rgba(220,234,247,0.74) 100%)",
                    border: "1px solid rgba(255,255,255,0.92)",
                    borderRadius: "999px",
                    boxShadow: [
                        "0 2px 1px rgba(255,255,255,0.95) inset",
                        "0 -1px 1px rgba(140,175,205,0.18) inset",
                        "0 8px 32px rgba(60,90,120,0.13)",
                        "0 1px 4px rgba(60,90,120,0.08)",
                    ].join(", "),
                    backdropFilter: "blur(28px) saturate(160%)",
                    WebkitBackdropFilter: "blur(28px) saturate(160%)",
                    cursor: disabled ? "not-allowed" : "pointer",
                    opacity: disabled ? 0.52 : 1,
                    transition: "transform 180ms cubic-bezier(.34,1.56,.64,1), box-shadow 200ms ease, background 200ms ease",
                    outline: "none",
                    textShadow: "0 1px 0 rgba(255,255,255,0.8)",
                    overflow: "hidden",
                    ...style,
                }}
                {...props}
            >
                {/* Shimmer highlight streak across the top half */}
                <span
                    aria-hidden="true"
                    style={{
                        position: "absolute",
                        top: 0,
                        left: "8%",
                        right: "8%",
                        height: "42%",
                        background: "linear-gradient(180deg, rgba(255,255,255,0.58) 0%, rgba(255,255,255,0) 100%)",
                        borderRadius: "0 0 50% 50%",
                        pointerEvents: "none",
                    }}
                />

                {/* Circular icon badge */}
                {icon && (
                    <span
                        style={{
                            position: "relative",
                            zIndex: 1,
                            display: "grid",
                            width: iconSize,
                            height: iconSize,
                            flexShrink: 0,
                            placeItems: "center",
                            borderRadius: "50%",
                            color: "#22394d",
                            background: "linear-gradient(145deg, rgba(255,255,255,0.92), rgba(228,240,250,0.76))",
                            border: "1px solid rgba(255,255,255,0.96)",
                            boxShadow: [
                                "0 1px 3px rgba(255,255,255,0.9) inset",
                                "0 4px 10px rgba(55,88,115,0.12)",
                            ].join(", "),
                        }}
                    >
                        {icon}
                    </span>
                )}

                {/* Vertical divider */}
                {icon && (
                    <span
                        aria-hidden="true"
                        style={{
                            position: "relative",
                            zIndex: 1,
                            width: 1,
                            height: "1.4rem",
                            background: "rgba(80,115,145,0.18)",
                            flexShrink: 0,
                        }}
                    />
                )}

                {/* Label */}
                <span style={{ position: "relative", zIndex: 1, whiteSpace: "nowrap" }}>
                    {children}
                </span>
            </button>
        );
    }
);

AppleGlassButton.displayName = "AppleGlassButton";
export default AppleGlassButton;
