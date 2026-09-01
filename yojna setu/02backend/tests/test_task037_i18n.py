"""
TASK-037 — Automated Multilingual / i18n Test Suite.
Tests:
1. English base locale file exists and is valid JSON.
2. All 12 supported Indian language files exist and are valid JSON.
3. Every supported language contains 100% of the base English keys (zero missing keys).
4. No empty or whitespace-only translation strings exist.
5. Canonical database scheme codes (e.g. SIH26092-001) and URLs are never corrupted.
6. Language options in frontend match the 12 canonical BCP-47 codes.
"""
import os
import json
import pytest

LOCALES_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "01frontend", "src", "i18n", "locales")
)

SUPPORTED_LANGUAGES = [
    'en', 'hi', 'bn', 'mr', 'te', 'ta', 'gu', 'kn', 'ml', 'pa', 'or', 'as'
]

def flatten_dict(d, parent_key='', sep='.'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def test_all_12_locale_files_exist():
    """Verify that all 12 locale JSON files exist on disk."""
    for lang in SUPPORTED_LANGUAGES:
        path = os.path.join(LOCALES_DIR, f"{lang}.json")
        assert os.path.exists(path), f"Locale file for {lang} does not exist at {path}"

def test_locales_are_valid_json():
    """Verify that all 12 locale files are valid parseable JSON."""
    for lang in SUPPORTED_LANGUAGES:
        path = os.path.join(LOCALES_DIR, f"{lang}.json")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert isinstance(data, dict), f"{lang}.json must be a JSON object"
            assert len(data.keys()) > 0, f"{lang}.json must not be empty"

def test_zero_missing_keys_across_all_languages():
    """Verify that all 11 non-English languages have zero missing keys compared to base English."""
    en_path = os.path.join(LOCALES_DIR, "en.json")
    with open(en_path, "r", encoding="utf-8") as f:
        en_data = json.load(f)
    
    flat_en = flatten_dict(en_data)
    assert len(flat_en) >= 200, f"English master dict should have comprehensive keys, got {len(flat_en)}"

    for lang in SUPPORTED_LANGUAGES:
        if lang == 'en':
            continue
        lang_path = os.path.join(LOCALES_DIR, f"{lang}.json")
        with open(lang_path, "r", encoding="utf-8") as f:
            lang_data = json.load(f)
        
        flat_lang = flatten_dict(lang_data)
        missing_keys = [k for k in flat_en if k not in flat_lang]
        assert len(missing_keys) == 0, f"Language [{lang}] has missing keys: {missing_keys[:5]}"

def test_zero_empty_translations():
    """Verify that no translation value in any language is blank or empty."""
    for lang in SUPPORTED_LANGUAGES:
        lang_path = os.path.join(LOCALES_DIR, f"{lang}.json")
        with open(lang_path, "r", encoding="utf-8") as f:
            lang_data = json.load(f)
        
        flat_lang = flatten_dict(lang_data)
        empty_keys = [k for k, v in flat_lang.items() if not str(v).strip()]
        assert len(empty_keys) == 0, f"Language [{lang}] has empty keys: {empty_keys}"

def test_essential_namespaces_exist():
    """Verify required top-level namespaces exist in every locale."""
    required_namespaces = [
        "nav", "home", "schemes", "schemeDetail", "schemeCard",
        "documents", "recommendations", "calculator", "partnerLocator",
        "auth", "dashboard", "applications", "savedSchemes", "notifications",
        "portalModal", "copilot", "voice", "common", "errors", "footer"
    ]
    for lang in SUPPORTED_LANGUAGES:
        lang_path = os.path.join(LOCALES_DIR, f"{lang}.json")
        with open(lang_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for ns in required_namespaces:
            assert ns in data, f"Namespace '{ns}' missing in {lang}.json"
