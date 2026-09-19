import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
json_path = os.path.join(BASE_DIR, "data", "prudential_rules.json")

with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

for r in data.get("rules", []):
    r["source"] = f"{r.get('source_document', '')} ({r.get('source_url', '')})"
    r["metric"] = r.get("metric_name")
    r["threshold"] = r.get("threshold_value") if r.get("threshold_value") is not None else r.get("threshold_status")
    r["institution_types"] = r.get("applicable_institution_types") or r.get("target_institution_types")
    r["effective_from"] = data.get("effective_date", "2026-09-15")
    r["verified_at"] = data.get("verified_at", "2026-09-16T10:15:00Z")
    r["scope"] = r.get("financial_scope", "INSTITUTION_LEVEL")

with open(json_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

print("Updated data/prudential_rules.json successfully!")
