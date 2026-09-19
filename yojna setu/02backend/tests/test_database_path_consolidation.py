"""
Regression test suite asserting authoritative single canonical database path consolidation:
- Asserts DEFAULT_DB_FILE points strictly to 02backend/app/yojnasetu.db.
- Asserts obsolete duplicate DB (02backend/yojnasetu.db) does not exist as an active database.
- Asserts canonical database exists and contains the full legitimate dataset.
"""

import os
import sqlite3
import pytest
from app.core.config import DEFAULT_DB_FILE, BASE_DIR, settings

def test_canonical_db_path_resolution():
    expected_path = os.path.normpath(os.path.join(BASE_DIR, "yojnasetu.db"))
    actual_path = os.path.normpath(DEFAULT_DB_FILE)
    assert actual_path == expected_path, f"Expected {expected_path}, got {actual_path}"
    assert os.path.exists(DEFAULT_DB_FILE), f"Canonical DB file does not exist at {DEFAULT_DB_FILE}"

def test_obsolete_duplicate_db_not_active():
    backend_dir = os.path.dirname(BASE_DIR)
    obsolete_db_path = os.path.join(backend_dir, "yojnasetu.db")
    assert not os.path.exists(obsolete_db_path), f"Obsolete duplicate DB still exists at {obsolete_db_path}!"

def test_canonical_db_contains_expanded_dataset():
    conn = sqlite3.connect(DEFAULT_DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM schemes")
    count = cur.fetchone()[0]
    conn.close()
    assert count == 859, f"Canonical DB should have exactly 859 schemes, got {count}"
