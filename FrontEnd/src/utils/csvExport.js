function escapeCsv(value) {
    if (value == null) return "";
    const text = String(value).replace(/"/g, '""');
    return /[",\n]/.test(text) ? `"${text}"` : text;
}

function downloadCsv(content, filename) {
    const blob = new Blob([content], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

function exportRecordsCsv(records, datasetInfo) {
    const fieldKeys = Array.from(
        new Set(records.flatMap((record) => Object.keys(record.fields || {}))),
    );
    const headers = ["Record ID", "Group", "Is Complete", ...fieldKeys];
    const rows = records.map((record) => [
        escapeCsv(record.recordId),
        escapeCsv(record.group),
        escapeCsv(record.isComplete ? "Yes" : "No"),
        ...fieldKeys.map((key) => escapeCsv(record.fields?.[key] ?? "")),
    ]);
    const csvContent = [headers.join(","), ...rows.map((row) => row.join(","))].join("\n");
    const baseName = (datasetInfo || "onboarding_analysis").replace(/\.[^/.]+$/, "");
    downloadCsv(csvContent, `${baseName}_export.csv`);
}

function exportSummaryCsv(summary) {
    const summaryRows = [
        ["Metric", "Value"],
        ["Total Partners Onboarded", summary.totalPartners ?? 0],
        ["Minimum Onboarding Days", summary.minDays ?? ""],
        ["Maximum Onboarding Days", summary.maxDays ?? ""],
        ["Average Onboarding Days", summary.avgDays ?? ""],
    ];
    downloadCsv(summaryRows.map((row) => row.join(",")).join("\n"), "onboarding_summary.csv");
}

export function exportDatasetCsv(records, datasetInfo, summary) {
    if (records && records.length > 0) {
        exportRecordsCsv(records, datasetInfo);
        return;
    }
    if (summary) {
        exportSummaryCsv(summary);
    }
}
