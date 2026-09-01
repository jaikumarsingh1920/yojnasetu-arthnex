import csv
import json
import os

csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "04data", "raw", "schemes_master_cleaned.csv"))
with open(csv_path, encoding='utf-8') as f:
    schemes = list(csv.DictReader(f))

print(f"=== DETAILED AUDIT OF ALL {len(schemes)} SCHEMES ===")
for s in schemes:
    sid = s["scheme_id"]
    name = s["scheme_name"]
    minis = s["ministry"]
    la = s["loan_available"]
    max_l = s["max_loan_amount"]
    rate_min = s["interest_rate_min"]
    rate_max = s["interest_rate_max"]
    sub_av = s["subsidy_available"]
    sub_pct = s["subsidy_percentage"]
    portal = s["official_portal"]
    source = s["official_source_url"]
    app_mode = s["application_mode"]
    print(f"[{sid}] {name}")
    print(f"  Ministry: {minis}")
    print(f"  Loan: {la} | Max: {max_l} | Rate: {rate_min} - {rate_max} | Sub: {sub_av} ({sub_pct}%)")
    print(f"  Portal: {portal}")
    print(f"  Source: {source}")
    print(f"  AppMode: {app_mode}")
    print("-" * 60)
