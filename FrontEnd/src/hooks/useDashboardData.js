import { useCallback, useEffect, useMemo, useState } from "react";
import { useLocation } from "react-router-dom";
import { fetchPartners, fetchPipeline, fetchSummary, fetchTeamComparison } from "../services/dashboardApi";
import { filterOnboardingRecords, getDisplayMetrics } from "../utils/filterOnboardingRecords";
import { mapSummaryFromCalculations, mapSummaryFromKpis } from "../utils/mapSummaryFromKpis";


function emptyDatasetState() {
    return {
        summary: null,
        records: [],
        datasetInfo: null,
        datasetLoaded: false,
    };
}

export function useDashboardData() {
    const location = useLocation();

    const [summary, setSummary] = useState(null);
    const [records, setRecords] = useState([]);
    const [datasetInfo, setDatasetInfo] = useState(null);
    const [datasetLoaded, setDatasetLoaded] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [toast, setToast] = useState(null);
    const [searchQuery, setSearchQuery] = useState("");
    const [pipelineData, setPipelineData] = useState(null);
    const [pipelineLoading, setPipelineLoading] = useState(true);
    const [pipelineError, setPipelineError] = useState(null);
    const [teamComparison, setTeamComparison] = useState(null);
    const [teamComparisonLoading, setTeamComparisonLoading] = useState(true);
    const [teamComparisonError, setTeamComparisonError] = useState(null);
    const [partnersData, setPartnersData] = useState(null);
    const [partnersLoading, setPartnersLoading] = useState(true);
    const [partnersError, setPartnersError] = useState(null);

    const applyLoadedDataset = useCallback((nextSummary, filename, nextRecords) => {
        setSummary(nextSummary);
        setDatasetInfo(filename);
        setRecords(nextRecords);
        setDatasetLoaded(true);
        setError(null);
    }, []);

    const applyEmptyDataset = useCallback(() => {
        const empty = emptyDatasetState();
        setSummary(empty.summary);
        setRecords(empty.records);
        setDatasetInfo(empty.datasetInfo);
        setDatasetLoaded(empty.datasetLoaded);
        setPartnersData(null);
    }, []);


    const loadSummary = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await fetchSummary();
            if (data == null) {
                applyEmptyDataset();
                return;
            }
            applyLoadedDataset(
                mapSummaryFromKpis(data.kpis),
                data.dataset?.filename || "Uploaded dataset",
                data.records || [],
            );
        } catch (err) {
            console.error("Failed to load summary from backend:", err);
            setError(err.message || "Failed to load summary");
        } finally {
            setLoading(false);
        }
    }, [applyEmptyDataset, applyLoadedDataset]);

    const loadPipeline = useCallback(async () => {
        setPipelineLoading(true);
        setPipelineError(null);
        try {
            setPipelineData(await fetchPipeline());
        } catch (err) {
            console.error("Failed to load pipeline from backend:", err);
            setPipelineError(err.message || "Failed to load pipeline");
        } finally {
            setPipelineLoading(false);
        }
    }, []);

    const loadTeamComparison = useCallback(async (stage) => {
        setTeamComparisonLoading(true);
        setTeamComparisonError(null);
        try {
            setTeamComparison(await fetchTeamComparison(stage));
        } catch (err) {
            console.error("Failed to load team comparison:", err);
            setTeamComparisonError(err.message || "Failed to load team comparison");
        } finally {
            setTeamComparisonLoading(false);
        }
    }, []);

    const loadPartners = useCallback(async () => {
        setPartnersLoading(true);
        setPartnersError(null);
        try {
            setPartnersData(await fetchPartners());
        } catch (err) {
            console.error("Failed to load partners:", err);
            setPartnersError(err.message || "Failed to load partners");
        } finally {
            setPartnersLoading(false);
        }
    }, []);

    useEffect(() => {
        if (location.state?.uploaded && location.state?.response) {
            const mapped = mapSummaryFromCalculations(location.state.response);
            const filename = location.state.filename || mapped.filename;
            applyLoadedDataset(mapped.summary, filename, mapped.records);
            setLoading(false);
            setToast({
                message: `Analysis complete: ${filename} processed successfully`,
                type: "success",
            });
            loadPipeline();
            loadTeamComparison();
            loadPartners();
            window.history.replaceState({}, document.title);
            return;
        }

        loadSummary();
        loadPipeline();
        loadTeamComparison();
        loadPartners();
    }, [location.state, loadSummary, loadPipeline, loadTeamComparison, loadPartners, applyLoadedDataset]);

    const filteredRecords = useMemo(
        () => filterOnboardingRecords(records, searchQuery),
        [records, searchQuery],
    );

    const displayMetrics = useMemo(
        () => getDisplayMetrics(summary, searchQuery, filteredRecords),
        [summary, searchQuery, filteredRecords],
    );

    const dismissToast = useCallback(() => setToast(null), []);

    return {
        summary,
        records,
        datasetInfo,
        datasetLoaded,
        loading,
        error,
        toast,
        searchQuery,
        setSearchQuery,
        displayMetrics,
        filteredRecords,
        pipelineData,
        pipelineLoading,
        pipelineError,
        teamComparison,
        teamComparisonLoading,
        teamComparisonError,
        partnersData,
        partnersLoading,
        partnersError,
        loadSummary,
        loadPipeline,
        loadTeamComparison,
        loadPartners,
        dismissToast,
    };
}
