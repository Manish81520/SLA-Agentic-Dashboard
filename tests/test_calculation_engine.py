import unittest
from datetime import date

import pandas as pd

from Backend.calculations import calculate_dataset, calculate_partners_list, calculate_team_comparison


AGENT_MAPPING = {
    "identifier_mapping": {"column": "Worker ID"},
    "partner_name_mapping": {"column": "Partner Name"},
    "project_mapping": {"column": "Delivery Team"},
    "onboarding_start_mapping": {"column": "Request Date"},
    "onboarding_completion_mapping": {"column": "Completion Date"},
    "stages": [
        {
            "stage_name": "Verification",
            "duration_mapping": {"column": "Verification SLA"},
            "start_mapping": {"column": "Verification Start"},
            "end_mapping": {"column": "Verification End"},
        },
        {
            "stage_name": "Provisioning",
            "duration_mapping": None,
            "start_mapping": {"column": "Provisioning Start"},
            "end_mapping": {"column": "Provisioning End"},
        },
    ],
}


class CalculationEngineTests(unittest.TestCase):
    def test_calculates_mapped_durations_aggregates_anomalies_and_forecasts(self):
        dataframe = pd.DataFrame({
            "Worker ID": ["W-1", "W-2", "W-3"],
            "Partner Name": ["Ava Patel", "Noah Smith", "Mia Chen"],
            "Delivery Team": ["Alpha", "Alpha", "Beta"],
            "Request Date": ["2026-01-01", "2026-01-01", "2026-01-01"],
            "Completion Date": ["2026-01-10", "", "2026-01-09"],
            "Verification SLA": [2, 4, 8],
            "Verification Start": ["2026-01-01", "2026-01-01", "2026-01-01"],
            "Verification End": ["2026-01-03", "2026-01-05", "2026-01-09"],
            "Provisioning Start": ["2026-01-03", "2026-01-05", "2026-01-09"],
            "Provisioning End": ["2026-01-05", "2026-01-08", "2026-01-13"],
            "Optional Field": [None, "available", None],
        })

        result = calculate_dataset(dataframe, AGENT_MAPPING, analysis_date=date(2026, 1, 10))

        self.assertEqual(result["kpis"]["totalRecords"], 3)
        self.assertEqual(result["kpis"]["groupCount"], 2)
        self.assertEqual(result["stages"][0]["average"], 5)
        self.assertEqual(result["stages"][1]["average"], 3)
        self.assertEqual(result["byGroup"][0]["group"], "Alpha")
        self.assertEqual(result["byGroup"][0]["Verification"], 3)
        self.assertEqual(result["anomalyWatchlist"][0]["recordId"], "W-3")
        self.assertEqual(result["focusAreas"][0]["recordId"], "W-2")
        self.assertEqual(result["records"][1]["forecast"]["currentStage"], "Provisioning")
        self.assertEqual(result["records"][1]["forecast"]["status"], "at_risk")
        self.assertEqual(result["records"][0]["stages"][1]["source"], "derived_from_dates")

    def test_handles_missing_fields_invalid_values_and_filters_without_hardcoded_headers(self):
        dataframe = pd.DataFrame({
            "Ticket": ["A", "B", "C"],
            "Squad": ["One", "Two", "Two"],
            "Effort Days": ["3", "not-a-number", "400"],
            "Category": ["Internal", "External", "External"],
        })
        mapping = {
            "identifier_mapping": {"column": "Ticket"},
            "project_mapping": {"column": "Squad"},
            "stages": [{"stage_name": "Work", "duration_mapping": {"column": "Effort Days"}}],
        }

        result = calculate_dataset(dataframe, mapping, filters={"Squad": "Two"})

        self.assertEqual(result["kpis"]["totalRecords"], 2)
        self.assertEqual(result["stages"][0]["trackedCount"], 0)
        self.assertEqual(result["stages"][0]["dataQuality"]["invalid_numeric"], 1)
        self.assertEqual(result["stages"][0]["dataQuality"]["outside_plausible_range"], 1)
        self.assertEqual(result["kpis"]["dataQualityIssues"], 2)
        self.assertIn("Category", result["filters"])
        self.assertEqual(result["records"][0]["recordId"], "B")

    def test_handles_invalid_dates_negative_durations_and_zero_average_without_crashing(self):
        dataframe = pd.DataFrame({
            "Case ID": ["1", "2", "3"],
            "Started": ["2026-01-01", "not-a-date", "2026-01-10"],
            "Finished": ["2026-01-01", "2026-01-04", "2026-01-08"],
        })
        mapping = {
            "identifier_mapping": {"column": "Case ID"},
            "stages": [{
                "stage_name": "Review",
                "start_mapping": {"column": "Started"},
                "end_mapping": {"column": "Finished"},
            }],
        }

        result = calculate_dataset(dataframe, mapping)

        self.assertEqual(result["stages"][0]["trackedCount"], 1)
        self.assertEqual(result["stages"][0]["average"], 0)
        self.assertEqual(result["stages"][0]["dataQuality"]["invalid_date"], 1)
        self.assertEqual(result["stages"][0]["dataQuality"]["outside_plausible_range"], 1)
        self.assertEqual(result["focusAreas"], [])

    def test_team_comparison_uses_dynamic_stage_team_and_partner_mappings(self):
        dataframe = pd.DataFrame({
            "Worker ID": ["W-1", "W-2", "W-3"],
            "Partner Name": ["Ava Patel", "Noah Smith", "Mia Chen"],
            "Delivery Team": ["Alpha", "Alpha", "Beta"],
            "Verification SLA": [2, 4, 8],
            "Provisioning Start": ["2026-01-01", "2026-01-01", "2026-01-01"],
            "Provisioning End": ["2026-01-02", "2026-01-04", "2026-01-07"],
        })

        comparison = calculate_team_comparison(dataframe, AGENT_MAPPING, "Provisioning")

        self.assertEqual(comparison["selectedStage"], "Provisioning")
        self.assertEqual(comparison["overallAverageDays"], 3.3)
        self.assertEqual(
            comparison["teams"],
            [
                {"team": "Alpha", "averageOnboardingDays": 2.0, "partnerCount": 2},
                {"team": "Beta", "averageOnboardingDays": 6.0, "partnerCount": 1},
            ],
        )
        self.assertEqual(comparison["focusArea"]["summary"]["partnersNeedingAttention"], 2)
        self.assertEqual(comparison["focusArea"]["summary"]["potentialAnomalies"], 1)
        self.assertEqual(comparison["focusArea"]["partners"][0]["partnerName"], "Mia Chen")
        self.assertEqual(comparison["focusArea"]["partners"][0]["stuckAtStage"], "Provisioning")
        self.assertTrue(comparison["focusArea"]["partners"][0]["isAnomaly"])

        with self.assertRaisesRegex(ValueError, "requested stage"):
            calculate_team_comparison(dataframe, AGENT_MAPPING, "Missing stage")

    def test_team_comparison_does_not_substitute_identifier_for_missing_partner_name(self):
        dataframe = pd.DataFrame({
            "Worker ID": ["internal-1", "internal-2"],
            "Delivery Team": ["Alpha", "Beta"],
            "Verification SLA": [4, 8],
        })
        mapping_without_names = {key: value for key, value in AGENT_MAPPING.items() if key != "partner_name_mapping"}

        comparison = calculate_team_comparison(dataframe, mapping_without_names, "Verification")

        self.assertEqual(comparison["focusArea"]["partners"], [])
        self.assertEqual(comparison["focusArea"]["summary"]["missingPartnerNames"], 1)

    def test_calculate_partners_list_returns_all_partners_with_standardized_fields(self):
        dataframe = pd.DataFrame({
            "Worker ID": ["W-1", "W-2", "W-3"],
            "Partner Name": ["Ava Patel", "Noah Smith", "Mia Chen"],
            "Delivery Team": ["Alpha", "Alpha", "Beta"],
            "Request Date": ["2026-01-01", "2026-01-01", "2026-01-01"],
            "Completion Date": ["2026-01-10", "", "2026-01-09"],
            "Verification SLA": [2, 4, 8],
            "Verification Start": ["2026-01-01", "2026-01-01", "2026-01-01"],
            "Verification End": ["2026-01-03", "2026-01-05", "2026-01-09"],
            "Provisioning Start": ["2026-01-03", "2026-01-05", "2026-01-09"],
            "Provisioning End": ["2026-01-05", "2026-01-08", "2026-01-13"],
        })

        result = calculate_partners_list(dataframe, AGENT_MAPPING, analysis_date=date(2026, 1, 10))

        self.assertEqual(result["totalCount"], 3)
        self.assertEqual(len(result["partners"]), 3)

        # Sorted alphabetically by partnerName: Ava Patel, Mia Chen, Noah Smith
        p0 = result["partners"][0]
        self.assertEqual(p0["partnerName"], "Ava Patel")
        self.assertEqual(p0["team"], "Alpha")
        self.assertEqual(p0["currentStage"], "Completed")
        self.assertEqual(p0["onboardingDays"], 9.0)
        self.assertEqual(p0["status"], "Completed")

        p1 = result["partners"][1]
        self.assertEqual(p1["partnerName"], "Mia Chen")
        self.assertEqual(p1["team"], "Beta")
        self.assertEqual(p1["currentStage"], "Completed")
        self.assertEqual(p1["onboardingDays"], 8.0)
        self.assertEqual(p1["status"], "Completed")

        p2 = result["partners"][2]
        self.assertEqual(p2["partnerName"], "Noah Smith")
        self.assertEqual(p2["team"], "Alpha")
        self.assertEqual(p2["currentStage"], "Provisioning")
        self.assertEqual(p2["onboardingDays"], 9.0)
        self.assertEqual(p2["status"], "In progress")

