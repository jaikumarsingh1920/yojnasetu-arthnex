"""
Database migration script to add canonical channel partner and mapping columns.
Applies ALTER TABLE safely and idempotently to:
- 02backend/app/yojnasetu.db
- 02backend/yojnasetu.db
- 04data/scripts/yojnasetu.db
"""

import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE_ROOT = os.path.dirname(BASE_DIR)

DATABASES = [
    os.path.join(BASE_DIR, "app", "yojnasetu.db"),
    os.path.join(BASE_DIR, "yojnasetu.db"),
    os.path.join(WORKSPACE_ROOT, "04data", "scripts", "yojnasetu.db")
]

PARTNER_COLUMNS = [
    ("institution_type", "VARCHAR(100)"),
    ("partner_category", "VARCHAR(100) DEFAULT 'AUTHORIZED_SCHEME_PARTNER'"),
    ("address", "VARCHAR(500)"),
    ("district", "VARCHAR(100)"),
    ("state", "VARCHAR(100)"),
    ("pincode", "VARCHAR(20)"),
    ("phone", "VARCHAR(100)"),
    ("email", "VARCHAR(100)"),
    ("website", "VARCHAR(255)"),
    ("service_type", "VARCHAR(100)"),
    ("last_verified_date", "VARCHAR(50)"),
    ("scheme_authorization_level", "VARCHAR(100)"),
    ("coordinates_status", "VARCHAR(50) DEFAULT 'VERIFIED'")
]

MAPPING_COLUMNS = [
    ("service_type", "VARCHAR(100)"),
    ("authorization_level", "VARCHAR(100) DEFAULT 'SCHEME_ROUTE_VERIFIED'"),
    ("last_verified_date", "VARCHAR(50)")
]

def migrate():
    for db_path in DATABASES:
        if not os.path.exists(db_path):
            print(f"Skipping {db_path} (does not exist)")
            continue
        
        print(f"Migrating schema for {db_path}...")
        con = sqlite3.connect(db_path)
        cur = con.cursor()

        # 1. Partner columns
        cur.execute("PRAGMA table_info(partners)")
        existing_partner_cols = {row[1] for row in cur.fetchall()}

        for col_name, col_type in PARTNER_COLUMNS:
            if col_name not in existing_partner_cols:
                sql = f"ALTER TABLE partners ADD COLUMN {col_name} {col_type}"
                try:
                    cur.execute(sql)
                    print(f"  Added partners.{col_name}")
                except Exception as e:
                    print(f"  Error adding partners.{col_name}: {e}")

        # 2. Partner scheme mappings columns
        cur.execute("PRAGMA table_info(partner_scheme_mappings)")
        existing_mapping_cols = {row[1] for row in cur.fetchall()}

        for col_name, col_type in MAPPING_COLUMNS:
            if col_name not in existing_mapping_cols:
                sql = f"ALTER TABLE partner_scheme_mappings ADD COLUMN {col_name} {col_type}"
                try:
                    cur.execute(sql)
                    print(f"  Added partner_scheme_mappings.{col_name}")
                except Exception as e:
                    print(f"  Error adding partner_scheme_mappings.{col_name}: {e}")

        con.commit()
        con.close()
        print(f"Migration completed for {db_path}")

if __name__ == "__main__":
    migrate()
