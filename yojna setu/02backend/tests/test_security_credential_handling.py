import os
import pytest
from app.core.config import Settings, settings
from app.services.ingestion.discovery_worker import get_myscheme_api_key, SchemeDiscoveryWorker
from app.db.session import SessionLocal


def test_myscheme_api_key_loaded_from_settings(monkeypatch):
    """Verify that MYSCHEME_API_KEY is retrieved exclusively from settings / environment."""
    monkeypatch.setenv("MYSCHEME_API_KEY", "test-mock-env-api-key")
    test_settings = Settings()
    assert test_settings.MYSCHEME_API_KEY == "test-mock-env-api-key"
    assert get_myscheme_api_key() == "test-mock-env-api-key"


def test_myscheme_api_key_missing_fails_safely(monkeypatch):
    """Verify that a missing API key fails safely with a clear ValueError."""
    monkeypatch.delenv("MYSCHEME_API_KEY", raising=False)
    monkeypatch.setattr(settings, "MYSCHEME_API_KEY", None)

    db = SessionLocal()
    try:
        worker = SchemeDiscoveryWorker(db)
        with pytest.raises(ValueError) as excinfo:
            worker.run_live_discovery(target_staged=1)
        assert "MYSCHEME_API_KEY is not configured" in str(excinfo.value)
    finally:
        db.close()


def test_source_code_has_no_hardcoded_myscheme_secret():
    """Verify that no hardcoded secret string exists in the discovery_worker file."""
    dw_path = os.path.join(os.path.dirname(__file__), "..", "app", "services", "ingestion", "discovery_worker.py")
    with open(dw_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "MYSCHEME_API_KEY = \"" not in content
    assert "MYSCHEME_API_KEY = '" not in content


def test_secret_value_never_emitted_in_logs_or_errors(monkeypatch, caplog):
    """Verify that a dummy secret key is never emitted in log records or error traces."""
    test_secret_val = "SECRET_CANARY_VALUE_123456789"
    monkeypatch.setenv("MYSCHEME_API_KEY", test_secret_val)
    monkeypatch.setattr(settings, "MYSCHEME_API_KEY", test_secret_val)

    db = SessionLocal()
    try:
        worker = SchemeDiscoveryWorker(db)
        with caplog.at_level("DEBUG"):
            caplog.clear()
            # Run batch discovery
            worker.run_discovery_batch(max_candidates=2, mock_fetch=True)

            # Also simulate a live discovery error where search triggers an exception
            class MockFailingClient:
                def __init__(self, *args, **kwargs):
                    pass
                def get(self, *args, **kwargs):
                    raise RuntimeError("Simulated network timeout for testing")

            monkeypatch.setattr("httpx.Client", MockFailingClient)
            try:
                worker.run_live_discovery(target_staged=1)
            except Exception as e:
                assert test_secret_val not in str(e)

        # Inspect all captured log text
        for record in caplog.records:
            assert test_secret_val not in record.getMessage()
            if record.exc_info:
                assert test_secret_val not in str(record.exc_info)
    finally:
        db.close()


def test_existing_discovery_functionality_with_injected_test_key(monkeypatch):
    """Verify that existing discovery worker functions properly when a key is injected via environment."""
    monkeypatch.setenv("MYSCHEME_API_KEY", "mock-injected-test-key-for-test-suite")
    monkeypatch.setattr(settings, "MYSCHEME_API_KEY", "mock-injected-test-key-for-test-suite")

    assert get_myscheme_api_key() == "mock-injected-test-key-for-test-suite"

    db = SessionLocal()
    try:
        worker = SchemeDiscoveryWorker(db)
        # Test discovery batch runs cleanly with injected key in environment
        res = worker.run_discovery_batch(max_candidates=2, mock_fetch=True)
        assert res is not None
        assert "total_discovered" in res
        assert res["total_discovered"] >= 0
    finally:
        db.close()


