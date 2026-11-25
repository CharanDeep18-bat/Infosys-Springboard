"""Unit tests for File Storage Abstraction (Local & Supabase Storage).

Validates:
1. LocalFileStorage operations (save, retrieve, delete, exists, health check).
2. SupabaseStorage operations with simulated HTTP responses.
3. Strict error propagation on upload failure (never reports success if remote fails).
4. Storage factory respects STORAGE_PROVIDER configuration ('local' vs 'supabase').
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.infrastructure.storage import LocalFileStorage, get_file_storage, reset_file_storage
from app.infrastructure.storage.supabase_storage import SupabaseStorage


class TestStorageLayer(unittest.TestCase):
    """Test suite for Local and Supabase storage implementations."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.upload_dir = Path(self.temp_dir.name)
        reset_file_storage()

    def tearDown(self):
        reset_file_storage()
        self.temp_dir.cleanup()

    # -------------------------------------------------------------------------
    # Local Storage Tests
    # -------------------------------------------------------------------------

    def test_local_storage_lifecycle(self):
        """Test complete save, retrieve, check, and delete lifecycle for LocalFileStorage."""
        storage = LocalFileStorage(upload_dir=str(self.upload_dir))
        doc_id = "test_doc_001"
        sample_bytes = b"%PDF-1.4 sample pdf content for local storage"

        # 1. Save
        saved_path = storage.save_file(sample_bytes, "report.pdf", doc_id)
        self.assertTrue(saved_path.is_file())
        self.assertEqual(saved_path.read_bytes(), sample_bytes)

        # 2. Exists
        self.assertTrue(storage.file_exists(doc_id))
        self.assertFalse(storage.file_exists("non_existent_doc"))

        # 3. Retrieve bytes
        retrieved_bytes = storage.get_file_bytes(doc_id)
        self.assertEqual(retrieved_bytes, sample_bytes)

        # 4. Health Check
        health = storage.check_health()
        self.assertTrue(health["healthy"])
        self.assertEqual(health["provider"], "local")

        # 5. Delete
        self.assertTrue(storage.delete_file(doc_id))
        self.assertFalse(storage.file_exists(doc_id))
        self.assertFalse(saved_path.exists())

    # -------------------------------------------------------------------------
    # Supabase Storage Tests
    # -------------------------------------------------------------------------

    def test_supabase_storage_health_unconfigured(self):
        """SupabaseStorage must report unhealthy when credentials are missing."""
        storage = SupabaseStorage(
            bucket_name="financial-documents",
            supabase_url="",
            supabase_key="",
            cache_dir=str(self.upload_dir),
        )
        health = storage.check_health()
        self.assertFalse(health["healthy"])
        self.assertIn("not configured", health.get("error", ""))

    @patch("httpx.Client")
    def test_supabase_storage_health_probe_success(self, mock_client_cls):
        """SupabaseStorage health probe succeeds when bucket is accessible via REST."""
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"name": "financial-documents", "public": False}
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        storage = SupabaseStorage(
            bucket_name="financial-documents",
            supabase_url="https://test.supabase.co",
            supabase_key="test-key",
            cache_dir=str(self.upload_dir),
        )
        health = storage.check_health()
        self.assertTrue(health["healthy"])
        self.assertEqual(health["bucket"], "financial-documents")
        self.assertEqual(health["status"], "connected_to_private_bucket")

    @patch("httpx.Client")
    def test_supabase_storage_upload_failure_raises_runtime_error(self, mock_client_cls):
        """CRITICAL: Supabase upload must raise RuntimeError if upload fails; never report success."""
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error in Supabase Storage"
        mock_client.__enter__.return_value = mock_client
        mock_client.post.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        storage = SupabaseStorage(
            bucket_name="financial-documents",
            supabase_url="https://test.supabase.co",
            supabase_key="test-key",
            cache_dir=str(self.upload_dir),
        )
        storage._sdk_client = None  # Ensure REST path is exercised

        sample_bytes = b"%PDF-1.4 test payload"
        with self.assertRaises(RuntimeError) as ctx:
            storage.save_file(sample_bytes, "test.pdf", "doc_fail_1")

        self.assertIn("Failed to upload document to Supabase Storage", str(ctx.exception))
        # Ensure file was not staged into permanent cache on failure
        self.assertFalse((self.upload_dir / "doc_fail_1.pdf").exists())

    @patch("httpx.Client")
    def test_supabase_storage_successful_upload_and_download(self, mock_client_cls):
        """Supabase upload and download round-trip via native REST."""
        sample_bytes = b"%PDF-1.4 authentic pdf content"

        mock_client = MagicMock()
        upload_resp = MagicMock(status_code=200, json=lambda: {"Key": "doc_success.pdf"})
        download_resp = MagicMock(status_code=200, content=sample_bytes)

        mock_client.__enter__.return_value = mock_client
        mock_client.post.return_value = upload_resp
        mock_client.get.return_value = download_resp
        mock_client_cls.return_value = mock_client

        storage = SupabaseStorage(
            bucket_name="financial-documents",
            supabase_url="https://test.supabase.co",
            supabase_key="test-key",
            cache_dir=str(self.upload_dir),
        )
        storage._sdk_client = None

        # 1. Save
        cached_path = storage.save_file(sample_bytes, "doc_success.pdf", "doc_success")
        self.assertTrue(cached_path.is_file())

        # 2. Retrieve without cache (delete local file to force network download)
        cached_path.unlink()
        downloaded = storage.get_file_bytes("doc_success")
        self.assertEqual(downloaded, sample_bytes)

    # -------------------------------------------------------------------------
    # Factory & Configuration Tests
    # -------------------------------------------------------------------------

    def test_factory_returns_local_storage(self):
        """get_file_storage() returns LocalFileStorage when STORAGE_PROVIDER=local."""
        with patch("app.config.get_settings") as mock_settings:
            mock_settings.return_value.storage_provider = "local"
            mock_settings.return_value.upload_dir = self.upload_dir

            reset_file_storage()
            storage = get_file_storage()
            self.assertIsInstance(storage, LocalFileStorage)
            self.assertEqual(storage.get_storage_provider(), "local")

    def test_factory_returns_supabase_storage(self):
        """get_file_storage() returns SupabaseStorage when STORAGE_PROVIDER=supabase."""
        with patch("app.config.get_settings") as mock_settings:
            mock_settings.return_value.storage_provider = "supabase"
            mock_settings.return_value.supabase_url = "https://example.supabase.co"
            mock_settings.return_value.supabase_key = "secret_key"
            mock_settings.return_value.supabase_storage_bucket = "financial-documents"
            mock_settings.return_value.upload_dir = self.upload_dir

            reset_file_storage()
            storage = get_file_storage()
            self.assertIsInstance(storage, SupabaseStorage)
            self.assertEqual(storage.get_storage_provider(), "supabase")


if __name__ == "__main__":
    unittest.main()
