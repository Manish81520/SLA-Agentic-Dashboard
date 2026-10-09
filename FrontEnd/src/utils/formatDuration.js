export function formatDays(value) {
    return value == null ? "—" : `${Number(value).toFixed(1)} days`;
}

export function formatDaysShort(value) {
    return value == null ? "\u2014" : `${Number(value).toFixed(1)} d`;
}

export function formatDayDifference(value) {
    if (value == null) return "—";
    return `${value > 0 ? "+" : ""}${Number(value).toFixed(1)} days`;
}

export function formatAverageDays(value) {
    return value == null ? "—" : Number(value).toFixed(1);
}
