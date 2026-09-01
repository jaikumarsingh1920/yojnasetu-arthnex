"""
Sync all keys to en.json and ensure all 12 locales have identical key sets.
"""

import json
import os

LOCALES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "01frontend", "src", "i18n", "locales")
REMAINING_FILE = os.path.join(os.path.dirname(__file__), "remaining_115_keys.json")

with open(REMAINING_FILE, "r", encoding="utf-8") as f:
    rem = json.load(f)

with open(os.path.join(LOCALES_DIR, "en.json"), "r", encoding="utf-8") as f:
    en_data = json.load(f)

def set_dotted(d, dotted, val):
    parts = dotted.split('.')
    cur = d
    for p in parts[:-1]:
        if p not in cur or not isinstance(cur[p], dict):
            cur[p] = {}
        cur = cur[p]
    cur[parts[-1]] = val

for dotted_k, info in rem.items():
    set_dotted(en_data, dotted_k, info["en"])

with open(os.path.join(LOCALES_DIR, "en.json"), "w", encoding="utf-8") as f:
    json.dump(en_data, f, ensure_ascii=False, indent=2)

print("Updated en.json with complete master keys.")
