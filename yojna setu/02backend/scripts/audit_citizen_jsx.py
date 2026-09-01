import os
import re

frontend_src = r'c:\Users\jaiku\OneDrive\Desktop\yojnasetu\yojna setu\01frontend\src'

citizen_files = [
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
    'components/ai/ChatMessage.tsx',
]

pattern = re.compile(r'>\s*([A-Za-z][A-Za-z0-9\s,\'\"\.\-\:\?\!\/]{3,})\s*<')

ignore_phrases = {
    'React.FC', 'YojnaSetu', 'YojnaSetu AI', 'MUDRA', 'PMEGP', 'PM Vishwakarma',
    'Kisan', 'Scholarship', 'Women', 'Government of India', 'General / Unreserved',
    'Uttar Pradesh', 'Maharashtra', 'Bihar', 'West Bengal', 'Madhya Pradesh',
    'Tamil Nadu', 'Rajasthan', 'Karnataka', 'Gujarat', 'Delhi', 'OpenStreetMap',
    'yojnasetu.gov.in', 'EMI = P × r × (1+r)ⁿ / ((1+r)ⁿ - 1)', 'ID:', 'OR',
    '404 — ', '403 — ', 'Previous', 'Next'
}

matches = []

for rel in citizen_files:
    path = os.path.join(frontend_src, rel)
    if not os.path.exists(path):
        continue
    with open(path, 'r', encoding='utf-8') as fh:
        lines = fh.readlines()
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith('//') or stripped.startswith('/*') or 'import ' in stripped:
            continue
        m = pattern.search(line)
        if m:
            text = m.group(1).strip()
            # If text is inside t('...') or JSX expression {...} ignore
            if text in ignore_phrases or text.startswith('{') or 't(' in line:
                continue
            matches.append((rel, i, text))

print(f"Found {len(matches)} potential raw strings in citizen files:")
for rel, i, text in matches:
    print(f"{rel}:{i} -> {text}")
