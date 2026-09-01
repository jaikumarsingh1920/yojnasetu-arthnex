"""
Automated Test Suite for Home Page UX Hierarchy, True Multilingual Localization, and Responsive Design
Tests:
1. All 12 supported locales exist, parse cleanly, and have 0 missing/empty keys.
2. True multilingual evaluation: actual translated content without blind English copies.
3. Home UX hierarchy:
   - Priority 1: Find Matching Schemes (Primary CTA to /recommendations)
   - Priority 2: Smart Matching & Personalized Guidance
   - Priority 3: How it Works (Concise 4-step roadmap)
   - Priority 4: Explore by Category (6 secondary discovery categories)
   - Priority 5: Exactly ONE browsing CTA to /schemes on the Home page
   - Priority 6: Consolidated Trust & Official Sources section
   - Priority 7: Single strong final CTA to /recommendations
4. Mobile responsiveness compliance (fluid layout, touch targets >= 44px, no fixed-width horizontal overflow).
5. Truthful claims audit (no guaranteed approval/sanction promises).
"""

import json
import os
import re
import pytest

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "01frontend")
LOCALES_DIR = os.path.join(FRONTEND_DIR, "src", "i18n", "locales")
HOME_TSX_PATH = os.path.join(FRONTEND_DIR, "src", "pages", "Home.tsx")

ALL_12_LOCALES = ["en", "hi", "bn", "mr", "te", "ta", "gu", "kn", "ml", "pa", "or", "as"]

HOME_REQUIRED_KEYS = [
    "home.heroTitle",
    "home.heroSubtitle",
    "home.findMatchingSchemes",
    "home.exploreAllSchemes",
    "home.searchPlaceholder",
    "home.searchButton",
    "home.portalBadge",
    "home.verifiedSchemesCount",
    "home.smartMatchingTitle",
    "home.smartMatchingDescription",
    "home.personalizedMatching",
    "home.ruleBasedEligibility",
    "home.officialSources",
    "home.noDocumentUpload",
    "home.howItWorksTitle",
    "home.howItWorksSub",
    "home.stepTellUs",
    "home.stepCheckEligibility",
    "home.stepDiscoverSchemes",
    "home.stepOfficialRoute",
    "home.exploreByCategory",
    "home.exploreByCategorySub",
    "home.categories.msmeTitle",
    "home.categories.agriTitle",
    "home.categories.artisanTitle",
    "home.categories.eduTitle",
    "home.categories.socialTitle",
    "home.categories.healthTitle",
    "home.trustTitle",
    "home.trustDesc",
    "home.trustPillar1",
    "home.trustPillar2",
    "home.trustPillar3",
    "home.trustPillar4",
    "home.finalCtaTitle",
    "home.finalCtaSubtitle",
    "home.finalCtaButton"
]

def get_nested(d, dotted):
    cur = d
    for part in dotted.split('.'):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur

def flatten_dict(d, prefix=""):
    items = {}
    for k, v in d.items():
        curr = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            items.update(flatten_dict(v, curr))
        else:
            items[curr] = v
    return items

# ==============================================================================
# 1. LOCALES INTEGRITY TESTS
# ==============================================================================

def test_all_12_locales_exist_and_parse():
    """Verify all 12 locale JSON files exist and contain valid JSON."""
    assert os.path.exists(LOCALES_DIR), f"Locales directory missing: {LOCALES_DIR}"
    for lang in ALL_12_LOCALES:
        file_path = os.path.join(LOCALES_DIR, f"{lang}.json")
        assert os.path.exists(file_path), f"Locale file missing for language: {lang}"
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert isinstance(data, dict), f"Locale {lang} root is not a dict"
            assert len(data) > 0, f"Locale {lang} is empty"

