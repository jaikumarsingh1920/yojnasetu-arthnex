import sqlite3
import shutil
import os
from datetime import datetime, timezone

DB_PATH = r"c:\Users\jaiku\OneDrive\Desktop\frontendredesign yojnasetu\yojnasetu-arthnex-main\yojna setu\02backend\app\yojnasetu.db"
BACKUP_PATH = r"c:\Users\jaiku\OneDrive\Desktop\frontendredesign yojnasetu\yojnasetu-arthnex-main\yojna setu\02backend\app\yojnasetu.db.pre_remediation_backup"
ARTIFACT_BACKUP = r"C:\Users\jaiku\.gemini\antigravity-ide\brain\919f4c41-7d34-4f60-a6f6-f53ec317f83d\yojnasetu.db.pre_remediation_backup"

def utc_now_str():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

def run_remediation():
    print("=================================================================")
    print("YOJNASETU PARTNER DATA REMEDIATION: PHASE 1, 6, 7, 8, 9, 10")
    print("=================================================================")

    # 1. Database Backup
    print(f"1. Creating backup of {DB_PATH}...")
    shutil.copy2(DB_PATH, BACKUP_PATH)
    shutil.copy2(DB_PATH, ARTIFACT_BACKUP)
    print(f"   -> Backup created at: {BACKUP_PATH}")
    print(f"   -> Artifact backup at: {ARTIFACT_BACKUP}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 2. Baseline Counts
    total_partners_pre = cur.execute("SELECT count(*) FROM partners").fetchone()[0]
    active_partners_pre = cur.execute("SELECT count(*) FROM partners WHERE is_active = 1").fetchone()[0]
    inactive_partners_pre = cur.execute("SELECT count(*) FROM partners WHERE is_active = 0").fetchone()[0]
    institutions_pre = cur.execute("SELECT count(*) FROM institution_entities").fetchone()[0]
    financial_obs_pre = cur.execute("SELECT count(*) FROM partner_financial_observations").fetchone()[0]
    scheme_mappings_pre = cur.execute("SELECT count(*) FROM partner_scheme_mappings").fetchone()[0]
    changelogs_pre = cur.execute("SELECT count(*) FROM partner_changelogs").fetchone()[0]

    print("\n--- BASELINE COUNTS ---")
    print(f"Total partner rows:             {total_partners_pre}")
    print(f"Active partners:                {active_partners_pre}")
    print(f"Inactive partners:              {inactive_partners_pre}")
    print(f"Canonical institutions:         {institutions_pre}")
    print(f"Financial observations:         {financial_obs_pre}")
    print(f"Scheme mappings:                {scheme_mappings_pre}")
    print(f"Changelog entries:              {changelogs_pre}")

    # 3. Add Quarantine Columns to 'partners' Table
    columns = [c[1] for c in cur.execute("PRAGMA table_info(partners)").fetchall()]
    
    if "record_status" not in columns:
        print("\nAdding 'record_status' column to partners...")
        cur.execute("ALTER TABLE partners ADD COLUMN record_status VARCHAR(50) DEFAULT 'ACTIVE'")
    if "validation_status" not in columns:
        print("Adding 'validation_status' column to partners...")
        cur.execute("ALTER TABLE partners ADD COLUMN validation_status VARCHAR(50) DEFAULT 'VALID'")
    if "quarantine_reason" not in columns:
        print("Adding 'quarantine_reason' column to partners...")
        cur.execute("ALTER TABLE partners ADD COLUMN quarantine_reason VARCHAR(500) DEFAULT NULL")
    if "nsfdc_authorized" not in columns:
        print("Adding 'nsfdc_authorized' column to partners...")
        cur.execute("ALTER TABLE partners ADD COLUMN nsfdc_authorized VARCHAR(50) DEFAULT 'UNKNOWN'")

    conn.commit()

    # Set default status for existing records based on is_active
    cur.execute("UPDATE partners SET record_status = 'ACTIVE' WHERE is_active = 1 AND record_status IS NULL")
    cur.execute("UPDATE partners SET record_status = 'INACTIVE' WHERE is_active = 0 AND record_status IS NULL")
    conn.commit()

    # 4. Quarantine Corrupted Records & Test Fixtures
    # 7 active corrupted records + 1 test fixture (PARTNER-001) + 5 inactive corrupted records
    corrupted_ids = {
        # Active corrupted address fragments
        '12401b23-5a1c-4bd3-b854-07ca88dab8bb': ("Mumbai  400 021", "PDF extraction/address parsing anomaly — institutional identity not verified"),
        'b42dba38-40a8-4665-8f50-eb44a8c91961': ("Ranchi- 834001", "PDF extraction/address parsing anomaly — institutional identity not verified"),
        '9381f6c7-d2d8-435e-a320-731879b5590e': ("Complex", "PDF extraction/address parsing anomaly — institutional identity not verified"),
        '83752b0f-14ca-4f50-86de-c8ca42c4e0e4': ("Tikiapara", "PDF extraction/address parsing anomaly — institutional identity not verified"),
        '20071c36-2fb4-4cb9-be0e-9dd1e8259e0f': ("Plot No.-47", "PDF extraction/address parsing anomaly — institutional identity not verified"),
        # Development test fixture committed to primary DB
        'PARTNER-001': ("National SC/ST Hub Channelizing Agency", "Test fixture committed to primary database — quarantined from production citizen routing"),
        # Historical inactive fragments
        'e3f483f0-bc9e-42db-80e4-6b98da3bd82a': ("State Channelizing Agency", "PDF extraction/address parsing anomaly — institutional identity not verified"),
        '57e84c56-60d2-404c-a044-44a5bc13fe33': ("Marg", "PDF extraction/address parsing anomaly — institutional identity not verified"),
        'f4eb3027-9e9d-4fe8-8500-3a0797432a10': ("Assam Pin  781 124", "PDF extraction/address parsing anomaly — institutional identity not verified"),
        '0472216a-139b-47ee-9778-4f7682685b0e': ("Sakar-II", "PDF extraction/address parsing anomaly — institutional identity not verified"),
        '5ab1922f-50c8-45e2-ab23-5751a8a951a7': ("Andhra Pradesh", "PDF extraction/address parsing anomaly — institutional identity not verified"),
    }

    print("\n--- QUARANTINING CORRUPTED RECORDS & TEST FIXTURES ---")
    ts = utc_now_str()
    for pid, (name, reason) in corrupted_ids.items():
        row = cur.execute("SELECT is_active, record_status FROM partners WHERE partner_id = ?", (pid,)).fetchone()
        if row:
            old_active = str(row['is_active'])
            old_status = str(row['record_status'] or 'ACTIVE')
            cur.execute("""
                UPDATE partners 
                SET is_active = 0, 
                    record_status = 'QUARANTINED', 
                    validation_status = 'PARSER_ANOMALY',
                    quarantine_reason = ?,
                    nsfdc_authorized = 'NOT_APPLICABLE'
                WHERE partner_id = ?
            """, (reason, pid))
            
            # Log in partner_changelogs
            cur.execute("""
                INSERT INTO partner_changelogs (partner_id, action, field, old_value, new_value, reason, admin_identifier, created_at)
                VALUES (?, 'QUARANTINE', 'record_status', ?, 'QUARANTINED', ?, 'system_remediation', ?)
            """, (pid, old_status, reason, ts))
            print(f"   [QUARANTINED] {pid} ('{name}') -> {reason[:55]}...")

    conn.commit()

    # 5. Duplicate Resolution: Punjab & Sind Bank
    # Head office with address: 6b8dc71e-28b2-47a6-8b9e-02a4c3bc94d7 (ACTIVE)
    # Duplicate with address NULL: ec68f3e7-43c5-4345-95a1-9e9cae1c08d9 (INACTIVE)
    dup_id = 'ec68f3e7-43c5-4345-95a1-9e9cae1c08d9'
    canonical_id = '6b8dc71e-28b2-47a6-8b9e-02a4c3bc94d7'
    dup_reason = f"Duplicate institutional record — canonical head office preserved under partner_id '{canonical_id}'"
    
    dup_row = cur.execute("SELECT is_active, record_status FROM partners WHERE partner_id = ?", (dup_id,)).fetchone()
    if dup_row and dup_row['is_active'] == 1:
        cur.execute("""
            UPDATE partners
            SET is_active = 0,
                record_status = 'INACTIVE',
                validation_status = 'DUPLICATE',
                quarantine_reason = ?,
                nsfdc_authorized = 'NOT_APPLICABLE'
            WHERE partner_id = ?
        """, (dup_reason, dup_id))

        cur.execute("""
            INSERT INTO partner_changelogs (partner_id, action, field, old_value, new_value, reason, admin_identifier, created_at)
            VALUES (?, 'DEACTIVATE_DUPLICATE', 'record_status', 'ACTIVE', 'INACTIVE', ?, 'system_remediation', ?)
        """, (dup_id, dup_reason, ts))
        print(f"\n   [DUPLICATE RESOLVED] Punjab & Sind Bank (NULL address, {dup_id}) marked INACTIVE.")
        print(f"   -> Canonical record preserved: {canonical_id} (5th Floor, 21 Rajendra Place, New Delhi).")

    conn.commit()

    # 6. Set NSFDC Authorization Semantics
    # A bank's existence in RBI data does NOT automatically imply NSFDC channel partner authorization.
    # Set nsfdc_authorized = 'AUTHORIZED' ONLY when confirmed by active scheme mappings in partner_scheme_mappings
    print("\n--- UPDATING NSFDC AUTHORIZATION SEMANTICS ---")
    cur.execute("""
        UPDATE partners 
        SET nsfdc_authorized = 'AUTHORIZED' 
        WHERE record_status = 'ACTIVE' 
          AND partner_id IN (
              SELECT DISTINCT partner_id 
              FROM partner_scheme_mappings 
              WHERE verification_status IN ('VERIFIED_OFFICIAL', 'VERIFIED')
          )
    """)
    cur.execute("""
        UPDATE partners 
        SET nsfdc_authorized = 'UNKNOWN' 
        WHERE record_status = 'ACTIVE' 
          AND nsfdc_authorized != 'AUTHORIZED'
    """)
    conn.commit()
    auth_count = cur.execute("SELECT count(*) FROM partners WHERE nsfdc_authorized = 'AUTHORIZED'").fetchone()[0]
    unknown_count = cur.execute("SELECT count(*) FROM partners WHERE nsfdc_authorized = 'UNKNOWN'").fetchone()[0]
    print(f"   -> Partners with confirmed NSFDC Scheme Authorization: {auth_count}")
    print(f"   -> Active partners with authorization status 'UNKNOWN':  {unknown_count}")

    # 7. Post-Remediation Verification Counts
    print("\n=================================================================")
    print("POST-REMEDIATION DATABASE COUNTS")
    print("=================================================================")
    total_post = cur.execute("SELECT count(*) FROM partners").fetchone()[0]
    active_post = cur.execute("SELECT count(*) FROM partners WHERE is_active = 1").fetchone()[0]
    quarantined_post = cur.execute("SELECT count(*) FROM partners WHERE record_status = 'QUARANTINED'").fetchone()[0]
    inactive_post = cur.execute("SELECT count(*) FROM partners WHERE record_status = 'INACTIVE'").fetchone()[0]
    changelogs_post = cur.execute("SELECT count(*) FROM partner_changelogs").fetchone()[0]

    print(f"Total partner rows:             {total_post} (unchanged — zero rows deleted)")
    print(f"Active citizen-safe partners:   {active_post} (was {active_partners_pre})")
    print(f"Quarantined records:            {quarantined_post}")
    print(f"Inactive records (duplicates):  {inactive_post}")
    print(f"Changelog entries:              {changelogs_post} (audit trail preserved)")

    conn.close()
    print("\nRemediation script completed successfully!")

if __name__ == "__main__":
    run_remediation()
