import os
import json
import re

locales_dir = r'c:\Users\jaiku\OneDrive\Desktop\yojnasetu\yojna setu\01frontend\src\i18n\locales'
supported_langs = ['en', 'hi', 'bn', 'mr', 'ta', 'te', 'gu', 'kn', 'ml', 'pa', 'or', 'as']

def flatten(d, prefix=''):
    items = {}
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            items.update(flatten(v, key))
        else:
            items[key] = v
    return items

permissible_english = {
    "PMEGP", "MUDRA", "PM SVANidhi", "Stand-Up India", "PM Vishwakarma",
    "PM-YASASVI", "Ayushman Bharat", "AB-PMJAY", "APY", "PMSBY", "PMJJBY",
    "CGTMSE", "KCC", "NLM", "PM-KUSUM", "NMMS", "PMMVY", "SSY", "NSFDC",
    "YojnaSetu", "LIVE", "PDF", "API", "RAG", "SIH", "GOI", "MoMSME", "MoA&FW",
    "MSME", "DBT", "Aadhaar", "PAN", "IFSC", "URL", "Email", "SMS", "OTP",
    "Shishu", "Kishore", "Tarun", "General", "OBC", "SC", "ST", "EWS",
    "YES", "NO", "NA", "N/A", "₹", "%", "/", "•", "✓", "✕", "⚠"
}

def is_permissible(val):
    v = str(val).strip()
    if not v:
        return True
    if v in permissible_english:
        return True
    if re.match(r"^[\d\s\.,₹%/\-\+•✓✕⚠:()@]+$", v):
        return True
    if v.startswith("http://") or v.startswith("https://") or "@" in v:
        return True
    return False

scripts = {
    'hi': r'[\u0900-\u097F]',
    'mr': r'[\u0900-\u097F]',
    'bn': r'[\u0980-\u09FF]',
    'as': r'[\u0980-\u09FF]',
    'ta': r'[\u0B80-\u0BFF]',
    'te': r'[\u0C00-\u0C7F]',
    'kn': r'[\u0C80-\u0CFF]',
    'ml': r'[\u0D00-\u0D7F]',
    'gu': r'[\u0A80-\u0AFF]',
    'pa': r'[\u0A00-\u0A7F]',
    'or': r'[\u0B00-\u0B7F]',
}

latin_untranslated = {}

for lang in supported_langs:
    if lang == 'en':
        continue
    loc_file = os.path.join(locales_dir, f"{lang}.json")
    with open(loc_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    flat = flatten(data)
    
    pat = re.compile(scripts[lang])
    latin_untranslated[lang] = []
    
    for k, val in flat.items():
        val_str = str(val).strip()
        if not is_permissible(val_str) and not pat.search(val_str):
            if re.search(r'[A-Za-z]{3,}', val_str):
                latin_untranslated[lang].append((k, val_str))

print("=== DETAILED BREAKDOWN OF UNTRANSLATED KEYS WITH ZERO NATIVE SCRIPT ===")
for lang, items in latin_untranslated.items():
    print(f"\nLanguage [{lang}]: {len(items)} keys")
    for k, v in items:
        clean_v = v.encode('ascii', errors='replace').decode('ascii')
        print(f"  {k} = \"{clean_v}\"")