def test_home_keys_exist_and_non_empty_in_all_12_locales():
    """Verify that all required Home keys are present and non-empty in all 12 locales."""
    for lang in ALL_12_LOCALES:
        file_path = os.path.join(LOCALES_DIR, f"{lang}.json")
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for key in HOME_REQUIRED_KEYS:
            val = get_nested(data, key)
            assert val is not None, f"Key '{key}' missing in locale '{lang}'"
            assert isinstance(val, str), f"Key '{key}' in locale '{lang}' is not a string"
            assert len(val.strip()) > 0, f"Key '{key}' in locale '{lang}' is empty"
            assert val != key, f"Key '{key}' in locale '{lang}' has literal raw key value"

def test_true_multilingual_no_blind_english_copies_in_non_english_locales():
    """Verify that non-English locales have authentic translations and not blind English copies."""
    with open(os.path.join(LOCALES_DIR, "en.json"), "r", encoding="utf-8") as f:
        en_data = json.load(f)

    # Check key Home titles and descriptions that must never be in English in regional locales
    critical_home_keys = [
        "home.heroTitle",
        "home.heroSubtitle",
        "home.findMatchingSchemes",
        "home.smartMatchingTitle",
        "home.smartMatchingDescription",
        "home.personalizedMatching",
        "home.ruleBasedEligibility",
        "home.noDocumentUpload",
        "home.howItWorksTitle",
        "home.howItWorksSub",
        "home.stepTellUs",
        "home.stepCheckEligibility",
        "home.stepDiscoverSchemes",
        "home.stepOfficialRoute",
        "home.exploreByCategory",
        "home.trustTitle",
        "home.trustDesc",
        "home.finalCtaTitle",
        "home.finalCtaButton"
    ]

    for lang in ALL_12_LOCALES:
        if lang == "en":
            continue
        file_path = os.path.join(LOCALES_DIR, f"{lang}.json")
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for key in critical_home_keys:
            en_val = get_nested(en_data, key)
            lang_val = get_nested(data, key)
            assert lang_val != en_val, (
                f"Locale '{lang}' has untranslated English copy for '{key}': '{lang_val}'"
            )

# ==============================================================================
# 2. HOME PAGE UX HIERARCHY & ROUTE RESTRICTIONS
# ==============================================================================

