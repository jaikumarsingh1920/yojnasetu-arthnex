import json
import os
import re

locales_dir = r'c:\Users\jaiku\OneDrive\Desktop\yojnasetu\yojna setu\01frontend\src\i18n\locales'

def flatten(d, prefix=''):
    items = {}
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            items.update(flatten(v, key))
        else:
            items[key] = v
    return items

with open(os.path.join(locales_dir, 'en.json'), 'r', encoding='utf-8') as f:
    en_flat = flatten(json.load(f))

with open(os.path.join(locales_dir, 'hi.json'), 'r', encoding='utf-8') as f:
    hi_flat = flatten(json.load(f))

with open(os.path.join(locales_dir, 'te.json'), 'r', encoding='utf-8') as f:
    te_flat = flatten(json.load(f))

dev_pat = re.compile(r'[\u0900-\u097F]')

te_rem = {}
for k, v in te_flat.items():
    if dev_pat.search(str(v)):
        te_rem[k] = {
            'en': en_flat.get(k, ''),
            'hi': hi_flat.get(k, ''),
            'curr_te': v
        }

print(f"Total remaining in te.json: {len(te_rem)}")
with open('scripts/te_rem_153.json', 'w', encoding='utf-8') as f:
    json.dump(te_rem, f, indent=2, ensure_ascii=False)

# Breakdown by namespace
ns_counts = {}
for k in te_rem:
    ns = k.split('.')[0]
    ns_counts[ns] = ns_counts.get(ns, 0) + 1

for ns, count in sorted(ns_counts.items(), key=lambda x: -x[1]):
    print(f"  {ns}: {count} keys")
