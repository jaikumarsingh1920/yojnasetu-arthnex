import sqlite3
import os
import sys

def migrate_database():
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(backend_dir, "app", "yojnasetu.db")
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    print(f"Connecting to database at {db_path}...")
    con = sqlite3.connect(db_path)
    cur = con.cursor()

    # 1. Update schemes table
    cur.execute("PRAGMA table_info(schemes)")
    scheme_cols = [c[1] for c in cur.fetchall()]

    if "updated_at" not in scheme_cols:
        print("Adding updated_at column to schemes...")
        cur.execute("ALTER TABLE schemes ADD COLUMN updated_at DATETIME;")
        con.commit()
    else:
        print("updated_at column already exists in schemes.")

    # 2. Ensure all existing schemes have scheme_status = 'ACTIVE'
    print("Normalizing scheme_status for all canonical schemes...")
    cur.execute("UPDATE schemes SET scheme_status = 'ACTIVE' WHERE scheme_status IS NULL OR scheme_status = '';")
    con.commit()

    # 3. Update scheme_changelogs table
    cur.execute("PRAGMA table_info(scheme_changelogs)")
    log_cols = [c[1] for c in cur.fetchall()]

    if "action" not in log_cols:
        print("Adding action column to scheme_changelogs...")
        cur.execute("ALTER TABLE scheme_changelogs ADD COLUMN action VARCHAR(50) DEFAULT 'UPDATE';")
        con.commit()
    else:
        print("action column already exists in scheme_changelogs.")

    if "admin_identifier" not in log_cols:
        print("Adding admin_identifier column to scheme_changelogs...")
        cur.execute("ALTER TABLE scheme_changelogs ADD COLUMN admin_identifier VARCHAR(255);")
        con.commit()
    else:
        print("admin_identifier column already exists in scheme_changelogs.")

    # Verify counts
    cur.execute("SELECT count(*) FROM schemes WHERE scheme_status = 'ACTIVE'")
    active_count = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM schemes")
    total_count = cur.fetchone()[0]
    print(f"Migration completed successfully! Total schemes: {total_count}, Active schemes: {active_count}")

    con.close()

if __name__ == "__main__":
    migrate_database()
