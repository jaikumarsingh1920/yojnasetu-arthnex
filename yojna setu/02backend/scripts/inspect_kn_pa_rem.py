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

dev_pat = re.compile(r'[\u0900-\u097F]')

for lang in ['kn', 'ml', 'gu', 'pa', 'or', 'as', 'bn']:
    with open(os.path.join(locales_dir, f"{lang}.json"), 'r', encoding='utf-8') as f:
        loc_flat = flatten(json.load(f))
    dev_keys = [k for k, v in loc_flat.items() if dev_pat.search(str(v))]
    print(f"Locale [{lang}]: {len(dev_keys)} keys with Devanagari")
    if lang == 'kn':
        print("Sample 13 keys in kn:")
        for k in dev_keys:
            print(f"  {k} -> {en_flat.get(k, '')}")

# Find union of all remaining keys across all 7 locales
all_rem = set()
for lang in ['kn', 'ml', 'gu', 'pa', 'or', 'as', 'bn']:
    with open(os.path.join(locales_dir, f"{lang}.json"), 'r', encoding='utf-8') as f:
        loc_flat = flatten(json.load(f))
    for k, v in loc_flat.items():
        if dev_pat.search(str(v)):
            all_rem.add(k)

print(f"\nTotal unique remaining keys across ALL languages: {len(all_rem)}")
with open('scripts/all_unique_rem_236.json', 'w', encoding='utf-8') as f:
    json.dump({k: {'en': en_flat.get(k, ''), 'hi': hi_flat.get(k, '')} for k in sorted(all_rem)}, f, indent=2, ensure_ascii=False)
