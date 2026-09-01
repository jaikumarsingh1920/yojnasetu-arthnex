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

with open(os.path.join(locales_dir, 'te.json'), 'r', encoding='utf-8') as f:
    te_flat = flatten(json.load(f))

with open(os.path.join(locales_dir, 'hi.json'), 'r', encoding='utf-8') as f:
    hi_flat = flatten(json.load(f))

devanagari_pat = re.compile(r'[\u0900-\u097F]')

problem_keys = []
for k, v in te_flat.items():
    if devanagari_pat.search(str(v)):
        problem_keys.append(k)

# Also check for pure English copied in any non-en locale
for lang in ['hi', 'bn', 'mr', 'ta', 'te', 'gu', 'kn', 'ml', 'pa', 'or', 'as']:
    with open(os.path.join(locales_dir, f"{lang}.json"), 'r', encoding='utf-8') as f:
        loc_flat = flatten(json.load(f))
    for k, v in loc_flat.items():
        if k in en_flat:
            en_v = str(en_flat[k]).strip()
            loc_v = str(v).strip()
            if en_v == loc_v and len(en_v) > 4 and re.search(r'[A-Za-z]{4,}', en_v):
                if k not in problem_keys:
                    problem_keys.append(k)

print(f"Total unique keys needing proper translation across all locales: {len(problem_keys)}")

with open(r'c:\Users\jaiku\OneDrive\Desktop\yojnasetu\yojna setu\02backend\scripts\problem_keys.json', 'w', encoding='utf-8') as f:
    json.dump(sorted(problem_keys), f, indent=2)

print("Sample problem keys with English and Hindi:")
for k in problem_keys[:10]:
    safe_en = str(en_flat.get(k, '')).encode('ascii', errors='replace').decode('ascii')
    print(f"{k} -> EN: {safe_en}")
