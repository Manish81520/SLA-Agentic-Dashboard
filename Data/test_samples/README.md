# Spreadsheet interpretation fixtures

These CSV files exercise different schema-inference cases without changing the
default `Data/onboarding.csv` sample.

- `candidate_standard.csv`: clear candidate lifecycle and ISO dates.
- `partner_alternative_headers.csv`: different entity, stage names, and headers.
- `ambiguous_date_formats.csv`: date-stage fixture normalized to ISO-style
  date values; invalid-format validation is covered by the automated tests.
- `incomplete_mappings.csv`: missing completion fields that require confirmation.

They are inputs for `inspect_spreadsheet(file_path=...)` and later ADK evals.
