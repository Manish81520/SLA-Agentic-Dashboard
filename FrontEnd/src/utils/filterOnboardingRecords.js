export function filterOnboardingRecords(records, searchQuery) {
    if (!searchQuery.trim() || !records.length) return records;
    const query = searchQuery.toLowerCase().trim();
    return records.filter((record) => {
        const id = String(record.recordId || "").toLowerCase();
        const group = String(record.group || "").toLowerCase();
        const fields = Object.values(record.fields || {}).join(" ").toLowerCase();
        return id.includes(query) || group.includes(query) || fields.includes(query);
    });
}

export function getDisplayMetrics(summary, searchQuery, filteredRecords) {
    if (!summary) return null;
    if (!searchQuery.trim()) return summary;
    return {
        ...summary,
        totalPartners: filteredRecords.length,
    };
}
