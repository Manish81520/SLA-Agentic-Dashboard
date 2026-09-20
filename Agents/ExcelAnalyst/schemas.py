"""Structured, reviewable output contracts for the ExcelAnalyst agent."""

from typing import List, Optional

from pydantic import BaseModel, Field


class ColumnMapping(BaseModel):
    """A proposed semantic-to-source-column mapping made by the agent."""

    column: Optional[str] = Field(
        default=None,
        description="Exact cleaned column header from the supplied metadata, or null when no reliable mapping exists",
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in this mapping from 0.0 (no confidence) to 1.0 (very high confidence)",
    )
    rationale: str = Field(
        description="Brief evidence for the mapping, based only on the supplied headers, samples, types, and statistics",
    )


class DateFormatAmbiguity(BaseModel):
    """A date-column parsing concern the user may need to confirm."""

    column: str = Field(description="Exact cleaned date column header")
    observed_formats: List[str] = Field(
        default_factory=list,
        description="Date format patterns observed in samples, for example DD/MM/YYYY or YYYY-MM-DD",
    )
    suggested_format: Optional[str] = Field(
        default=None,
        description="Safest proposed parsing format, or null when no safe default can be proposed",
    )
    requires_confirmation: bool = Field(
        description="True when dates could be interpreted in more than one way",
    )
    note: str = Field(description="Concise explanation of the ambiguity or parsing risk")


class ConfirmationRequirement(BaseModel):
    """A mapping or parsing decision that must be reviewed before calculations."""

    field_path: str = Field(
        description="Path in this response requiring review, for example stages[0].end_mapping",
    )
    candidate_columns: List[str] = Field(
        default_factory=list,
        description="Exact source-column candidates the user can choose from",
    )
    reason: str = Field(description="Why this decision cannot be safely automated")


class OnboardingStage(BaseModel):
    """A proposed onboarding milestone with explicit, reviewable source mappings."""

    stage_name: str = Field(
        description="Descriptive name of the onboarding stage or milestone",
    )
    start_mapping: Optional[ColumnMapping] = Field(
        default=None,
        description="Mapping to the exact column that starts this stage",
    )
    end_mapping: Optional[ColumnMapping] = Field(
        default=None,
        description="Mapping to the exact column that completes this stage",
    )
    duration_mapping: Optional[ColumnMapping] = Field(
        default=None,
        description="Mapping to an existing numeric duration/SLA-value column, if the source provides one",
    )
    description: Optional[str] = Field(
        default=None,
        description="Summary of what is tracked in this stage",
    )


class DatasetUnderstanding(BaseModel):
    """The stable configuration bridge between dynamic spreadsheets and the backend."""

    dataset_summary: str = Field(description="High-level description of the dataset")
    entity_type: str = Field(description="Type of entity being onboarded")
    identifier_mapping: ColumnMapping = Field(
        description="Proposed primary identifier-column mapping",
    )
    project_mapping: Optional[ColumnMapping] = Field(
        default=None,
        description="Proposed project, team, or account-assignment column mapping",
    )
    detected_project_name: Optional[str] = Field(
        default=None,
        description="Specific project name(s) identified in column names or data",
    )
    onboarding_start_mapping: Optional[ColumnMapping] = Field(
        default=None,
        description="Proposed mapping for the overall onboarding initiation date",
    )
    onboarding_completion_mapping: Optional[ColumnMapping] = Field(
        default=None,
        description="Proposed mapping for the overall onboarding completion date",
    )
    stages: List[OnboardingStage] = Field(
        default_factory=list,
        description="Detected onboarding stages in logical chronological sequence",
    )
    date_column_mappings: List[ColumnMapping] = Field(
        default_factory=list,
        description="All identified date/timestamp columns with confidence and rationale",
    )
    date_format_ambiguities: List[DateFormatAmbiguity] = Field(
        default_factory=list,
        description="Date-format ambiguity and parsing-risk notes",
    )
    columns_requiring_confirmation: List[ConfirmationRequirement] = Field(
        default_factory=list,
        description="Mappings or date decisions that must be reviewed before calculations",
    )
