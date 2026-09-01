import sqlite3
import csv
import os
import datetime

def export_live_schemes():
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(backend_dir, "app", "yojnasetu.db")
    if not os.path.exists(db_path):
        db_path = os.path.join(backend_dir, "yojnasetu.db")

    print(f"Reading from database: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get live column names
    cursor.execute("PRAGMA table_info(schemes)")
    columns = [row["name"] for row in cursor.fetchall()]

    # Query all 90 schemes
    cursor.execute("SELECT * FROM schemes ORDER BY scheme_id ASC")
    rows = cursor.fetchall()
    print(f"Retrieved {len(rows)} records with {len(columns)} columns.")

    # Target file paths
    workspace_root = os.path.abspath(os.path.join(backend_dir, ".."))
    dest_workspace = os.path.join(workspace_root, "90_SCHEMES_COMPLETE_DATASET.csv")
    dest_artifact = os.path.join(r"C:\Users\jaiku\.gemini\antigravity-ide\brain\aa994cfa-d45b-4acd-b5fb-bdebc9db6992", "90_SCHEMES_COMPLETE_DATASET.csv")

    targets = [dest_workspace, dest_artifact]

    for target in targets:
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            writer.writerow(columns)
            for r in rows:
                writer.writerow([r[col] if r[col] is not None else "" for col in columns])
        print(f"Written: {target} (Size: {os.path.getsize(target):,} bytes)")

    # Validation Checks
    scheme_ids = [r["scheme_id"] for r in rows]
    unique_ids = set(scheme_ids)
    expected_ids = [f"SIH26092-{i:03d}" for i in range(1, 91)]
    missing_ids = [sid for sid in expected_ids if sid not in unique_ids]
    duplicate_ids = [sid for sid in scheme_ids if scheme_ids.count(sid) > 1]

    print("\n--- VALIDATION SUMMARY ---")
    print(f"Total Rows Extracted: {len(rows)}")
    print(f"Unique Scheme IDs: {len(unique_ids)}")
    print(f"Missing Expected IDs: {missing_ids}")
    print(f"Duplicate IDs: {duplicate_ids}")

    conn.close()
    return len(rows), len(columns), columns, rows, dest_workspace

if __name__ == "__main__":
    export_live_schemes()
