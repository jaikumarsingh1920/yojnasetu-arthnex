import os
import sys
import json
import time
import requests
from datetime import datetime, timezone

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models.partner import Partner

CACHE_FILE = os.path.join(os.path.dirname(__file__), "nominatim_cache.json")
AUDIT_ARTIFACT_PATH = r"c:\Users\jaiku\.gemini\antigravity-ide\brain\aa994cfa-d45b-4acd-b5fb-bdebc9db6992\official_partners_geocoding_audit.json"

USER_AGENT = "YojnaSetu_SIH26092_PartnerLocator/1.0 (contact@yojnasetu.gov.in)"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8", errors="ignore") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading cache: {e}")
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

CLEANED_PARTNERS_PATH = r"c:\Users\jaiku\.gemini\antigravity-ide\brain\aa994cfa-d45b-4acd-b5fb-bdebc9db6992\scratch\cleaned_partners.json"

def load_cleaned_partner_texts():
    if os.path.exists(CLEANED_PARTNERS_PATH):
        with open(CLEANED_PARTNERS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def clean_query(partner_name, full_text):
    text = full_text or partner_name or ""
    import re
    # Look for 6-digit pin code
    pincode_match = re.search(r'\b\d{6}\b', text)
    pincode = pincode_match.group(0) if pincode_match else ""
    
    # Remove leading category numbers or duplicates
    cleaned = re.sub(r'^\d+\s+', '', text).strip()
    
    # Formulate a search query
    # E.g. "Tadepalli, Amaravathi - 522501, India"
    # Search with name + pincode + India or main address tokens
    tokens = [t.strip() for t in cleaned.split(',') if t.strip()]
    if pincode and len(tokens) > 1:
        query = f"{tokens[0]}, {pincode}, India"
    elif len(tokens) >= 2:
        query = f"{tokens[0]}, {tokens[-1]}, India"
    else:
        query = f"{cleaned[:80]}, India"
        
    return query, cleaned

def classify_nominatim_result(results, original_text):
    if not results or len(results) == 0:
        return "FAILED", None, None, "No results returned by Nominatim", "FAILED"
    
    first = results[0]
    lat = float(first.get("lat"))
    lon = float(first.get("lon"))
    display_name = first.get("display_name", "")
    address_info = first.get("address", {})
    addresstype = first.get("addresstype", "")
    place_class = first.get("class", "")
    place_type = first.get("type", "")
    
    country_code = address_info.get("country_code", "").lower()
    country = address_info.get("country", "").lower()
    
    if country_code != "in" and "india" not in country:
        return "FAILED", None, None, f"Result outside India ({display_name})", "FAILED"
    
    # Check if result is just country-level or broad state-level
    if addresstype in ["country", "state"] or place_type in ["country", "state"]:
        return "MEDIUM", None, None, f"Match too broad (state/country center: {display_name})", "MEDIUM"
    
    # High confidence: specific building, office, amenity, suburb, district, town, city, village, postcode
    if addresstype in ["building", "office", "amenity", "suburb", "neighbourhood", "quarter", "postcode", "city", "town", "village", "county", "district"]:
        return "HIGH", lat, lon, display_name, "HIGH"
    
    # Default to medium if ambiguous
    return "AMBIGUOUS", lat, lon, f"Ambiguous place type ({place_type}/{addresstype}: {display_name})", "AMBIGUOUS"

def run_geocoding_pipeline():
    db = SessionLocal()
    cache = load_cache()
    cleaned_items = load_cleaned_partner_texts()
    
    partners = db.query(Partner).filter(Partner.verification_status == "VERIFIED_OFFICIAL").all()
    print(f"Loaded {len(partners)} official partners for geocoding pipeline.")
    
    # Map cleaned text by index
    cleaned_map = {}
    for i, item in enumerate(cleaned_items):
        cleaned_map[i] = item.get("text", "")
    
    stats = {
        "total_official_partners": len(partners),
        "already_geocoded": 0,
        "successfully_geocoded": 0,
        "high_confidence": 0,
        "medium_confidence": 0,
        "low_confidence": 0,
        "ambiguous": 0,
        "failed": 0,
        "coordinates_verified_count": 0
    }
    
    audit_records = []
    headers = {"User-Agent": USER_AGENT}
    
    for idx, partner in enumerate(partners):
        full_text = cleaned_map.get(idx, partner.name)
        partner.verification_notes = full_text[:500] if full_text else None
        
        # Check if already geocoded with high confidence
        if partner.coordinates_verified and partner.latitude is not None and partner.longitude is not None:
            stats["already_geocoded"] += 1
            stats["coordinates_verified_count"] += 1
            audit_records.append({
                "partner_id": partner.partner_id,
                "partner_name": partner.name,
                "source_category": partner.source_category,
                "geocoding_status": "ALREADY_VERIFIED",
                "confidence": partner.geocoding_confidence or "HIGH",
                "latitude": partner.latitude,
                "longitude": partner.longitude,
                "provider": partner.geocoding_provider or "NOMINATIM",
                "display_name": partner.geocoding_display_name,
                "failure_reason": None
            })
            continue
            
        # Clean query
        query, text_used = clean_query(partner.name, full_text)
        
        # Check cache
        cache_key = f"nominatim_{query}"
        if cache_key in cache:
            results = cache[cache_key]
        else:
            print(f"[{idx}/{len(partners)}] Nominatim Request for: {partner.name[:40]}... Query: '{query}'")
            try:
                resp = requests.get(NOMINATIM_URL, params={"q": query, "format": "json", "addressdetails": 1}, headers=headers, timeout=10)
                if resp.status_code == 200:
                    results = resp.json()
                    cache[cache_key] = results
                    save_cache(cache)
                else:
                    print(f"  HTTP Error {resp.status_code} from Nominatim")
                    results = []
            except Exception as e:
                print(f"  Request failed: {e}")
                results = []
            
            # Rate limit 1.2 seconds
            time.sleep(1.2)
        
        # Classify
        classification, lat, lon, display_name_or_reason, confidence = classify_nominatim_result(results, full_text)
        
        now = datetime.now(timezone.utc)
        partner.geocoding_provider = "NOMINATIM"
        partner.geocoded_at = now
        partner.geocoding_query = query
        
        if classification == "HIGH" and lat is not None and lon is not None:
            partner.latitude = lat
            partner.longitude = lon
            partner.coordinates_verified = True
            partner.coordinates_source = "NOMINATIM_OSM_OFFICIAL_ADDRESS"
            partner.geocoding_status = "SUCCESS"
            partner.geocoding_confidence = "HIGH"
            partner.geocoding_display_name = display_name_or_reason
            
            stats["successfully_geocoded"] += 1
            stats["high_confidence"] += 1
            stats["coordinates_verified_count"] += 1
            
            failure_reason = None
        else:
            # Rule: Never invent coordinates. Keep NULL for non-HIGH confidence.
            partner.latitude = None
            partner.longitude = None
            partner.coordinates_verified = False
            partner.geocoding_status = classification
            partner.geocoding_confidence = confidence
            partner.geocoding_display_name = None
            
            failure_reason = display_name_or_reason
            if classification == "MEDIUM":
                stats["medium_confidence"] += 1
            elif classification == "AMBIGUOUS":
                stats["ambiguous"] += 1
            else:
                stats["failed"] += 1
                
        audit_records.append({
            "partner_id": partner.partner_id,
            "partner_name": partner.name,
            "source_category": partner.source_category,
            "geocoding_status": partner.geocoding_status,
            "confidence": partner.geocoding_confidence,
            "latitude": partner.latitude,
            "longitude": partner.longitude,
            "provider": partner.geocoding_provider,
            "display_name": partner.geocoding_display_name,
            "failure_reason": failure_reason
        })
    
    db.commit()
    db.close()
    
    # Save Audit Artifact JSON
    audit_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": stats,
        "records": audit_records
    }
    
    os.makedirs(os.path.dirname(AUDIT_ARTIFACT_PATH), exist_ok=True)
    with open(AUDIT_ARTIFACT_PATH, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2, ensure_ascii=False)
        
    print("\n==============================================")
    print("GEOCODING PIPELINE EXECUTION COMPLETE")
    print("==============================================")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    print(f"Audit artifact exported to: {AUDIT_ARTIFACT_PATH}")
    return stats

if __name__ == "__main__":
    run_geocoding_pipeline()
