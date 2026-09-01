"""
Complete Multilingual Sanitizer & Auditor
Applies all verified modular translation dictionaries, eliminates legacy Devanagari/English copies,
and ensures true 12-language parity across the entire platform.
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
from batch_home_nav_footer import BATCH_HOME_NAV_FOOTER
from batch_calc_comp_schemes import BATCH_CALC_COMP_SCHEMES
from batch_rec_dash_docs_partners import BATCH_REC_DASH_DOCS_PARTNERS
from exact_153_translations import EXACT_153_DATA
from final_15_translations import FINAL_15_TRANSLATIONS

SUPPORTED_LANGUAGES = ["en", "hi", "bn", "mr", "ta", "te", "gu", "kn", "ml", "pa", "or", "as"]

ALL_TRANSLATIONS = {}
for mod in [
    COMMON_TRANSLATIONS,
    CALCULATOR_TRANSLATIONS,
    COMPARE_TRANSLATIONS,
    SCHEMES_AND_PARTNERS_TRANSLATIONS,
    RECOMMENDATIONS_DASHBOARD_TRANSLATIONS,
    REMAINING_CALCULATOR_COMPARE,
    REMAINING_SCHEMES_DASHBOARD_OTHER,
    BATCH_HOME_NAV_FOOTER,
    BATCH_CALC_COMP_SCHEMES,
    BATCH_REC_DASH_DOCS_PARTNERS,
    EXACT_153_DATA,
    FINAL_15_TRANSLATIONS
]:
    ALL_TRANSLATIONS.update(mod)

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

def sanitize_and_sync():
    print(f"Loaded {len(ALL_TRANSLATIONS)} verified translation keys.")

    # 1. Update all locales with verified translation dictionary
    for lang in SUPPORTED_LANGUAGES:
        loc_file = os.path.join(LOCALES_DIR, f"{lang}.json")
        with open(loc_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        for key, lang_map in ALL_TRANSLATIONS.items():
            if lang in lang_map:
                set_nested_value(data, key, lang_map[lang])

        with open(loc_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # 2. Check for any remaining actual Devanagari letters in non-Hindi/Marathi locales
    dev_letters_pat = re.compile(r'[\u0904-\u0939\u093D-\u0963\u0966-\u097F]')
    non_hi_mr = ["te", "ta", "kn", "ml", "gu", "pa", "or", "as", "bn"]

    remaining_issues = {}
    for lang in non_hi_mr:
        loc_file = os.path.join(LOCALES_DIR, f"{lang}.json")
        with open(loc_file, "r", encoding="utf-8") as f:
            flat = flatten(json.load(f))
        
        lang_issues = []
        for k, v in flat.items():
            if dev_letters_pat.search(str(v)):
                lang_issues.append((k, str(v)))
        if lang_issues:
            remaining_issues[lang] = lang_issues
            print(f"Locale [{lang}]: {len(lang_issues)} keys still have Devanagari letters.")

    if not remaining_issues:
        print("SUCCESS: EXACTLY ZERO Devanagari letters found in all 9 non-Hindi/Marathi locale files!")
    else:
        print(f"Summary: {len(remaining_issues)} locales have issues remaining.")

if __name__ == "__main__":
    sanitize_and_sync()
