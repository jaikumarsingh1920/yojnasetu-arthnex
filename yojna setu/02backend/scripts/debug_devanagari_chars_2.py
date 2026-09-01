import json
import re

dev_pat = re.compile(r'[\u0900-\u097F]')

with open('../01frontend/src/i18n/locales/pa.json', 'r', encoding='utf-8') as f:
    pa_data = json.load(f)

def flatten(d, prefix=''):
    items = {}
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            items.update(flatten(v, key))
        else:
            items[key] = v
    return items

flat = flatten(pa_data)
found = 0
for k, v in flat.items():
    matches = dev_pat.findall(str(v))
    if matches:
        found += 1
        codepoints = [f"U+{ord(c):04X}" for c in set(matches)]
        print(f"Key '{k}' (sample chars {codepoints[:3]}): {str(v)[:30].encode('ascii', 'backslashreplace').decode('ascii')}")
        if found >= 10:
            break
print(f"Total matching keys in pa.json: {found}")
