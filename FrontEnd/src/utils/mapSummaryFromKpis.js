export function mapSummaryFromKpis(kpis = {}) {
    return {
        totalPartners: kpis.totalCandidates ?? kpis.totalRecords ?? 0,
        minDays: kpis.minTotalOnboardingDays ?? kpis.minimumTotalDuration ?? null,
        maxDays: kpis.maxTotalOnboardingDays ?? kpis.maximumTotalDuration ?? null,
        avgDays: kpis.avgTotalOnboardingDays ?? kpis.averageTotalDuration ?? null,
        totalAnomalies: kpis.totalAnomalies ?? 0,
        groupCount: kpis.projectGroups ?? kpis.groupCount ?? 0,
    };
}

export function mapSummaryFromCalculations(payload) {
    const calculations = payload?.calculations || payload || {};
    return {
        summary: mapSummaryFromKpis(calculations.kpis),
        filename: calculations.dataset?.filename || "Uploaded dataset",
        records: calculations.records || [],
    };
}
