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

scripts = {
    'hi': (r'[\u0900-\u097F]', 'Devanagari'),
    'mr': (r'[\u0900-\u097F]', 'Devanagari'),
    'bn': (r'[\u0980-\u09FF]', 'Bengali'),
    'as': (r'[\u0980-\u09FF]', 'Assamese/Bengali'),
    'ta': (r'[\u0B80-\u0BFF]', 'Tamil'),
    'te': (r'[\u0C00-\u0C7F]', 'Telugu'),
    'kn': (r'[\u0C80-\u0CFF]', 'Kannada'),
    'ml': (r'[\u0D00-\u0D7F]', 'Malayalam'),
    'gu': (r'[\u0A80-\u0AFF]', 'Gujarati'),
    'pa': (r'[\u0A00-\u0A7F]', 'Gurmukhi'),
    'or': (r'[\u0B00-\u0B7F]', 'Odia'),
}

permissible_english = {
    "PMEGP", "MUDRA", "PM SVANidhi", "Stand-Up India", "PM Vishwakarma",
    "PM-YASASVI", "Ayushman Bharat", "AB-PMJAY", "APY", "PMSBY", "PMJJBY",
    "CGTMSE", "KCC", "NLM", "PM-KUSUM", "NMMS", "PMMVY", "SSY", "NSFDC",
    "YojnaSetu", "LIVE", "PDF", "API", "RAG", "SIH", "GOI", "MoMSME", "MoA&FW",
    "MSME", "DBT", "Aadhaar", "PAN", "IFSC", "URL", "Email", "SMS", "OTP",
    "Shishu", "Kishore", "Tarun", "General", "OBC", "SC", "ST", "EWS",
    "YES", "NO", "NA", "N/A", "₹", "%", "/", "•", "✓", "✕", "⚠",
    "1800-11-2026", "support@yojnasetu.gov.in", "yojnasetu.gov.in"
}

def is_permissible(val):
    v = str(val).strip()
    if not v:
        return True
    if v in permissible_english:
        return True
    if re.match(r"^[\d\s\.,₹%/\-\+•✓✕⚠:()@\<\>\{\}\|_#\*]+$", v):
        return True
    if v.startswith("http://") or v.startswith("https://") or "@" in v:
        return True
    return False

results = {}

for lang, (regex_str, script_name) in scripts.items():
    loc_file = os.path.join(locales_dir, f"{lang}.json")
    with open(loc_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    flat = flatten(data)
    
    pat = re.compile(regex_str)
    devanagari_pat = re.compile(r'[\u0900-\u097F]')
    
    english_copied = []
    devanagari_in_non_devanagari = []
    
    for k, val in flat.items():
        v_str = str(val).strip()
        if is_permissible(v_str):
            continue
        
        # Check if contains English words (3+ chars)
        # remove placeholders like {{count}}, {{name}}, etc.
        v_no_placeholders = re.sub(r'\{\{.*?\}\}', '', v_str)
        
        has_native = bool(pat.search(v_no_placeholders))
        has_english = bool(re.search(r'[A-Za-z]{3,}', v_no_placeholders))
        has_devanagari = bool(devanagari_pat.search(v_no_placeholders))
        
        # If the language is NOT hi or mr, but has Devanagari and NO native script
        if lang not in ['hi', 'mr'] and has_devanagari and not has_native:
            devanagari_in_non_devanagari.append((k, v_str))
        elif not has_native and has_english:
            english_copied.append((k, v_str))
            
    results[lang] = {
        'total': len(flat),
        'english_copied': english_copied,
        'devanagari_copied': devanagari_in_non_devanagari
    }

print("=== SCRIPT INTEGRITY & COPIED TRANSLATION AUDIT ===")
for lang, res in results.items():
    print(f"\nLanguage: {lang.upper()} (Total keys: {res['total']})")
    print(f"  - Pure English copied: {len(res['english_copied'])}")
    print(f"  - Devanagari copied into non-Hindi/Marathi: {len(res['devanagari_copied'])}")
    if res['english_copied']:
        print("    Sample English copied:")
        for k, v in res['english_copied'][:5]:
            safe_v = v[:50].encode('ascii', errors='replace').decode('ascii')
            print(f"      * {k}: {safe_v}")
    if res['devanagari_copied']:
        print("    Sample Devanagari copied:")
        for k, v in res['devanagari_copied'][:5]:
            safe_v = v[:50].encode('ascii', errors='replace').decode('ascii')
            print(f"      * {k}: {safe_v}")
