"""Repository operations for persisted datasets and partner rows."""

from dataclasses import dataclass
from datetime import datetime, timezone
import math
import threading
from typing import Any

import pandas as pd
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from Backend.calculations.configuration import configuration_from_agent
from Backend.calculations.normalization import _is_missing, json_value
from Backend.db.models import Dataset, DatasetMapping, PartnerRow
from Backend.db.session import db_generation


WRITE_LOCK = threading.Lock()
_CACHE_LOCK = threading.Lock()
_CACHE: dict[tuple[int, int, int], "LoadedDataset"] = {}
M_DUPUP = "Duplicate identifiers found: {identifiers}. Each partner needs a unique identifier — fix the CSV and upload again."


@dataclass
class LoadedDataset:
    """The active persisted dataset in calculation-ready form."""

    dataset_id: int
    revision: int
    filename: str
    columns: list[str]
    dataframe: pd.DataFrame
    agent_response: dict
    rows: dict[int, dict]


class NoActiveDataset(Exception):
    """Raised when there is no active uploaded dataset."""


def to_storable(value: Any) -> Any:
    """Convert a dataframe value to the JSON representation used for storage."""
    converted = json_value(value)
    if isinstance(converted, float) and math.isfinite(converted) and converted.is_integer():
        return int(converted)
    return converted


def identifier_norm_of(value: Any) -> str | None:
    """Return the normalized identifier or None for a blank value."""
    if _is_missing(value):
        return None
    return str(value).strip().casefold()


def rows_to_dataframe(columns: list[str], row_ids: list[int], datas: list[dict]) -> pd.DataFrame:
    """Build the calculation dataframe with database row IDs as its index."""
    return pd.DataFrame(list(datas), columns=columns, index=list(row_ids))


def create_dataset(session: Session, filename: str, dataframe: pd.DataFrame, agent_response: dict) -> int:
    """Persist an upload, making it the sole active dataset."""
    configuration = configuration_from_agent(agent_response)
    identifier_column = configuration.identifier_column
    norms: list[str | None] = []
    if identifier_column in dataframe.columns:
        norms = [identifier_norm_of(value) for value in dataframe[identifier_column].tolist()]
        seen: set[str] = set()
        duplicate_values: list[str] = []
        duplicate_seen: set[str] = set()
        for value, norm in zip(dataframe[identifier_column].tolist(), norms):
            if norm is not None and norm in seen and norm not in duplicate_seen:
                duplicate_values.append(str(value).strip())
                duplicate_seen.add(norm)
            if norm is not None:
                seen.add(norm)
        if duplicate_values:
            shown = duplicate_values[:5]
            suffix = f" and {len(duplicate_values) - 5} more" if len(duplicate_values) > 5 else ""
            raise ValueError(M_DUPUP.format(identifiers=", ".join(shown) + suffix))
    else:
        norms = [None] * len(dataframe)

    session.execute(update(Dataset).values(is_active=False))
    dataset = Dataset(filename=filename, columns=list(dataframe.columns), is_active=True, revision=1)
    session.add(dataset)
    session.flush()
    session.add(DatasetMapping(dataset_id=dataset.id, agent_response=agent_response))
    now = datetime.now(timezone.utc)
    for position, ((_, row), norm) in enumerate(zip(dataframe.iterrows(), norms), start=1):
        data = {column: to_storable(row[column]) for column in dataframe.columns}
        session.add(PartnerRow(dataset_id=dataset.id, position=position, identifier_norm=norm, data=data, updated_at=now))
    return dataset.id


def get_active_dataset(session: Session) -> Dataset | None:
    """Return the current active dataset, if any."""
    return session.scalar(select(Dataset).where(Dataset.is_active.is_(True)))


def load_active(session: Session) -> LoadedDataset:
    """Load and cache the active dataset in calculation-ready form."""
    dataset = get_active_dataset(session)
    if dataset is None:
        raise NoActiveDataset()
    key = (db_generation(), dataset.id, dataset.revision)
    with _CACHE_LOCK:
        cached = _CACHE.get(key)
        if cached is not None:
            return cached

    mapping = session.scalar(select(DatasetMapping).where(DatasetMapping.dataset_id == dataset.id))
    partner_rows = list(session.scalars(
        select(PartnerRow).where(PartnerRow.dataset_id == dataset.id).order_by(PartnerRow.position)
    ))
    row_ids = [row.id for row in partner_rows]
    datas = [dict(row.data) for row in partner_rows]
    loaded = LoadedDataset(
        dataset_id=dataset.id,
        revision=dataset.revision,
        filename=dataset.filename,
        columns=list(dataset.columns),
        dataframe=rows_to_dataframe(list(dataset.columns), row_ids, datas),
        agent_response=dict(mapping.agent_response) if mapping is not None else {},
        rows=dict(zip(row_ids, datas)),
    )
    with _CACHE_LOCK:
        for cache_key in list(_CACHE):
            if cache_key[1] == dataset.id and cache_key != key:
                del _CACHE[cache_key]
        _CACHE[key] = loaded
    return loaded


def get_row(session: Session, dataset_id: int, row_id: int) -> PartnerRow | None:
    """Return a row only when it belongs to the active dataset."""
    return session.scalar(select(PartnerRow).where(PartnerRow.dataset_id == dataset_id, PartnerRow.id == row_id))


def identifier_exists(session: Session, dataset_id: int, norm: str, exclude_row_id: int | None = None) -> bool:
    """Check whether a normalized identifier already exists in a dataset."""
    statement = select(PartnerRow.id).where(PartnerRow.dataset_id == dataset_id, PartnerRow.identifier_norm == norm)
    if exclude_row_id is not None:
        statement = statement.where(PartnerRow.id != exclude_row_id)
    return session.scalar(statement) is not None


def insert_row(session: Session, dataset_id: int, data: dict, norm: str | None) -> PartnerRow:
    """Insert one partner after the existing source-order rows."""
    position = (session.scalar(select(func.max(PartnerRow.position)).where(PartnerRow.dataset_id == dataset_id)) or 0) + 1
    row = PartnerRow(dataset_id=dataset_id, position=position, identifier_norm=norm, data=dict(data), updated_at=datetime.now(timezone.utc))
    session.add(row)
    session.flush()
    return row


def update_row(session: Session, row: PartnerRow, data: dict) -> None:
    """Replace a row's stored data with a new dictionary."""
    row.data = dict(data)
    row.updated_at = datetime.now(timezone.utc)
    session.flush()


def bump_revision(session: Session, dataset_id: int) -> int:
    """Increase and return the dataset revision after a row write."""
    dataset = session.get(Dataset, dataset_id)
    assert dataset is not None
    dataset.revision += 1
    session.flush()
    return dataset.revision
