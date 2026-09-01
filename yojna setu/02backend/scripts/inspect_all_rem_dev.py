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

with open(os.path.join(locales_dir, 'en.json'), 'r', encoding='utf-8') as f:
    en_flat = flatten(json.load(f))

with open(os.path.join(locales_dir, 'hi.json'), 'r', encoding='utf-8') as f:
    hi_flat = flatten(json.load(f))

devanagari_pat = re.compile(r'[\u0900-\u097F]')

all_non_hi_mr = ['te', 'ta', 'kn', 'ml', 'gu', 'pa', 'or', 'as', 'bn']

remaining_dev_keys = set()
for lang in all_non_hi_mr:
    with open(os.path.join(locales_dir, f"{lang}.json"), 'r', encoding='utf-8') as f:
        loc_flat = flatten(json.load(f))
    for k, v in loc_flat.items():
        if devanagari_pat.search(str(v)):
            remaining_dev_keys.add(k)

print(f"Total remaining keys with Devanagari across non-Hindi/Marathi files: {len(remaining_dev_keys)}")

rem_dict = {}
for k in sorted(remaining_dev_keys):
    rem_dict[k] = {
        'en': en_flat.get(k, ''),
        'hi': hi_flat.get(k, '')
    }

with open('scripts/all_remaining_devanagari_keys.json', 'w', encoding='utf-8') as f:
    json.dump(rem_dict, f, indent=2, ensure_ascii=False)

# Breakdown by namespace
ns_map = {}
for k in remaining_dev_keys:
    ns = k.split('.')[0]
    ns_map[ns] = ns_map.get(ns, 0) + 1

for ns, count in sorted(ns_map.items(), key=lambda x: -x[1]):
    print(f"  {ns}: {count} keys")

for k in sorted(remaining_dev_keys)[:10]:
    print(f"  {k} -> EN: {en_flat.get(k, '')}")
