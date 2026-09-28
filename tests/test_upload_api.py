import io
import unittest
from pathlib import Path

from fastapi import HTTPException, UploadFile

from Backend.main import MAX_UPLOAD_SIZE_BYTES, process_csv_upload


class UploadApiTests(unittest.IsolatedAsyncioTestCase):
    async def test_process_csv_upload_returns_agent_response(self):
        received_path = None

        async def fake_agent_runner(file_path):
            nonlocal received_path
            received_path = file_path
            with open(file_path, encoding="utf-8") as uploaded_file:
                self.assertEqual(uploaded_file.read(), "Employee ID,Request Date\nE-1,2026-01-01\n")
            return {"entity_type": "employee"}

        upload = UploadFile(
            filename="onboarding.csv",
            file=io.BytesIO(b"Employee ID,Request Date\nE-1,2026-01-01\n"),
        )
        result = await process_csv_upload(upload, fake_agent_runner)

        self.assertEqual(result, {"entity_type": "employee"})
        self.assertIsNotNone(received_path)
        self.assertFalse(Path(received_path).exists())

    async def test_process_csv_upload_rejects_non_csv_files(self):
        upload = UploadFile(filename="onboarding.txt", file=io.BytesIO(b"hello"))
        with self.assertRaises(HTTPException) as context:
            await process_csv_upload(upload)
        self.assertEqual(context.exception.status_code, 400)

    async def test_process_csv_upload_rejects_oversized_files(self):
        upload = UploadFile(
            filename="onboarding.csv",
            file=io.BytesIO(b"a" * (MAX_UPLOAD_SIZE_BYTES + 1)),
        )
        with self.assertRaises(HTTPException) as context:
            await process_csv_upload(upload)
        self.assertEqual(context.exception.status_code, 413)

    async def test_process_csv_upload_returns_a_safe_error_for_agent_failure(self):
        async def failing_agent_runner(file_path):
            raise ConnectionError("Gemini is unavailable")

        upload = UploadFile(filename="onboarding.csv", file=io.BytesIO(b"Employee ID\nE-1\n"))
        with self.assertRaises(HTTPException) as context:
            await process_csv_upload(upload, failing_agent_runner)

        self.assertEqual(context.exception.status_code, 500)
        self.assertEqual(context.exception.detail, "ExcelAnalyst could not process the uploaded CSV.")
