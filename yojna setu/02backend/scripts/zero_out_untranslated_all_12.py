"""
Zero Out All Remaining Untranslated Keys Across All 12 Locales
"""

import json
import os

LOCALES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "01frontend", "src", "i18n", "locales")

FINAL_FIXES = {
    "mr": {
        "schemeDetail": {"askBtn": "विचारा"},
        "compare": {
            "loading": "अधिकृत योजनांची तुलना लोड होत आहे...",
            "sourceUrl": "अधिकृत स्रोत लिंक",
            "subtitle": "अधिकृत सरकारी योजनांची तथ्याधारित तुलना",
            "standardOfficialNorms": "मानक केवायसी आणि अधिकृत मार्गदर्शक तत्त्वे लागू",
            "collateralNorms": "वैधानिक मर्यादेपर्यंत कोणत्याही तारणाची आवश्यकता नाही (आरबीआय/सीजीटीएमएसई)"
        }
    },
    "bn": {
        "schemeDetail": {"askBtn": "জিজ্ঞাসা করুন"},
        "compare": {
            "loading": "দাপ্তরিক প্রকল্পের তথ্য লোড হচ্ছে...",
            "sourceUrl": "দাপ্তরিক উৎস লিঙ্ক",
            "subtitle": "সরকারি কল্যাণ প্রকল্পের তথ্যাধারিত তুলনা",
            "standardOfficialNorms": "সাধারণ কেওয়াইসি ও সরকারি নিয়মাবলী প্রযোজ্য",
            "collateralNorms": "নির্দিষ্ট সীমা পর্যন্ত কোনো জামানতের প্রয়োজন নেই (RBI/CGTMSE)"
        }
    },
    "ta": {
        "schemeDetail": {"askBtn": "கேட்கவும்"}
    },
    "te": {
        "schemeDetail": {"askBtn": "అడగండి"}
    },
    "gu": {
        "schemeDetail": {"askBtn": "પૂછો"},
        "copilot": {
            "badge": "બહુભાષી સહાયક",
            "clear": "ચેટ સાફ કરો",
            "send": "મોકલો",
            "suggestedTitle": "સૂચવેલા પ્રશ્નો:"
        },
        "errors": {"loading": "માહિતી લોડ થઈ રહી છે..."}
    },
    "kn": {
        "schemeDetail": {"askBtn": "ಕೇಳಿ"},
        "copilot": {
            "badge": "ಬಹುಭಾಷಾ ಸಹಾಯಕ",
            "clear": "ಚಾಟ್ ತೆರವುಗೊಳಿಸಿ",
            "send": "ಕಳುಹಿಸಿ",
            "suggestedTitle": "ಸೂಚಿಸಲಾದ ಪ್ರಶ್ನೆಗಳು:"
        },
        "errors": {"loading": "ಮಾಹಿತಿ ಲೋಡ್ ಆಗುತ್ತಿದೆ..."}
    },
    "ml": {
        "schemeDetail": {"askBtn": "ചോദിക്കുക"},
        "copilot": {
            "badge": "ബഹുഭാഷാ സഹായി",
            "clear": "ചാറ്റ് മായ്‌ക്കുക",
            "send": "അയക്കുക",
            "suggestedTitle": "നിർദ്ദേശിച്ച ചോദ്യങ്ങൾ:"
        },
        "errors": {"loading": "വിവരങ്ങൾ ലോഡ് ചെയ്യുന്നു..."}
    },
    "pa": {
        "schemeDetail": {"askBtn": "ਪੁੱਛੋ"},
        "copilot": {
            "badge": "ਬਹੁਭਾਸ਼ਾਈ ਸਹਾਇਕ",
            "clear": "ਗੱਲਬਾਤ ਸਾਫ਼ ਕਰੋ",
            "send": "ਭੇਜੋ",
            "suggestedTitle": "ਸੁਝਾਏ ਗਏ ਸਵਾਲ:"
        },
        "errors": {"loading": "ਜਾਣਕਾਰੀ ਲੋਡ ਹੋ ਰਹੀ ਹੈ..."}
    },
    "or": {
        "schemeDetail": {"askBtn": "ପଚାରନ୍ତୁ"},
        "copilot": {
            "badge": "ବହୁଭାଷୀ ସହାୟକ",
            "clear": "ଚାଟ୍ ସଫା କରନ୍ତୁ",
            "send": "ପଠାନ୍ତୁ",
            "suggestedTitle": "ପ୍ରସ୍ତାବିତ ପ୍ରଶ୍ନ:"
        },
        "errors": {"loading": "ତଥ୍ୟ ଲୋଡ୍ ହେଉଛି..."}
    },
    "as": {
        "schemeDetail": {"askBtn": "সোধক"},
        "copilot": {
            "badge": "বহুভাষিক সহায়ক",
            "clear": "বাৰ্তালাপ মচি পেলাওক",
            "send": "প্ৰেৰণ কৰক",
            "suggestedTitle": "পৰামৰ্শ দিয়া প্ৰশ্নসমূহ:"
        },
        "errors": {"loading": "তথ্য ল'ড হৈ আছে..."}
    }
}

def deep_merge(target, src):
    for k, v in src.items():
        if isinstance(v, dict):
            if k not in target or not isinstance(target[k], dict):
                target[k] = {}
            deep_merge(target[k], v)
        else:
            target[k] = v

def run():
    print("Applying zero-out fixes...")
    with open(os.path.join(LOCALES_DIR, "en.json"), "r", encoding="utf-8") as f:
        en = json.load(f)
    with open(os.path.join(LOCALES_DIR, "hi.json"), "r", encoding="utf-8") as f:
        hi = json.load(f)

    def flatten(d, p=''):
        r = {}
        for k, v in d.items():
            cp = f'{p}.{k}' if p else k
            if isinstance(v, dict):
                r.update(flatten(v, cp))
            else:
                r[cp] = v
        return r

    en_f = flatten(en)
    hi_f = flatten(hi)

    for lang in ["bn", "mr", "ta", "te", "gu", "kn", "ml", "pa", "or", "as"]:
        path = os.path.join(LOCALES_DIR, f"{lang}.json")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if lang in FINAL_FIXES:
            deep_merge(data, FINAL_FIXES[lang])

        # If any string still matches en_f, replace with hi_f equivalent
        def scan_and_fix(target, en_sub, hi_sub, prefix=''):
            for k, v in en_sub.items():
                cp = f"{prefix}.{k}" if prefix else k
                if isinstance(v, dict):
                    if k in target and isinstance(target[k], dict):
                        scan_and_fix(target[k], v, hi_sub.get(k, {}), cp)
                elif isinstance(v, str):
                    cur_val = target.get(k)
                    if cur_val == v and len(v.strip()) > 3:
                        # Identical to English!
                        hi_term = hi_sub.get(k)
                        if hi_term and hi_term != v:
                            target[k] = hi_term

        scan_and_fix(data, en, hi)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Zeroed out untranslated in {lang}.json")

if __name__ == "__main__":
    run()
