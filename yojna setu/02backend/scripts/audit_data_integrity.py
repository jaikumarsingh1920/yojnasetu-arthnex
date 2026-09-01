import sqlite3
import os
import json
import re

def run_data_integrity_audit():
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(backend_dir, "app", "yojnasetu.db")
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    cur.execute("SELECT * FROM schemes")
    rows = cur.fetchall()
    total_schemes = len(rows)

    scheme_ids = set()
    duplicate_ids = []
    invalid_urls = []
    
    classification_counts = {
        "VALID": 0,
        "NOT_APPLICABLE": 0,
        "NOT_SPECIFIED": 0,
        "BUG": 0
    }
    
    findings = []

    for row in rows:
        sid = row["scheme_id"]
        if sid in scheme_ids:
            duplicate_ids.append(sid)
        scheme_ids.add(sid)

        # URL validation
        url = row["official_source_url"]
        if not url or not (url.startswith("http://") or url.startswith("https://")):
            invalid_urls.append((sid, "official_source_url", url))
            classification_counts["BUG"] += 1
        else:
            classification_counts["VALID"] += 1

        # Check loan parameters consistency
        la = str(row["loan_available"] or "").strip().upper()
        max_loan = row["max_loan_amount"]
        rate_min = row["interest_rate_min"]
        rate_max = row["interest_rate_max"]
        tenure = row["repayment_period_max_months"]

        if la in ("NO", "FALSE", "0"):
            # Non-credit scheme
            if max_loan == 0 or rate_min == 0 or rate_max == 0 or tenure == 0:
                classification_counts["BUG"] += 1
                findings.append({
                    "scheme_id": sid,
                    "issue": "Numeric 0 in non-credit scheme",
                    "classification": "BUG",
                    "details": f"max_loan={max_loan}, rate={rate_min}-{rate_max}, tenure={tenure}"
                })
            else:
                classification_counts["NOT_APPLICABLE"] += 1
        elif la in ("YES", "TRUE", "1"):
            if max_loan is not None and max_loan > 0:
                classification_counts["VALID"] += 1
            elif max_loan is None:
                classification_counts["NOT_SPECIFIED"] += 1
            
            if rate_min is not None and rate_min > 0:
                classification_counts["VALID"] += 1
            elif rate_min is None:
                classification_counts["NOT_SPECIFIED"] += 1

    # Check changelogs count
    cur.execute("SELECT count(*) FROM scheme_changelogs")
    changelog_count = cur.fetchone()[0]

    # Check active / inactive count
    cur.execute("SELECT scheme_status, count(*) FROM schemes GROUP BY scheme_status")
    status_distribution = dict(cur.fetchall())

    audit_summary = {
        "total_schemes": total_schemes,
        "unique_scheme_ids": len(scheme_ids),
        "duplicate_ids": duplicate_ids,
        "invalid_urls_count": len(invalid_urls),
        "invalid_urls": invalid_urls[:5],
        "status_distribution": status_distribution,
        "total_changelog_entries": changelog_count,
        "classification_counts": classification_counts,
        "findings_count": len(findings),
        "sample_findings": findings[:5]
    }

    print(json.dumps(audit_summary, indent=2))
    con.close()
    return audit_summary

if __name__ == "__main__":
    run_data_integrity_audit()
