import os
import re

frontend_src = r'c:\Users\jaiku\OneDrive\Desktop\yojnasetu\yojna setu\01frontend\src'

components = [
    'components/OfficialPortalModal.tsx',
    'components/SchemeEmbeddedCalculator.tsx',
    'components/SchemeDocumentGuidance.tsx',
    'components/StatusTimeline.tsx',
    'components/Badge.tsx',
    'components/SaveSchemeButton.tsx',
    'components/CompareButton.tsx',
    'components/ai/AICopilot.tsx',
    'components/ai/ChatWindow.tsx',
    'components/ai/ChatMessage.tsx',
    'components/ai/VoiceButton.tsx',
]

pattern = re.compile(r'>\s*([A-Za-z][A-Za-z0-9\s,\'\"\.\-\:\?\!\/]{3,})\s*<')

ignore_phrases = {
    'React.FC', 'YojnaSetu', 'YojnaSetu AI', 'MUDRA', 'PMEGP', 'PM Vishwakarma',
    'Kisan', 'Scholarship', 'Women', 'Government of India', 'General / Unreserved',
    'OpenStreetMap', 'yojnasetu.gov.in', 'ID:', 'OR', 'Previous', 'Next',
    'Month', 'Months', 'Years', 'Year'
}

for comp in components:
    path = os.path.join(frontend_src, comp)
    if not os.path.exists(path):
        continue
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith('//') or stripped.startswith('/*') or 'import ' in stripped:
            continue
        m = pattern.search(line)
        if m:
            text = m.group(1).strip()
            if text in ignore_phrases or text.startswith('{') or 't(' in line:
                continue
            print(f"{comp}:{i} -> {text}")
