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
    te_data = json.load(f)
te_flat = flatten(te_data)

devanagari_pat = re.compile(r'[\u0900-\u097F]')

devanagari_keys = []
for k, v in te_flat.items():
    if devanagari_pat.search(str(v)):
        devanagari_keys.append(k)

print(f"Total Devanagari keys in te.json: {len(devanagari_keys)}")
# Group by top-level namespace
namespaces = {}
for k in devanagari_keys:
    ns = k.split('.')[0]
    namespaces[ns] = namespaces.get(ns, 0) + 1

print("Breakdown by namespace:")
for ns, count in sorted(namespaces.items(), key=lambda x: -x[1]):
    print(f"  {ns}: {count} keys")

print("\nSample keys in te.json:")
for k in devanagari_keys[:15]:
    print(f"  {k}")
