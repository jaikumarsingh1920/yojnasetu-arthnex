import json
import os

with open('scripts/problem_keys.json') as f:
    keys = json.load(f)

locales_dir = r'c:\Users\jaiku\OneDrive\Desktop\yojnasetu\yojna setu\01frontend\src\i18n\locales'
with open(os.path.join(locales_dir, 'en.json'), 'r', encoding='utf-8') as f:
    en_data = json.load(f)

def flatten(d, prefix=''):
    items = {}
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            items.update(flatten(v, key))
        else:
            items[key] = v
    return items

en_flat = flatten(en_data)

kv = {}
for k in keys:
    kv[k] = en_flat.get(k, '')

with open('scripts/problem_kv.json', 'w', encoding='utf-8') as f:
    json.dump(kv, f, indent=2, ensure_ascii=False)

print(f"Dumped {len(kv)} keys to scripts/problem_kv.json")
