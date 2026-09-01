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
for k, v in list(flat.items())[:20]:
    matches = dev_pat.findall(str(v))
    if matches:
        # print unicode codepoints
        codepoints = [f"U+{ord(c):04X} ({c})" for c in set(matches)]
        print(f"Key '{k}' has Devanagari: {', '.join(codepoints)}")
