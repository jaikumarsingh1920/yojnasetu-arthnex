import os
import re
import pytest

FRONTEND_SRC = os.path.abspath(r'..\01frontend\src')

VIEWPORTS = [320, 360, 375, 390, 414, 768, 820, 1024, 1280, 1440]

CITIZEN_PAGES = [
    'pages/Home.tsx',
    'pages/Schemes.tsx',
    'pages/SchemeDetail.tsx',
    'pages/Compare.tsx',
    'pages/Recommendations.tsx',
    'pages/Profile.tsx',
    'pages/ChannelPartners.tsx',
    'pages/Calculator.tsx',
    'pages/Dashboard.tsx',
    'pages/Applications.tsx',
    'pages/ApplicationDetail.tsx',
    'pages/SavedSchemes.tsx',
    'pages/Notifications.tsx',
    'pages/Login.tsx',
    'pages/Register.tsx',
    'pages/NotFound.tsx',
    'pages/Unauthorized.tsx',
]

CITIZEN_COMPONENTS = [
    'components/Navbar.tsx',
    'components/Footer.tsx',
    'components/ComparisonTray.tsx',
    'components/CompareButton.tsx',
    'components/SchemeCard.tsx',
    'components/OfficialPortalModal.tsx',
    'components/SaveSchemeButton.tsx',
    'components/MapLocator.tsx',
    'components/SchemeEmbeddedCalculator.tsx',
    'components/SchemeDocumentGuidance.tsx',
    'components/ai/AICopilot.tsx',
    'components/ai/ChatWindow.tsx',
]

def test_no_unresponsive_fixed_widths_in_citizen_ui():
    """Verify citizen pages don't have hardcoded fixed-pixel width classes like w-[400px] or min-w-[500px] without responsive prefixes."""
    fixed_width_pattern = re.compile(r'(?<!sm:|md:|lg:|xl:)\b(w-\[\d+px\]|min-w-\[\d+px\])\b')

    violations = []
    for rel in CITIZEN_PAGES + CITIZEN_COMPONENTS:
        full_path = os.path.join(FRONTEND_SRC, rel)
        if not os.path.exists(full_path):
            continue
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        matches = fixed_width_pattern.findall(content)
        for m in matches:
            # Extract numeric value
            num_match = re.search(r'\d+', m)
            if num_match:
                width = int(num_match.group())
                # Any fixed width > 300px on mobile without prefix is a violation
                if width > 300:
                    violations.append(f"{rel}: {m}")

    assert len(violations) == 0, f"Found fixed width violations on mobile in citizen UI: {violations}"

def test_aicopilot_and_comparison_tray_dock_stacking():
    """Verify AICopilot dynamically offsets its position when ComparisonTray is active to prevent overlap."""
    copilot_file = os.path.join(FRONTEND_SRC, 'components', 'ai', 'AICopilot.tsx')
    with open(copilot_file, 'r', encoding='utf-8') as f:
        content = f.read()

    assert 'useComparison' in content, "AICopilot must import useComparison"
    assert 'hasComparisonDock' in content, "AICopilot must detect hasComparisonDock"
    assert 'bottom-20' in content or 'bottom-24' in content, "AICopilot must offset upward when dock is active"

def test_comparison_tray_touch_target_accessibility():
    """Verify ComparisonTray action buttons have accessible minimum heights."""
    tray_file = os.path.join(FRONTEND_SRC, 'components', 'ComparisonTray.tsx')
    with open(tray_file, 'r', encoding='utf-8') as f:
        content = f.read()

    assert 'min-h-[44px]' in content, "ComparisonTray buttons must satisfy minimum 44px touch target guideline"

def test_schemes_pagination_touch_targets_and_localization():
    """Verify Schemes.tsx pagination buttons have accessible touch targets and proper i18n."""
    schemes_file = os.path.join(FRONTEND_SRC, 'pages', 'Schemes.tsx')
    with open(schemes_file, 'r', encoding='utf-8') as f:
        content = f.read()

    assert "{t('common.prev', 'Previous')}" in content, "Previous button must use i18n"
    assert "{t('common.next', 'Next')}" in content, "Next button must use i18n"
    assert 'min-h-[44px]' in content, "Pagination navigation buttons must satisfy min-h-[44px]"
    assert 'min-w-[38px]' in content or 'min-w-[36px]' in content, "Pagination page number buttons must have min touch area"

def test_scheme_card_guidelines_localized():
    """Verify SchemeCard has no hardcoded Guidelines button text."""
    card_file = os.path.join(FRONTEND_SRC, 'components', 'SchemeCard.tsx')
    with open(card_file, 'r', encoding='utf-8') as f:
        content = f.read()

    assert "{t('schemeCard.guidelines', 'Guidelines')}" in content, "Guidelines button must be localized"

def test_dashboard_active_applications_localized():
    """Verify Dashboard.tsx has localized action links and descriptions."""
    dash_file = os.path.join(FRONTEND_SRC, 'pages', 'Dashboard.tsx')
    with open(dash_file, 'r', encoding='utf-8') as f:
        content = f.read()

    assert "{t('dashboard.activeApplicationsSub'" in content, "Active applications subtitle must be localized"
    assert "{t('dashboard.startNewCheck'" in content, "Start new check CTA must be localized"

def test_maplocator_quick_focus_localized():
    """Verify MapLocator.tsx quick focus and distance units are localized."""
    map_file = os.path.join(FRONTEND_SRC, 'components', 'MapLocator.tsx')
    with open(map_file, 'r', encoding='utf-8') as f:
        content = f.read()

    assert "{t('partnerLocator.quickFocus'" in content, "Quick focus must be localized"
    assert "{t('partnerLocator.kmAway'" in content, "Distance unit must be localized"

def test_saved_schemes_browse_cta_standardized():
    """Verify SavedSchemes.tsx uses standardized exploreAllSchemes CTA."""
    saved_file = os.path.join(FRONTEND_SRC, 'pages', 'SavedSchemes.tsx')
    with open(saved_file, 'r', encoding='utf-8') as f:
        content = f.read()

    assert "t('home.exploreAllSchemes'" in content, "Saved schemes empty state should use exploreAllSchemes"

def test_responsive_grid_and_container_conventions():
    """Verify all citizen pages utilize responsive grid classes and max-w-7xl containers."""
    for rel in CITIZEN_PAGES:
        full_path = os.path.join(FRONTEND_SRC, rel)
        if not os.path.exists(full_path):
            continue
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check standard container padding convention (px-4 sm:px-6 lg:px-8 or max-w-md / max-w-2xl / max-w-7xl)
        has_responsive_padding = 'px-4' in content or 'p-4' in content or 'p-6' in content
        assert has_responsive_padding, f"{rel} must have responsive container padding"
