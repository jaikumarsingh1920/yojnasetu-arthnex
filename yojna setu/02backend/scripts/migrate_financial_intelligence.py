import os
import sys

# Ensure backend dir is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.db.session import engine, DEFAULT_DB_FILE
from app.db.base_class import Base
from app.models.financial_intelligence import (
    InstitutionEntity,
    InstitutionAlias,
    PartnerFinancialObservation,
    PrudentialRule,
)
import sqlite3

def run_migration():
    print(f"Creating tables in database bound to engine (target: {DEFAULT_DB_FILE})...")
    Base.metadata.create_all(bind=engine)
    
    # Verify tables in DEFAULT_DB_FILE
    conn = sqlite3.connect(DEFAULT_DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('institution_entities', 'institution_aliases', 'partner_financial_observations', 'prudential_rules')")
    tables = [r[0] for r in cur.fetchall()]
    print(f"Created tables in {DEFAULT_DB_FILE}: {tables}")
    conn.close()

    # Also check if root yojnasetu.db exists and sync tables if needed
    root_db = os.path.join(BASE_DIR, "yojnasetu.db")
    if os.path.exists(root_db) and root_db != DEFAULT_DB_FILE:
        conn2 = sqlite3.connect(root_db)
        cur2 = conn2.cursor()
        cur2.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('institution_entities', 'institution_aliases', 'partner_financial_observations', 'prudential_rules')")
        tables2 = [r[0] for r in cur2.fetchall()]
        print(f"Tables in root {root_db}: {tables2}")
        conn2.close()

if __name__ == "__main__":
    run_migration()
