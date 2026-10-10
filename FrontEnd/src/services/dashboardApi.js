const SUMMARY_URL = "/api/summary";
const PIPELINE_URL = "/api/pipeline";
const TEAM_COMPARISON_URL = "/api/team-comparison";
const FOCUS_AREA_URL = "/api/focus-area";
const PARTNERS_URL = "/api/partners";
const PARTNER_SCHEMA_URL = "/api/partners/schema";
const PARTNER_ROWS_URL = "/api/partners/rows";
const PARTNERS_WRITE_URL = "/api/partners";
const NETWORK_MESSAGE = "The API could not be reached. Confirm that the backend is running on port 8000.";

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

export function fetchPartners() {
    return fetchJson(PARTNERS_URL);
}

export class ApiError extends Error {
    constructor(message, status = 0, fieldErrors = {}) { super(message); this.name = "ApiError"; this.status = status; this.fieldErrors = fieldErrors; }
}
async function sendJson(url, method, body) {
    let response;
    try { response = await fetch(url, { method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }); }
    catch { throw new ApiError(NETWORK_MESSAGE, 0); }
    const payload = (response.headers.get("content-type") || "").includes("application/json") ? await response.json() : {};
    if (response.ok) return payload;
    if (typeof payload.detail === "string") throw new ApiError(payload.detail, response.status);
    if (payload.detail && typeof payload.detail === "object") throw new ApiError(payload.detail.message || "The request was not valid.", response.status, payload.detail.fieldErrors || {});
    throw new ApiError("The request was not valid.", response.status);
}
export function fetchPartnerSchema() { return fetchJson(PARTNER_SCHEMA_URL); }
export function fetchPartnerRows() { return fetchJson(PARTNER_ROWS_URL); }
export function createPartner(fields) { return sendJson(PARTNERS_WRITE_URL, "POST", { fields }); }
export function updatePartner(rowId, fields) { return sendJson(`${PARTNERS_WRITE_URL}/${rowId}`, "PATCH", { fields }); }
