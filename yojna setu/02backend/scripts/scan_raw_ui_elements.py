import os
import re

frontend_src = r'c:\Users\jaiku\OneDrive\Desktop\yojnasetu\yojna setu\01frontend\src'
target_dirs = [os.path.join(frontend_src, 'pages'), os.path.join(frontend_src, 'components')]

# Regex patterns for attributes
attr_patterns = {
    'placeholder': re.compile(r'placeholder=([\"\\\'])(.*?)\1'),
    'title': re.compile(r'\btitle=([\"\\\'])(.*?)\1'),
    'aria-label': re.compile(r'aria-label=([\"\\\'])(.*?)\1'),
}

ignore_exact = {
    'YojnaSetu', 'YojnaSetu Logo', 'YojnaSetu AI', 'Clear Search Input',
    'Open in Google Maps', 'Toggle theme'
}

findings = []

for tdir in target_dirs:
    for root, _, files in os.walk(tdir):
        for f in files:
            if f.endswith('.tsx') and not f.startswith('Admin'):
                path = os.path.join(root, f)
                with open(path, 'r', encoding='utf-8') as fh:
                    lines = fh.readlines()
                for line_no, line in enumerate(lines, 1):
                    # Check attributes
                    for attr_name, pat in attr_patterns.items():
                        for m in pat.finditer(line):
                            val = m.group(2).strip()
                            if val and not val.startswith('{') and val not in ignore_exact:
                                if re.search(r'[A-Za-z]{3,}', val):
                                    findings.append((f, line_no, attr_name, val))

print(f"Total raw string attribute findings: {len(findings)}")
for f, line_no, attr_name, val in findings:
    safe_val = val.encode('ascii', errors='replace').decode('ascii')
    print(f"{f}:{line_no} [{attr_name}] -> {safe_val}")
