import json
import os

with open(r'c:\Users\jaiku\OneDrive\Desktop\yojnasetu\yojna setu\02backend\scripts\problem_keys.json', 'r', encoding='utf-8') as f:
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

key_map = {}
for k in keys:
    key_map[k] = en_flat.get(k, '')

print(f"Total keys mapped: {len(key_map)}")

# Categorize into chunks or inspect namespaces
by_ns = {}
for k, v in key_map.items():
    ns = k.split('.')[0]
    if ns not in by_ns:
        by_ns[ns] = []
    by_ns[ns].append((k, v))

for ns, kvs in sorted(by_ns.items()):
    print(f"\nNamespace [{ns}] ({len(kvs)} keys):")
    for k, v in kvs[:3]:
        safe_v = v.encode('ascii', errors='replace').decode('ascii')
        print(f"  {k} = {safe_v}")
