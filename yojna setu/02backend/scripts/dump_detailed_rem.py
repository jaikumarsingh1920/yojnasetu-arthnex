import json
import os

with open('scripts/remaining_problem_keys.json', 'r', encoding='utf-8') as f:
    rem_keys = json.load(f)

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

detailed_rem = {}
for k in rem_keys:
    detailed_rem[k] = {
        'en': en_flat.get(k, ''),
        'hi': hi_flat.get(k, '')
    }

with open('scripts/detailed_remaining_187.json', 'w', encoding='utf-8') as f:
    json.dump(detailed_rem, f, indent=2, ensure_ascii=False)

print(f"Dumped {len(detailed_rem)} remaining keys to scripts/detailed_remaining_187.json")
