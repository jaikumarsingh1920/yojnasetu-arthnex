"""
Apply True Multilingual Translations
Reads modular translation dictionaries and updates all 12 locale JSON files in:
01frontend/src/i18n/locales/
"""

import os
import json
import re
import sys

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
FRONTEND_SRC = os.path.join(PROJECT_ROOT, "01frontend", "src")
LOCALES_DIR = os.path.join(FRONTEND_SRC, "i18n", "locales")

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "translations"))

from common_translations import COMMON_TRANSLATIONS
from calculator_translations import CALCULATOR_TRANSLATIONS
from compare_translations import COMPARE_TRANSLATIONS
from schemes_and_partners_translations import SCHEMES_AND_PARTNERS_TRANSLATIONS
from recommendations_dashboard_translations import RECOMMENDATIONS_DASHBOARD_TRANSLATIONS
from remaining_calculator_compare import REMAINING_CALCULATOR_COMPARE
from remaining_schemes_dashboard_other import REMAINING_SCHEMES_DASHBOARD_OTHER

ALL_TRANSLATIONS = {}
ALL_TRANSLATIONS.update(COMMON_TRANSLATIONS)
ALL_TRANSLATIONS.update(CALCULATOR_TRANSLATIONS)
ALL_TRANSLATIONS.update(COMPARE_TRANSLATIONS)
ALL_TRANSLATIONS.update(SCHEMES_AND_PARTNERS_TRANSLATIONS)
ALL_TRANSLATIONS.update(RECOMMENDATIONS_DASHBOARD_TRANSLATIONS)
ALL_TRANSLATIONS.update(REMAINING_CALCULATOR_COMPARE)
ALL_TRANSLATIONS.update(REMAINING_SCHEMES_DASHBOARD_OTHER)

SUPPORTED_LANGUAGES = ["en", "hi", "bn", "mr", "ta", "te", "gu", "kn", "ml", "pa", "or", "as"]

def set_nested_value(d, key_path, value):
    parts = key_path.split(".")
    curr = d
    for part in parts[:-1]:
        if part not in curr or not isinstance(curr[part], dict):
            curr[part] = {}
        curr = curr[part]
    curr[parts[-1]] = value

def flatten(d, prefix=""):
    items = {}
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            items.update(flatten(v, key))
        else:
            items[key] = v
    return items

def apply_translations():
    print(f"Total modular keys to synchronize: {len(ALL_TRANSLATIONS)}")
    
    # Check completeness across all 12 languages
    for key, lang_map in ALL_TRANSLATIONS.items():
        for lang in SUPPORTED_LANGUAGES:
            if lang not in lang_map:
                print(f"WARNING: Key '{key}' missing translation for '{lang}'")

    for lang in SUPPORTED_LANGUAGES:
        loc_file = os.path.join(LOCALES_DIR, f"{lang}.json")
        if not os.path.exists(loc_file):
            print(f"ERROR: {loc_file} does not exist!")
            continue
            
        with open(loc_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        updated_count = 0
        for key, lang_map in ALL_TRANSLATIONS.items():
            if lang in lang_map:
                val = lang_map[lang]
                set_nested_value(data, key, val)
                updated_count += 1
                
        with open(loc_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print(f"Locale [{lang}]: Synchronized {updated_count} keys successfully.")

if __name__ == "__main__":
    apply_translations()
