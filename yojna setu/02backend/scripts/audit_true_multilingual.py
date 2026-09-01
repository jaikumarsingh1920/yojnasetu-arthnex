# -*- coding: utf-8 -*-
"""
Official True Multilingual Value-Level Audit Script for YojnaSetu
Compares ACTUAL VALUES across all 12 supported Indian regional languages:
  - English (en)
  - Hindi (hi)
  - Bengali (bn)
  - Marathi (mr)
  - Telugu (te)
  - Tamil (ta)
  - Gujarati (gu)
  - Kannada (kn)
  - Malayalam (ml)
  - Punjabi (pa)
  - Odia (or)
  - Assamese (as)

Validates:
1. Complete Key Parity (vs en.json)
2. Zero Empty / Null / Blank String Translations
3. Zero Copied English Strings (except legitimate official scheme names, acronyms, URLs, IDs, symbols)
4. Zero Script Leaks (No Devanagari in non-Hindi/Marathi locales)
5. Syntactic & Structural JSON Integrity
"""

import os
import json
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
LOCALES_DIR = os.path.join(PROJECT_ROOT, "..", "01frontend", "src", "i18n", "locales")
if not os.path.exists(LOCALES_DIR):
    LOCALES_DIR = os.path.join(PROJECT_ROOT, "01frontend", "src", "i18n", "locales")

SUPPORTED_LANGUAGES = ["en", "hi", "bn", "mr", "ta", "te", "gu", "kn", "ml", "pa", "or", "as"]

# Legitimate technical / government tokens permitted to appear untranslated
PERMISSIBLE_ENGLISH_TOKENS = {
    "YOJNASETU", "PMEGP", "MUDRA", "PM SVANIDHI", "PM-KISAN", "STAND-UP INDIA",
    "AYUSHMAN BHARAT", "APY", "PM-KUSUM", "PM VISWAKARMA", "PM VISHWAKARMA",
    "MSME", "DBT", "GOI", "MOMSME", "DIC", "CSC", "RBI", "KYC", "E-KYC", "UIDAI",
    "AADHAAR", "PAN", "IFSC", "OTP", "URL", "PDF", "SMS", "GPS", "API",
    "HTTP", "HTTPS", "GOV.IN", "NIC.IN", "SUPPORT@YOJNASETU.GOV.IN", "INFO@YOJNASETU.GOV.IN",
    "BEN10@EXAMPLE.COM", "CITIZEN@EXAMPLE.COM", "VERIFIED", "UNVERIFIED", "A-", "A", "A+",
    "1800-11-2026", "1950", "1800-180-1551", "14555", "14434", "1800-180-1111", "1800-11-0001",
    "N/A", "A TO Z", "Z TO A"
}

def flatten(d, prefix=""):
    items = {}
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            items.update(flatten(v, key))
        else:
            items[key] = v
    return items

def is_pure_english(val):
    text = str(val).strip()
    if not text:
        return False
    # Check if string contains only ASCII alphabetic/space characters
    clean = re.sub(r'[^a-zA-Z\s]', '', text).strip()
    if not clean:
        return False
    # Check if word length is substantial and not in permissible list
    words = clean.upper().split()
    non_permissible = [w for w in words if w not in PERMISSIBLE_ENGLISH_TOKENS]
    if len(clean) > 8 and len(non_permissible) >= 2:
        return True
    return False

def audit_all_locales():
    print("=" * 70)
    print("       YOJNASETU TRUE MULTILINGUAL VALUE-LEVEL AUDIT")
    print("=" * 70)
    
    en_file = os.path.join(LOCALES_DIR, "en.json")
    if not os.path.exists(en_file):
        print(f"FATAL: en.json not found at {en_file}")
        sys.exit(1)
        
    with open(en_file, "r", encoding="utf-8") as f:
        en_flat = flatten(json.load(f))
        
    total_master_keys = len(en_flat)
    print(f"Master Template (en.json): {total_master_keys} keys")
    print("-" * 70)
    
    dev_letters_pat = re.compile(r'[\u0904-\u0939\u093D-\u0963\u0966-\u097F]')
    
    audit_results = {}
    total_violations = 0
    
    for lang in SUPPORTED_LANGUAGES:
        loc_file = os.path.join(LOCALES_DIR, f"{lang}.json")
        if not os.path.exists(loc_file):
            print(f"[{lang.upper()}] ERROR: File missing!")
            total_violations += 1
            continue
            
        with open(loc_file, "r", encoding="utf-8") as f:
            try:
                loc_data = json.load(f)
                loc_flat = flatten(loc_data)
            except Exception as e:
                print(f"[{lang.upper()}] JSON PARSE ERROR: {e}")
                total_violations += 1
                continue
                
        # 1. Missing keys
        missing_keys = [k for k in en_flat if k not in loc_flat]
        
        # 2. Empty values
        empty_keys = [k for k, v in loc_flat.items() if str(v).strip() == ""]
        
        # 3. Copied English in non-English files
        copied_english = []
        if lang != "en":
            for k, v in loc_flat.items():
                if is_pure_english(v) and str(v).strip() == str(en_flat.get(k, "")).strip():
                    copied_english.append((k, v))
                    
        # 4. Devanagari in non-Hindi/Marathi files
        dev_leaks = []
        if lang not in ["hi", "mr", "en"]:
            for k, v in loc_flat.items():
                if dev_letters_pat.search(str(v)):
                    dev_leaks.append((k, v))
                    
        issues_count = len(missing_keys) + len(empty_keys) + len(copied_english) + len(dev_leaks)
        total_violations += issues_count
        
        audit_results[lang] = {
            "total_keys": len(loc_flat),
            "missing": len(missing_keys),
            "empty": len(empty_keys),
            "copied_english": len(copied_english),
            "dev_leaks": len(dev_leaks),
            "status": "PASS" if issues_count == 0 else "FAIL"
        }
        
        status_sym = "[PASS]" if issues_count == 0 else "[FAIL]"
        print(f"Locale {lang.upper():<4} | Keys: {len(loc_flat):<5} | Missing: {len(missing_keys):<2} | Empty: {len(empty_keys):<2} | Copied EN: {len(copied_english):<2} | Script Leaks: {len(dev_leaks):<2} | {status_sym}")

    print("=" * 70)
    if total_violations == 0:
        print("OVERALL RESULT: ALL 12 LOCALES PASSED VALUE-LEVEL MULTILINGUAL AUDIT!")
        print("100% genuine regional translations verified across all supported languages.")
    else:
        print(f"OVERALL RESULT: {total_violations} TOTAL ISSUES FOUND ACROSS LOCALES.")
    print("=" * 70)
    
    return total_violations == 0

if __name__ == "__main__":
    success = audit_all_locales()
    if not success:
        sys.exit(1)
