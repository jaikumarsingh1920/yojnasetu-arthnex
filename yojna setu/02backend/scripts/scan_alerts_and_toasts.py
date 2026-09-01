import os
import re

frontend_src = r'c:\Users\jaiku\OneDrive\Desktop\yojnasetu\yojna setu\01frontend\src'

alert_pattern = re.compile(r'\balert\([\"\\\'](.*?)\1\)')
toast_pattern = re.compile(r'\btoast\.(?:error|success|info|warning)\([\"\\\'](.*?)\1\)')

findings = []

for root, _, files in os.walk(frontend_src):
    for f in files:
        if f.endswith('.tsx') or f.endswith('.ts'):
            if 'Admin' in f or 'test' in f:
                continue
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as fh:
                lines = fh.readlines()
            for line_no, line in enumerate(lines, 1):
                m_alert = alert_pattern.search(line)
                if m_alert:
                    findings.append((f, line_no, 'alert', m_alert.group(1)))
                m_toast = toast_pattern.search(line)
                if m_toast:
                    findings.append((f, line_no, 'toast', m_toast.group(1)))

print(f"Total alert/toast findings: {len(findings)}")
for f, l, typ, txt in findings:
    print(f"{f}:{l} [{typ}]: {txt}")
