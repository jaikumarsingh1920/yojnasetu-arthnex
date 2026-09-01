import os
import json
import re

# Devanagari letters and digits, excluding common Indic punctuation (danda \u0964, \u0965)
devanagari_letters_pat = re.compile(r'[\u0904-\u0939\u093D-\u0963\u0966-\u097F]')

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

print("=== AUDIT OF DEVANAGARI TEXT IN NON-HINDI/MARATHI LOCALES ===")
non_hi_mr = ['te', 'ta', 'kn', 'ml', 'gu', 'pa', 'or', 'as', 'bn']

remaining_real_dev = {}
for lang in non_hi_mr:
    with open(os.path.join(locales_dir, f"{lang}.json"), 'r', encoding='utf-8') as f:
        loc_flat = flatten(json.load(f))
    real_dev_keys = [k for k, v in loc_flat.items() if devanagari_letters_pat.search(str(v))]
    print(f"Locale [{lang}]: {len(real_dev_keys)} keys with actual Devanagari letters")
    if real_dev_keys:
        for k in real_dev_keys:
            remaining_real_dev[k] = en_flat.get(k, '')
            print(f"   * {k} -> {en_flat.get(k, '')}")

print(f"\nTotal unique keys with actual Devanagari letters across all non-Hindi/Marathi files: {len(remaining_real_dev)}")