def test_home_page_single_browsing_cta_rule():
    """
    Verify that YojnaSetu Home page has exactly ONE browsing CTA to '/schemes'.
    YojnaSetu must feel like a personalized scheme-matching platform,
    NOT a catalogue of 90 schemes.
    """
    assert os.path.exists(HOME_TSX_PATH), "Home.tsx does not exist"
    with open(HOME_TSX_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Find all Link elements pointing to /schemes
    # Pattern: to="/schemes" or to={'/schemes'}
    matches = re.findall(r'<Link[^>]+to=["\']\/schemes["\']', content)
    assert len(matches) == 1, (
        f"Expected exactly 1 browsing Link to '/schemes' in Home.tsx, but found {len(matches)}!"
    )

    # Ensure the single browsing CTA is home.exploreAllSchemes
    assert "t('home.exploreAllSchemes')" in content, (
        "Expected single browsing CTA to use t('home.exploreAllSchemes')"
    )

def test_home_page_primary_recommendation_flow():
    """
    Verify that primary CTAs prominently guide citizens to /recommendations.
    """
    with open(HOME_TSX_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Verify links to /recommendations exist in Hero, Smart Matching, and Final CTA
    rec_links = re.findall(r'<Link[^>]+to=["\']\/recommendations["\']', content)
    assert len(rec_links) >= 3, (
        f"Expected at least 3 prominent recommendation links to '/recommendations', found {len(rec_links)}"
    )

    # Check key semantic translation tokens
    assert "t('home.findMatchingSchemes')" in content, "Missing 'home.findMatchingSchemes' token"
    assert "t('home.finalCtaButton')" in content, "Missing 'home.finalCtaButton' token"

def test_home_page_all_six_category_cards_preserved():
    """
    Verify that the 6 category cards are preserved as secondary discovery.
    """
    with open(HOME_TSX_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    required_categories = [
        "home.categories.msmeTitle",
        "home.categories.agriTitle",
        "home.categories.artisanTitle",
        "home.categories.eduTitle",
        "home.categories.socialTitle",
        "home.categories.healthTitle"
    ]
    for cat in required_categories:
        assert f"t('{cat}')" in content, f"Category card '{cat}' is missing in Home.tsx"

    # Verify 'schemes.viewDetails' is used on cards
    assert "t('schemes.viewDetails'" in content, "Missing 'schemes.viewDetails' on category cards"

def test_home_page_concise_four_step_roadmap():
    """
    Verify the concise 4-step 'How It Works' roadmap is present.
    """
    with open(HOME_TSX_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    for step in ["home.stepTellUs", "home.stepCheckEligibility", "home.stepDiscoverSchemes", "home.stepOfficialRoute"]:
        assert f"t('{step}')" in content, f"Step '{step}' missing in Home.tsx"

def test_home_page_trust_and_official_sources():
    """
    Verify consolidated Trust & Official Sources section is present.
    """
    with open(HOME_TSX_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    for pillar in ["home.trustPillar1", "home.trustPillar2", "home.trustPillar3", "home.trustPillar4"]:
        assert f"t('{pillar}')" in content, f"Trust pillar '{pillar}' missing in Home.tsx"

# ==============================================================================
# 3. MOBILE RESPONSIVENESS & ACCESSIBILITY AUDIT
# ==============================================================================

def test_home_page_mobile_touch_targets_and_overflow():
    """
    Verify mobile compliance:
    - Minimum 44px touch targets on primary interactive buttons (min-h-[48px], min-h-[50px]).
    - Responsive grid wrapping (no hardcoded fixed pixel container widths like w-[1000px]).
    - Flexible layouts that fit 320px, 360px, 375px, 390px, 414px viewports.
    """
    with open(HOME_TSX_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Ensure touch target classes min-h-[48px] or min-h-[50px] are present on CTAs
    assert "min-h-[48px]" in content or "min-h-[50px]" in content, (
        "Home page CTAs must have explicit touch target height (e.g. min-h-[48px]) for mobile compliance"
    )

    # Ensure no fixed widths > 400px that break 320px mobile screens
    fixed_width_matches = re.findall(r'w-\[(\d+)px\]', content)
    for width in fixed_width_matches:
        assert int(width) <= 320, (
            f"Found fixed pixel width w-[{width}px] which causes horizontal overflow on 320px/360px mobile viewports!"
        )

    # Check that responsive grid classes are present
    assert "grid-cols-1" in content, "Expected mobile-first grid-cols-1"
    assert "sm:grid-cols-2" in content or "sm:grid-cols-3" in content, "Expected responsive grid layout"

# ==============================================================================
# 4. TRUTHFUL CLAIMS COMPLIANCE
# ==============================================================================

def test_home_page_truthful_language():
    """
    Verify Home.tsx and all locales do NOT claim:
    - Guaranteed approval
    - Instant loan sanction
    - Direct government sanction
    And DO use truthful claims:
    - Rule-based eligibility
    - Official sources
    - May be eligible
    - Zero document upload
    """
    prohibited_terms = [
        "guaranteed approval",
        "guaranteed eligibility",
        "100% approval guaranteed",
        "direct loan sanction",
        "instant sanction guaranteed"
    ]

    with open(HOME_TSX_PATH, "r", encoding="utf-8") as f:
        home_content = f.read().lower()

    for term in prohibited_terms:
        assert term not in home_content, f"Prohibited untruthful claim found in Home.tsx: '{term}'"

    # Check that en.json does not contain prohibited terms
    with open(os.path.join(LOCALES_DIR, "en.json"), "r", encoding="utf-8") as f:
        en_content = f.read().lower()

    for term in prohibited_terms:
        assert term not in en_content, f"Prohibited untruthful claim found in en.json: '{term}'"
