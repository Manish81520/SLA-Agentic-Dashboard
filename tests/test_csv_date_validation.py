import tempfile
import unittest
from pathlib import Path

import pandas as pd

from Agents.ExcelAnalyst.data_cleaner import clean_dataframe
from Agents.ExcelAnalyst.tools import inspect_spreadsheet


class CsvDateValidationTests(unittest.TestCase):
    def test_inspector_rejects_ambiguous_csv_dates(self):
        with tempfile.TemporaryDirectory() as directory:
            csv_file = Path(directory) / "ambiguous.csv"
            csv_file.write_text(
                "Employee ID,Request Date\nE-100,06/06/2006\n",
                encoding="utf-8",
            )

            result = inspect_spreadsheet(str(csv_file))

        self.assertIn("error", result)
        self.assertIn("YYYY-MM-DD", result["error"])
        self.assertEqual(result["date_format_validation"]["issues"], [{
            "column": "Request Date",
            "csv_row": 2,
            "value": "06/06/2006",
            "reason": "Dates must be calendar-valid YYYY-MM-DD or YYYY/MM/DD.",
        }])

    def test_inspector_accepts_iso_csv_dates_and_canonicalizes_slashes(self):
        with tempfile.TemporaryDirectory() as directory:
            csv_file = Path(directory) / "iso.csv"
            csv_file.write_text(
                "Employee ID,Request Date\nE-100,2006/06/06\n",
                encoding="utf-8",
            )

            result = inspect_spreadsheet(str(csv_file))

        self.assertNotIn("error", result)
        self.assertEqual(result["preview_rows"][0]["Request Date"], "2006-06-06")

    def test_cleaner_does_not_infer_non_iso_date_order(self):
        cleaned, report = clean_dataframe(pd.DataFrame({"Request Date": ["06/06/2006"]}))

        self.assertEqual(cleaned.loc[0, "Request Date"], "06/06/2006")
        self.assertEqual(report["columns_skipped_date_parse"], ["Request Date"])
