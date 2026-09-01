# -*- coding: utf-8 -*-
"""
Automated QA Audit for Mobile-First Home Page UI/UX & Global Text Size Accessibility
"""

import os
import json
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
FRONTEND_SRC = os.path.join(PROJECT_ROOT, "01frontend", "src")
LOCALES_DIR = os.path.join(FRONTEND_SRC, "i18n", "locales")

SUPPORTED_LANGUAGES = ["en", "hi", "bn", "mr", "ta", "te", "gu", "kn", "ml", "pa", "or", "as"]

def test_locales():
    print("1. Auditing Locale Files & Parity...")
    with open(os.path.join(LOCALES_DIR, "en.json"), "r", encoding="utf-8") as f:
        en_data = json.load(f)

    # Check critical new keys
    required_keys = [
        ("home", "heroCompactTitle"),
        ("home", "searchHeading"),
        ("home", "searchSubheading"),
        ("accessibility", "textSize"),
        ("accessibility", "decreaseText"),
        ("accessibility", "defaultText"),
        ("accessibility", "increaseText"),
    ]

    for lang in SUPPORTED_LANGUAGES:
        loc_path = os.path.join(LOCALES_DIR, f"{lang}.json")
        assert os.path.exists(loc_path), f"Locale {lang}.json missing"
        with open(loc_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for section, key in required_keys:
            assert section in data, f"Section '{section}' missing in {lang}.json"
            assert key in data[section], f"Key '{section}.{key}' missing in {lang}.json"
            val = data[section][key]
            assert val and str(val).strip() != "", f"Key '{section}.{key}' is empty in {lang}.json"
        print(f"   [OK] Locale [{lang.upper()}] verified for all accessibility & home keys")

def test_home_page_structure():
    print("\n2. Auditing Home.tsx Component Structure...")
    home_file = os.path.join(FRONTEND_SRC, "pages", "Home.tsx")
    with open(home_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Check for single browsing CTA
    schemes_links = re.findall(r'to=[\'"]/schemes[\'"]', content)
    print(f"   * Found {len(schemes_links)} link(s) to '/schemes' in Home.tsx")
    assert len(schemes_links) == 1, "Expected exactly 1 browsing link to '/schemes' in Home.tsx"

    # 2. Check for recommendation CTA links
    rec_links = re.findall(r'to=[\'"]/recommendations[\'"]', content)
    print(f"   * Found {len(rec_links)} link(s) to '/recommendations' in Home.tsx")
    assert len(rec_links) >= 2, "Expected primary & final CTA links to '/recommendations'"

    # 3. Check for Category section
    assert "t('home.exploreByCategory')" in content or 't("home.exploreByCategory")' in content, "Category section missing"
    print("   [OK] Category discovery section verified")

    # 4. Check for Trust section
    assert "t('home.trustTitle')" in content or 't("home.trustTitle")' in content, "Trust section missing"
    print("   [OK] Consolidated Trust & Provenance section verified")

    # 5. Check for Search section
    assert "handleSearchSubmit" in content, "Search handling missing"
    print("   [OK] Secondary Search & Focus Areas section verified")

def test_accessibility_text_size():
    print("\n3. Auditing Text Size Context & CSS Rules...")
    context_file = os.path.join(FRONTEND_SRC, "context", "TextSizeContext.tsx")
    assert os.path.exists(context_file), "TextSizeContext.tsx missing"
    with open(context_file, "r", encoding="utf-8") as f:
        ctx_content = f.read()
    assert "yojnasetu_text_size" in ctx_content, "localStorage persistence key missing"
    assert "data-text-size" in ctx_content, "data-text-size attribute setter missing"
    print("   [OK] TextSizeContext & localStorage persistence verified")

    css_file = os.path.join(FRONTEND_SRC, "index.css")
    with open(css_file, "r", encoding="utf-8") as f:
        css_content = f.read()
    assert 'html[data-text-size="small"]' in css_content, "Small text size CSS rule missing"
    assert 'html[data-text-size="default"]' in css_content, "Default text size CSS rule missing"
    assert 'html[data-text-size="large"]' in css_content, "Large text size CSS rule missing"
    assert '@media (max-width: 640px)' in css_content, "Mobile responsive text size media query missing"
    print("   [OK] CSS data-text-size rules and mobile responsiveness verified")

    navbar_file = os.path.join(FRONTEND_SRC, "components", "Navbar.tsx")
    with open(navbar_file, "r", encoding="utf-8") as f:
        nav_content = f.read()
    assert "useTextSize" in nav_content, "Navbar must use useTextSize"
    assert "A−" in nav_content and "A+" in nav_content, "Navbar must render A- and A+ buttons"
    print("   [OK] Navbar text size accessibility controls verified")

if __name__ == "__main__":
    print("=" * 70)
    print("  YOJNASETU MOBILE HOME PAGE & ACCESSIBILITY AUTOMATED AUDIT")
    print("=" * 70)
    test_locales()
    test_home_page_structure()
    test_accessibility_text_size()
    print("\n" + "=" * 70)
    print("  ALL MOBILE HOME PAGE & ACCESSIBILITY AUDITS PASSED!")
    print("=" * 70)
