import React, { useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
    DashboardHero,
    DashboardToast,
    EmptyDatasetBanner,
    ErrorBanner,
    FocusAreaSection,
    HomeNavBar,
    PartnersListSection,
    PipelineSection,

    SearchFeedback,
    SummaryCards,
    TeamComparisonSection,
} from "../components/home";
import { useAutoDismiss } from "../hooks/useAutoDismiss";
import { useDashboardData } from "../hooks/useDashboardData";
import { exportDatasetCsv } from "../utils/csvExport";
import "./HomePage.css";

export default function HomePage() {
    const navigate = useNavigate();
    const {
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
    } = useDashboardData();


    useAutoDismiss(toast, dismissToast);

    const handleUpload = useCallback(() => navigate("/upload"), [navigate]);
    const handleManage = useCallback(() => navigate("/partners/manage"), [navigate]);
    const handleExport = useCallback(() => {
        exportDatasetCsv(records, datasetInfo, summary);
    }, [records, datasetInfo, summary]);

    return (
        <div className="hn-page">
            <HomeNavBar
                searchQuery={searchQuery}
                onSearchChange={setSearchQuery}
                onUpload={handleUpload}
                onExport={handleExport}
                onManage={handleManage}
                hasData={records.length > 0}
            />

            <DashboardToast toast={toast} onDismiss={dismissToast} />

            <main className="hn-main" id="main-content">
                <DashboardHero
                    datasetLoaded={datasetLoaded}
                    datasetInfo={datasetInfo}
                    loading={loading}
                />

                {!loading && !datasetLoaded && (
                    <EmptyDatasetBanner onUpload={handleUpload} />
                )}

                {error && (
                    <ErrorBanner
                        message={`Could not connect to backend analysis: ${error}`}
                        onRetry={loadSummary}
                    />
                )}

                {datasetLoaded && (
                    <SearchFeedback
                        query={searchQuery}
                        matchCount={filteredRecords.length}
                        totalCount={summary?.totalPartners ?? 0}
                    />
                )}

                <SummaryCards
                    displayMetrics={displayMetrics}
                    searchQuery={searchQuery}
                    loading={loading}
                />

                <PipelineSection
                    data={pipelineData}
                    loading={pipelineLoading}
                    error={pipelineError}
                    onRetry={loadPipeline}
                    datasetLoaded={datasetLoaded}
                />

                <TeamComparisonSection
                    data={teamComparison}
                    loading={teamComparisonLoading}
                    error={teamComparisonError}
                    onRetry={() => loadTeamComparison(teamComparison?.selectedStage)}
                    onStageChange={loadTeamComparison}
                    datasetLoaded={datasetLoaded}
                />

                <FocusAreaSection />

                <PartnersListSection
                    data={partnersData}
                    loading={partnersLoading}
                    error={partnersError}
                    onRetry={loadPartners}
                    datasetLoaded={datasetLoaded}
                />
            </main>

        </div>
    );
}
