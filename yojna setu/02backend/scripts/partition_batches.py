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

with open('scripts/all_remaining_devanagari_keys.json', 'r', encoding='utf-8') as f:
    dev_keys = json.load(f)

print(f"Total keys to translate: {len(dev_keys)}")

# Let's inspect each namespace and dump them into individual JSON batches for high accuracy
batches = {}
for k, data in dev_keys.items():
    ns = k.split('.')[0]
    if ns not in batches:
        batches[ns] = {}
    batches[ns][k] = data

os.makedirs('scripts/translation_batches', exist_ok=True)
for ns, items in batches.items():
    batch_file = os.path.join('scripts/translation_batches', f"{ns}_batch.json")
    with open(batch_file, 'w', encoding='utf-8') as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
    print(f"Wrote batch '{ns}' ({len(items)} keys)")
