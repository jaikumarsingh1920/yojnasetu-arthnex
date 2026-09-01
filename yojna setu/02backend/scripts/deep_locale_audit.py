import os
import json
import re

locales_dir = r'c:\Users\jaiku\OneDrive\Desktop\yojnasetu\yojna setu\01frontend\src\i18n\locales'

supported_langs = ['en', 'hi', 'bn', 'mr', 'ta', 'te', 'gu', 'kn', 'ml', 'pa', 'or', 'as']

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
        return False
    if v in permissible_english:
        return True
    if re.match(r"^[\d\s\.,₹%/\-\+•✓✕⚠:()@]+$", v):
        return True
    if v.startswith("http://") or v.startswith("https://") or "@" in v:
        return True
    return False

# Unicode script ranges for target languages
scripts = {
    'hi': r'[\u0900-\u097F]', # Devanagari
    'mr': r'[\u0900-\u097F]', # Devanagari
    'bn': r'[\u0980-\u09FF]', # Bengali
    'as': r'[\u0980-\u09FF]', # Assamese (uses Bengali script with unique chars)
    'ta': r'[\u0B80-\u0BFF]', # Tamil
    'te': r'[\u0C00-\u0C7F]', # Telugu
    'kn': r'[\u0C80-\u0CFF]', # Kannada
    'ml': r'[\u0D00-\u0D7F]', # Malayalam
    'gu': r'[\u0A80-\u0AFF]', # Gujarati
    'pa': r'[\u0A00-\u0A7F]', # Gurmukhi (Punjabi)
    'or': r'[\u0B00-\u0B7F]', # Odia
}

for lang in supported_langs:
    if lang == 'en':
        continue
    loc_file = os.path.join(locales_dir, f"{lang}.json")
    with open(loc_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    flat = flatten(data)
    
    missing = []
    empty = []
    identical_to_en = []
    no_native_script = []

    pattern = re.compile(scripts[lang])

    for k, en_val in en_flat.items():
        if k not in flat:
            missing.append(k)
        else:
            val = str(flat[k]).strip()
            if not val:
                empty.append(k)
            elif val == str(en_val).strip() and not is_permissible(val):
                identical_to_en.append((k, val))
            elif not is_permissible(val) and not pattern.search(val):
                # Has Latin letters and no native script characters
                if re.search(r'[A-Za-z]{3,}', val):
                    no_native_script.append((k, val))

    print(f"=== {lang.upper()} Audit ===")
    print(f"Total keys: {len(flat)} | Missing: {len(missing)} | Empty: {len(empty)}")
    print(f"Identical to English (not permissible): {len(identical_to_en)}")
    print(f"Contains Latin with zero native script: {len(no_native_script)}")
    if identical_to_en[:3]:
        safe_id = [(k, v[:30].encode('ascii', errors='replace').decode('ascii')) for k, v in identical_to_en[:3]]
        print("  Sample identical:", safe_id)
    if no_native_script[:3]:
        safe_no = [(k, v[:30].encode('ascii', errors='replace').decode('ascii')) for k, v in no_native_script[:3]]
        print("  Sample no native script:", safe_no)
    print()
