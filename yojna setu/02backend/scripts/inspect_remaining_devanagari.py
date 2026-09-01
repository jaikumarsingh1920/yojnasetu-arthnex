import os
import json
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

with open(os.path.join(locales_dir, 'te.json'), 'r', encoding='utf-8') as f:
    te_flat = flatten(json.load(f))

with open(os.path.join(locales_dir, 'en.json'), 'r', encoding='utf-8') as f:
    en_flat = flatten(json.load(f))

devanagari_pat = re.compile(r'[\u0900-\u097F]')

remaining_devanagari = {}
for k, v in te_flat.items():
    if devanagari_pat.search(str(v)):
        remaining_devanagari[k] = en_flat.get(k, '')

print(f"Total remaining Devanagari keys in te.json: {len(remaining_devanagari)}")
with open('scripts/remaining_problem_keys.json', 'w', encoding='utf-8') as f:
    json.dump(remaining_devanagari, f, indent=2, ensure_ascii=False)

# Group by namespace
ns_counts = {}
for k in remaining_devanagari:
    ns = k.split('.')[0]
    ns_counts[ns] = ns_counts.get(ns, 0) + 1

for ns, count in sorted(ns_counts.items(), key=lambda x: -x[1]):
    print(f"  {ns}: {count} keys")

print("\nSample remaining keys:")
for k, en_val in list(remaining_devanagari.items())[:10]:
    print(f"  {k} -> EN: {en_val}")
