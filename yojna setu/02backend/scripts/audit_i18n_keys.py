"""
Comprehensive A-Z Localization Audit Script
Scans all frontend source files for translation calls and checks all 12 locale dictionaries.
"""

import os
import re
import json
import glob

FRONTEND_SRC = os.path.join(os.path.dirname(__file__), "..", "..", "01frontend", "src")
LOCALES_DIR = os.path.join(FRONTEND_SRC, "i18n", "locales")

# Matches t('key.subkey', ...) or t("key.subkey", ...) - with word boundary to avoid matching .get('...'), .split('...')
T_PATTERN = re.compile(r"\bt\(\s*['\"]([a-zA-Z0-9_\-\.]+)['\"]")

# Also look for raw translation keys rendered inside JSX like >schemes.viewDetails< or {'schemes.viewDetails'}
JSX_RAW_PATTERN = re.compile(r">(?:\{['\"])?([a-zA-Z0-9_\-]+\.[a-zA-Z0-9_\-\.]+)(?:['\"]\})?<")

def get_nested(d, key):
    parts = key.split(".")
    cur = d
    for p in parts:
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return None
    return cur

def audit():
    used_keys = {}
    jsx_raw_matches = []

    for root, dirs, files in os.walk(FRONTEND_SRC):
        for f in files:
            if f.endswith(".tsx") or f.endswith(".ts"):
                path = os.path.join(root, f)
                rel_path = os.path.relpath(path, FRONTEND_SRC)
                with open(path, "r", encoding="utf-8", errors="ignore") as code_file:
                    lines = code_file.readlines()
                    for idx, line in enumerate(lines, 1):
                        # check t()
                        for m in T_PATTERN.findall(line):
                            if m not in used_keys:
                                used_keys[m] = []
                            used_keys[m].append(f"{rel_path}:{idx}")

                        # check potential raw key in JSX (excluding import, comments, css classes)
                        if "import " not in line and "from " not in line and "//" not in line:
                            for raw in JSX_RAW_PATTERN.findall(line):
                                if any(prefix in raw for prefix in ["schemes.", "nav.", "common.", "calculator.", "home.", "compare.", "channelPartners."]):
                                    jsx_raw_matches.append((raw, f"{rel_path}:{idx}", line.strip()))

    print(f"==================================================")
    print(f"A-Z I18N AUDIT: {len(used_keys)} unique keys used via t()")
    print(f"==================================================")

    if jsx_raw_matches:
        print(f"WARNING: Found {len(jsx_raw_matches)} potential RAW translation keys directly in JSX:")
        for raw, loc, line in jsx_raw_matches:
            print(f"  - {raw} at {loc}: {line}")
    else:
        print("PASS: No un-wrapped raw translation keys found in JSX text.")

    locales = sorted(glob.glob(os.path.join(LOCALES_DIR, "*.json")))
    missing_by_locale = {}
    all_keys_union = set(used_keys.keys())

    for loc in locales:
        lang = os.path.basename(loc).replace(".json", "")
        with open(loc, "r", encoding="utf-8") as f:
            data = json.load(f)

        missing = []
        for k in all_keys_union:
            val = get_nested(data, k)
            if val is None or val == "":
                missing.append(k)

        missing_by_locale[lang] = missing
        if missing:
            print(f"Locale [{lang}]: {len(missing)} MISSING KEYS!")
            for mk in missing[:15]:
                locs = ", ".join(used_keys.get(mk, [])[:2])
                print(f"    * '{mk}' (used in: {locs})")
        else:
            print(f"Locale [{lang}]: 100% PASS ({len(all_keys_union)} / {len(all_keys_union)} keys present)")

    return used_keys, missing_by_locale

if __name__ == "__main__":
    audit()
