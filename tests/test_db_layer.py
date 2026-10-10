"""Tests for the Phase 1 persistence layer."""

from datetime import date, datetime, timezone
import tempfile
import unittest

from sqlalchemy.exc import IntegrityError

from Backend.calculations import calculate_dataset, calculate_partners_list
from Backend.calculations.normalization import normalize_dataframe
from Backend.db import repository as repo
from Backend.db.models import PartnerRow
from Backend.db.session import init_db, session_scope
from fixtures import AGENT_MAPPING, fresh_db, make_dataframe


class DatabaseLayerTests(unittest.TestCase):
    def setUp(self):
        fresh_db()

    def _create(self, dataframe=None):
        with session_scope() as session:
            source = make_dataframe() if dataframe is None else dataframe
            return repo.create_dataset(session, "sample.csv", normalize_dataframe(source), AGENT_MAPPING)

    def test_round_trip_preserves_calculations(self):
        original = normalize_dataframe(make_dataframe())
        self._create(original)
        with session_scope() as session:
            loaded = repo.load_active(session)
        self.assertEqual(calculate_dataset(original, AGENT_MAPPING, analysis_date=date(2026, 1, 10)), calculate_dataset(loaded.dataframe, AGENT_MAPPING, analysis_date=date(2026, 1, 10)))

    def test_to_storable(self):
        self.assertEqual([repo.to_storable(value) for value in [7.0, 7.5, float("nan"), "x"]], [7, 7.5, None, "x"])

    def test_duplicate_upload_is_rejected(self):
        dataframe = make_dataframe()
        dataframe.loc[1, "Worker ID"] = "W-1"
        with self.assertRaisesRegex(ValueError, r"^Duplicate identifiers found: W-1\."):
            self._create(dataframe)

    def test_database_unique_identifier_constraint(self):
        dataset_id = self._create()
        with self.assertRaises(IntegrityError):
            with session_scope() as session:
                session.add(PartnerRow(dataset_id=dataset_id, position=10, identifier_norm="same", data={}, updated_at=datetime.now(timezone.utc)))
                session.add(PartnerRow(dataset_id=dataset_id, position=11, identifier_norm="same", data={}, updated_at=datetime.now(timezone.utc)))

    def test_null_identifiers_are_allowed(self):
        dataset_id = self._create()
        with session_scope() as session:
            session.add_all([PartnerRow(dataset_id=dataset_id, position=10, identifier_norm=None, data={}, updated_at=datetime.now(timezone.utc)), PartnerRow(dataset_id=dataset_id, position=11, identifier_norm=None, data={}, updated_at=datetime.now(timezone.utc))])

    def test_file_database_persists(self):
        with tempfile.TemporaryDirectory() as directory:
            url = f"sqlite:///{directory}/onboarding.db"
            init_db(url, create_tables=True)
            original = normalize_dataframe(make_dataframe())
            with session_scope() as session:
                repo.create_dataset(session, "sample.csv", original, AGENT_MAPPING)
            init_db(url)
            with session_scope() as session:
                loaded = repo.load_active(session)
            self.assertEqual(loaded.revision, 1)
            self.assertEqual(calculate_dataset(original, AGENT_MAPPING, analysis_date=date(2026, 1, 10)), calculate_dataset(loaded.dataframe, AGENT_MAPPING, analysis_date=date(2026, 1, 10)))

    def test_new_dataset_becomes_active(self):
        first = self._create()
        second = self._create()
        with session_scope() as session:
            self.assertFalse(session.get(repo.Dataset, first).is_active)
            self.assertTrue(session.get(repo.Dataset, second).is_active)
            self.assertEqual(repo.load_active(session).dataset_id, second)

    def test_cache_is_invalidated_by_revision(self):
        dataset_id = self._create()
        with session_scope() as session:
            first = repo.load_active(session)
            row = repo.get_row(session, dataset_id, next(iter(first.rows)))
            assert row is not None
            changed = dict(row.data)
            changed["Partner Name"] = "Updated"
            repo.update_row(session, row, changed)
            revision = repo.bump_revision(session, dataset_id)
            second = repo.load_active(session)
        self.assertEqual(second.revision, revision)
        self.assertEqual(second.dataframe.iloc[0]["Partner Name"], "Updated")

    def test_dataframe_has_stored_row_ids_and_columns(self):
        self._create()
        with session_scope() as session:
            loaded = repo.load_active(session)
        self.assertEqual(list(loaded.dataframe.index), list(loaded.rows))
        self.assertEqual(list(loaded.dataframe.columns), loaded.columns)

    def test_partner_rows_expose_database_row_ids(self):
        dataframe = make_dataframe()
        dataframe.index = [101, 102, 103]
        result = calculate_partners_list(dataframe, AGENT_MAPPING)
        self.assertTrue(all(isinstance(partner["rowId"], int) for partner in result["partners"]))
        self.assertEqual({partner["rowId"] for partner in result["partners"]}, {101, 102, 103})
