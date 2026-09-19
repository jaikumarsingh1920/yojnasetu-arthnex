from app.db.session import engine
from sqlalchemy import text

def run_migration():
    with engine.begin() as conn:
        cols = {
            "schemes": [
                ("application_channel", "VARCHAR(255)")
            ],
            "partners": [
                ("city", "VARCHAR(100)"),
                ("parent_organization", "VARCHAR(255)"),
                ("coordinate_precision", "VARCHAR(50) DEFAULT 'EXACT_ADDRESS'")
            ],
            "partner_scheme_mappings": [
                ("confidence", "VARCHAR(20) DEFAULT 'HIGH'")
            ]
        }
        for table, table_cols in cols.items():
            existing = [row[1] for row in conn.execute(text(f"PRAGMA table_info({table})")).fetchall()]
            for col_name, col_def in table_cols:
                if col_name not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def}"))
                    print(f"Added {table}.{col_name}")
                else:
                    print(f"Already exists: {table}.{col_name}")

if __name__ == "__main__":
    run_migration()
