const SUMMARY_URL = "/api/summary";
const PIPELINE_URL = "/api/pipeline";
const TEAM_COMPARISON_URL = "/api/team-comparison";
const FOCUS_AREA_URL = "/api/focus-area";

async function fetchJson(url) {
    const response = await fetch(url);
    if (response.status === 404) {
        return null;
    }
    if (!response.ok) {
        throw new Error(`Server returned status ${response.status}`);
    }
    return response.json();
}

export function fetchSummary() {
    return fetchJson(SUMMARY_URL);
}

export function fetchPipeline() {
    return fetchJson(PIPELINE_URL);
}

export function fetchTeamComparison(stage) {
    const query = stage ? `?${new URLSearchParams({ stage }).toString()}` : "";
    return fetchJson(`${TEAM_COMPARISON_URL}${query}`);
}

export function fetchFocusArea() {
    return fetchJson(FOCUS_AREA_URL);
}
