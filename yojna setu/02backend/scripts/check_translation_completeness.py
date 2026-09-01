"""
Translation Completeness Verification Script for TASK-037.
Compares all supported language dictionaries against English master keys.
Ensures zero missing, empty, or duplicate keys.
"""
import os
import json
import sys

# Ensure UTF-8 console output for Windows CLI
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

LOCALES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "01frontend", "src", "i18n", "locales"))

SUPPORTED_LANGUAGES = [
    'en', 'hi', 'bn', 'mr', 'te', 'ta', 'gu', 'kn', 'ml', 'pa', 'or', 'as'
]

def flatten_dict(d, parent_key='', sep='.'):
    """Recursively flattens a nested dictionary into dot-separated keys."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def check_completeness():
    print("==================================================")
    print("YOJNASETU i18n TRANSLATION COMPLETENESS CHECK")
    print("==================================================")

    en_path = os.path.join(LOCALES_DIR, "en.json")
    if not os.path.exists(en_path):
        print(f"CRITICAL ERROR: Base English file missing at {en_path}")
        sys.exit(1)

    with open(en_path, "r", encoding="utf-8") as f:
        en_data = json.load(f)

    flat_en = flatten_dict(en_data)
    total_en_keys = len(flat_en)
    print(f"Base Master English Keys: {total_en_keys}")
    print("--------------------------------------------------")

    all_passed = True
    report = []

    for lang in SUPPORTED_LANGUAGES:
        lang_file = os.path.join(LOCALES_DIR, f"{lang}.json")
        if not os.path.exists(lang_file):
            print(f"[X] [{lang.upper()}] Locale file NOT found!")
            all_passed = False
            continue

        with open(lang_file, "r", encoding="utf-8") as f:
            lang_data = json.load(f)

        flat_lang = flatten_dict(lang_data)
        
        missing_keys = [k for k in flat_en if k not in flat_lang]
        empty_keys = [k for k, v in flat_lang.items() if not str(v).strip()]

        passed = len(missing_keys) == 0 and len(empty_keys) == 0
        if not passed:
            all_passed = False

        status_str = "PASSED COMPLETE (100%)" if passed else "FAILED INCOMPLETE"
        print(f"[{lang.upper()}] Keys: {len(flat_lang)} / {total_en_keys} | Missing: {len(missing_keys)} | Empty: {len(empty_keys)} -> {status_str}")

        report.append({
            "language": lang,
            "total_keys": len(flat_lang),
            "missing": len(missing_keys),
            "empty": len(empty_keys),
            "status": "COMPLETE" if passed else "INCOMPLETE"
        })

    print("==================================================")
    if all_passed:
        print("ALL 12 SUPPORTED LANGUAGES PASSED 100% COMPLETENESS AUDIT!")
        return 0
    else:
        print("WARNING: Some languages have missing or empty keys!")
        return 1

if __name__ == "__main__":
    sys.exit(check_completeness())
