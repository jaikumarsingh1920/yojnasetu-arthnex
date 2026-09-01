"""
Automated A-Z Localization Audit Test Suite
Enforces 100% localization integrity across all 12 official languages:
en, hi, bn, mr, te, ta, gu, kn, ml, pa, or, as.
"""

import os
import re
import json
import glob
import pytest

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
FRONTEND_SRC = os.path.join(PROJECT_ROOT, "01frontend", "src")
LOCALES_DIR = os.path.join(FRONTEND_SRC, "i18n", "locales")

SUPPORTED_LANGUAGES = ["en", "hi", "bn", "mr", "ta", "te", "gu", "kn", "ml", "pa", "or", "as"]

T_PATTERN = re.compile(r"\bt\(\s*['\"]([a-zA-Z0-9_\-\.]+)['\"]")
INTERPOLATION_PATTERN = re.compile(r"\{\{([a-zA-Z0-9_]+)\}\}")

def get_nested(d, key):
    parts = key.split(".")
    cur = d
    for p in parts:
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return None
    return cur

@pytest.fixture(scope="module")
def used_frontend_keys():
    """Collects all translation keys called via t('...') in frontend code."""
    keys = set()
    for root, _, files in os.walk(FRONTEND_SRC):
        for f in files:
            if f.endswith(".tsx") or f.endswith(".ts"):
                path = os.path.join(root, f)
                with open(path, "r", encoding="utf-8", errors="ignore") as fp:
                    content = fp.read()
                    for k in T_PATTERN.findall(content):
                        keys.add(k)
    return keys

@pytest.fixture(scope="module")
def locale_data():
    """Loads all 12 locale JSON files."""
    data = {}
    for lang in SUPPORTED_LANGUAGES:
        loc_path = os.path.join(LOCALES_DIR, f"{lang}.json")
        assert os.path.exists(loc_path), f"Locale file missing: {loc_path}"
        with open(loc_path, "r", encoding="utf-8") as fp:
            data[lang] = json.load(fp)
    return data

def test_all_12_locales_exist_and_load(locale_data):
    """Verify all 12 language files exist and have non-empty top-level dictionaries."""
    assert len(locale_data) == 12
    for lang, content in locale_data.items():
        assert isinstance(content, dict)
        assert len(content) > 10, f"Locale {lang} has suspiciously few top-level sections"

def test_schemes_view_details_present_in_all_12_languages(locale_data):
    """Verify schemes.viewDetails is explicitly defined with accurate translations across all 12 languages."""
    for lang, content in locale_data.items():
        vd = get_nested(content, "schemes.viewDetails")
        assert vd is not None, f"schemes.viewDetails missing in {lang}"
        assert len(vd.strip()) > 0, f"schemes.viewDetails is empty in {lang}"

    # Verify English and Hindi exact match
    assert locale_data["en"]["schemes"]["viewDetails"] == "View Details"
    assert locale_data["hi"]["schemes"]["viewDetails"] == "विवरण देखें"

def test_all_used_frontend_keys_exist_in_all_locales(used_frontend_keys, locale_data):
    """Verify that every key used in frontend TSX/TS files exists in all 12 locale files."""
    missing_report = {}
    for lang in SUPPORTED_LANGUAGES:
        lang_missing = []
        for k in used_frontend_keys:
            val = get_nested(locale_data[lang], k)
            if val is None or (isinstance(val, str) and len(val.strip()) == 0):
                lang_missing.append(k)
        if lang_missing:
            missing_report[lang] = lang_missing

    assert not missing_report, f"Missing keys found: {json.dumps(missing_report, indent=2)}"

def test_home_category_portfolios_translated(locale_data):
    """Verify category section title and categories are translated across locales."""
    for lang in SUPPORTED_LANGUAGES:
        home = locale_data[lang].get("home", {})
        assert "categorySectionBadge" in home, f"categorySectionBadge missing in {lang}"
        assert "categorySectionTitle" in home, f"categorySectionTitle missing in {lang}"
        categories = home.get("categories", {})
        assert "msmeTitle" in categories, f"msmeTitle missing in {lang}"
        assert "agriTitle" in categories, f"agriTitle missing in {lang}"
        assert "artisanTitle" in categories, f"artisanTitle missing in {lang}"

def test_no_raw_translation_keys_in_jsx():
    """Verify that no raw dotted translation keys are rendered directly as raw strings in JSX."""
    jsx_raw_pattern = re.compile(r">(?:\{['\"])?([a-zA-Z0-9_\-]+\.[a-zA-Z0-9_\-\.]+)(?:['\"]\})?<")
    violations = []

    for root, _, files in os.walk(FRONTEND_SRC):
        for f in files:
            if f.endswith(".tsx"):
                path = os.path.join(root, f)
                with open(path, "r", encoding="utf-8", errors="ignore") as fp:
                    for idx, line in enumerate(fp, 1):
                        if "import " in line or "from " in line or "//" in line:
                            continue
                        for match in jsx_raw_pattern.findall(line):
                            if any(prefix in match for prefix in ["schemes.", "nav.", "common.", "calculator.", "home."]):
                                violations.append(f"{f}:{idx} -> {match}")

    assert not violations, f"Raw translation keys directly in JSX text: {violations}"
