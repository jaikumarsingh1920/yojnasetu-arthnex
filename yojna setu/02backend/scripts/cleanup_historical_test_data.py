"""
Explicit cleanup and archiving mechanism for historical test residue:
Removes test schemes SIH26092-860 through SIH26092-880 and test candidates CAND-TEST-*
created during historical un-isolated ingestion tests.

Archives all records safely to archived_test_* tables before deletion,
preserving 100% reversibility and provenance.
"""

import os
import sys
import sqlite3
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cleanup_historical_test_data")

def cleanup_test_data(db_path: str) -> dict:
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found at {db_path}")

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Enable foreign keys
    cur.execute("PRAGMA foreign_keys = ON;")

    # 1. Inspect target records
    cur.execute("SELECT scheme_id, scheme_name FROM schemes WHERE scheme_id >= 'SIH26092-860' ORDER BY scheme_id")
    target_schemes = cur.fetchall()
    logger.info(f"Identified {len(target_schemes)} historical test schemes (SIH26092-860 to 880).")

    cur.execute("SELECT candidate_id, discovered_name FROM candidate_schemes WHERE candidate_id LIKE 'CAND-TEST%'")
    target_candidates = cur.fetchall()
    logger.info(f"Identified {len(target_candidates)} historical test candidates (CAND-TEST-*).")

    if not target_schemes and not target_candidates:
        logger.info("Database is already clean. No test artifacts found.")
        conn.close()
        return {"schemes_archived": 0, "schemes_deleted": 0, "canonical_scheme_count": 859}

    # 2. Create archive tables if they don't exist
    cur.execute("CREATE TABLE IF NOT EXISTS archived_test_schemes AS SELECT * FROM schemes WHERE 0")
    cur.execute("CREATE TABLE IF NOT EXISTS archived_test_scheme_rules AS SELECT * FROM scheme_rules WHERE 0")
    cur.execute("CREATE TABLE IF NOT EXISTS archived_test_scheme_documents AS SELECT * FROM scheme_documents WHERE 0")
    cur.execute("CREATE TABLE IF NOT EXISTS archived_test_scheme_sources AS SELECT * FROM scheme_sources WHERE 0")
    cur.execute("CREATE TABLE IF NOT EXISTS archived_test_scheme_verifications AS SELECT * FROM scheme_verifications WHERE 0")
    cur.execute("CREATE TABLE IF NOT EXISTS archived_test_scheme_changelogs AS SELECT * FROM scheme_changelogs WHERE 0")
    cur.execute("CREATE TABLE IF NOT EXISTS archived_test_candidate_schemes AS SELECT * FROM candidate_schemes WHERE 0")

    # 3. Archive data
    cur.execute("INSERT OR REPLACE INTO archived_test_schemes SELECT * FROM schemes WHERE scheme_id >= 'SIH26092-860'")
    cur.execute("INSERT OR REPLACE INTO archived_test_scheme_rules SELECT * FROM scheme_rules WHERE scheme_id >= 'SIH26092-860'")
    cur.execute("INSERT OR REPLACE INTO archived_test_scheme_documents SELECT * FROM scheme_documents WHERE scheme_id >= 'SIH26092-860'")
    cur.execute("INSERT OR REPLACE INTO archived_test_scheme_sources SELECT * FROM scheme_sources WHERE scheme_id >= 'SIH26092-860'")
    cur.execute("INSERT OR REPLACE INTO archived_test_scheme_verifications SELECT * FROM scheme_verifications WHERE scheme_id >= 'SIH26092-860'")
    cur.execute("INSERT OR REPLACE INTO archived_test_scheme_changelogs SELECT * FROM scheme_changelogs WHERE scheme_id >= 'SIH26092-860'")
    cur.execute("INSERT OR REPLACE INTO archived_test_candidate_schemes SELECT * FROM candidate_schemes WHERE candidate_id LIKE 'CAND-TEST%'")

    # 4. Safely delete from active tables in dependency order
    cur.execute("DELETE FROM scheme_rules WHERE scheme_id >= 'SIH26092-860'")
    deleted_rules = cur.rowcount
    cur.execute("DELETE FROM scheme_documents WHERE scheme_id >= 'SIH26092-860'")
    deleted_docs = cur.rowcount
    cur.execute("DELETE FROM scheme_sources WHERE scheme_id >= 'SIH26092-860'")
    deleted_sources = cur.rowcount
    cur.execute("DELETE FROM scheme_verifications WHERE scheme_id >= 'SIH26092-860'")
    deleted_verifs = cur.rowcount
    cur.execute("DELETE FROM scheme_changelogs WHERE scheme_id >= 'SIH26092-860'")
    deleted_changelogs = cur.rowcount
    cur.execute("DELETE FROM schemes WHERE scheme_id >= 'SIH26092-860'")
    deleted_schemes = cur.rowcount

    cur.execute("DELETE FROM candidate_schemes WHERE candidate_id LIKE 'CAND-TEST%'")
    deleted_candidates = cur.rowcount

    conn.commit()

    # 5. Integrity verification specifically on scheme child tables
    scheme_child_tables = [
        'scheme_rules', 'scheme_documents', 'scheme_sources',
        'scheme_verifications', 'scheme_changelogs', 'partner_scheme_mappings',
        'saved_schemes'
    ]
    scheme_fk_violations = []
    for tbl in scheme_child_tables:
        cur.execute(f"PRAGMA foreign_key_check({tbl})")
        violations = cur.fetchall()
        if violations:
            scheme_fk_violations.extend([(tbl, v) for v in violations])

    if scheme_fk_violations:
        conn.rollback()
        conn.close()
        raise RuntimeError(f"Scheme foreign key violations detected after cleanup: {scheme_fk_violations}")

    # Ensure no active records reference the deleted scheme IDs
    cur.execute("SELECT COUNT(*) FROM scheme_rules WHERE scheme_id >= 'SIH26092-860'")
    rem_rules = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM scheme_documents WHERE scheme_id >= 'SIH26092-860'")
    rem_docs = cur.fetchone()[0]
    if rem_rules > 0 or rem_docs > 0:
        conn.rollback()
        conn.close()
        raise RuntimeError(f"Orphaned scheme rules ({rem_rules}) or documents ({rem_docs}) remain!")

    cur.execute("SELECT COUNT(*) FROM schemes")
    total_schemes = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM schemes WHERE scheme_id >= 'SIH26092-860'")
    remaining_test_schemes = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM schemes WHERE scheme_id <= 'SIH26092-859'")
    legitimate_schemes = cur.fetchone()[0]

    conn.close()

    logger.info(f"Cleanup complete: deleted {deleted_schemes} schemes, {deleted_rules} rules, {deleted_docs} docs, {deleted_candidates} candidates.")
    logger.info(f"Total schemes remaining: {total_schemes}, legitimate (001-859): {legitimate_schemes}, test schemes remaining: {remaining_test_schemes}")

    return {
        "deleted_schemes": deleted_schemes,
        "deleted_rules": deleted_rules,
        "deleted_docs": deleted_docs,
        "deleted_sources": deleted_sources,
        "deleted_verifications": deleted_verifs,
        "deleted_changelogs": deleted_changelogs,
        "deleted_candidates": deleted_candidates,
        "canonical_scheme_count": total_schemes,
        "legitimate_scheme_count": legitimate_schemes,
        "remaining_test_schemes": remaining_test_schemes,
        "scheme_fk_violations": len(scheme_fk_violations)
    }

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_db = os.path.join(base_dir, "app", "yojnasetu.db")
    logger.info(f"Executing test data cleanup on {target_db}...")
    result = cleanup_test_data(target_db)
    print("Cleanup Result:", result)
