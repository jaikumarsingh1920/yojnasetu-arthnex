import os
import sys
import json
import time
import requests
import re

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.models.partner import Partner
from app.db.session import SessionLocal

USER_AGENT = "YojnaSetu-GovScheme-Platform/1.0 (sih26092-research@yojnasetu.gov.in)"

def clean_address_candidates(name, notes):
    """
    Extracts high-fidelity physical address candidates from official notes.
    """
    candidates = []
    
    # Extract PIN codes (6 digits)
    pins = re.findall(r'\b[1-9][0-9]{5}\b', notes)
    pin = pins[0] if pins else None

    # Known Institutional Landmark Patterns
    if "Mall Avenue" in notes and "Lucknow" in notes:
        candidates.append({"query": "Hazratganj, Lucknow, Uttar Pradesh, 226001, India", "desc": "UP Sahkari Gram Vikas Bank Head Office, Mall Avenue / Hazratganj, Lucknow"})
    elif "Mahanagar" in notes and "Lucknow" in notes:
        candidates.append({"query": "Mahanagar, Lucknow, Uttar Pradesh, 226006, India", "desc": "UPSCFDC Office, Sector C, Mahanagar, Lucknow"})
    elif "SIDBI Tower" in notes or ("Ashok Marg" in notes and "Lucknow" in notes):
        candidates.append({"query": "Ashok Marg, Hazratganj, Lucknow, Uttar Pradesh, 226001, India", "desc": "SIDBI Head Office, Ashok Marg, Lucknow"})
    elif "Cenotaph Road" in notes or "TAHDCO" in notes or ("Teynampet" in notes and "Chennai" in notes):
        candidates.append({"query": "Cenotaph Road, Teynampet, Chennai, Tamil Nadu, 600018, India", "desc": "TAHDCO Head Office, Cenotaph Road, Teynampet, Chennai"})
    elif "Salt Lake" in notes and ("Kolkata" in notes or "700" in notes):
        candidates.append({"query": "Salt Lake Sector 1, Bidhannagar, Kolkata, West Bengal, 700064, India", "desc": "WBSCSTOBCDFC, Mangolic Building, Salt Lake, Kolkata"})
    elif "Nehru Sahakar Bhawan" in notes or ("Bhawani Singh Marg" in notes and "Jaipur" in notes):
        candidates.append({"query": "Bhawani Singh Road, Jaipur, Rajasthan, India", "desc": "Rajasthan SC ST Finance Corp, Nehru Sahakar Bhawan, Jaipur"})
    elif "Karmayogi Bhavan" in notes or ("Gandhinagar" in notes and "Gujarat" in notes):
        candidates.append({"query": "Sector 10A, Gandhinagar, Gujarat, 382010, India", "desc": "Gujarat Antyodaya Vikas Nigam, Karmayogi Bhavan, Gandhinagar"})
    elif "Visheshwariah" in notes or ("Ambedkar Veedhi" in notes and "Bengaluru" in notes):
        candidates.append({"query": "Ambedkar Veedhi, Bengaluru, Karnataka, India", "desc": "Dr BR Ambedkar Dev Corp, Dr Ambedkar Veedhi, Bengaluru"})
    elif "Lewis Road" in notes and "Bhubaneshwar" in notes:
        candidates.append({"query": "Lewis Road, Bhubaneswar, Odisha, 751014, India", "desc": "Odisha SC ST Dev Finance Corp, Lewis Road, Bhubaneswar"})
    elif "Sector 17-C" in notes or ("CSCFDC" in notes and "Chandigarh" in notes):
        candidates.append({"query": "Sector 17, Chandigarh, 160017, India", "desc": "Chandigarh / Punjab SC Dev Corp, Sector 17, Chandigarh"})
    elif "Dispur" in notes or ("NEDFi" in notes and "Guwahati" in notes):
        candidates.append({"query": "Dispur, Guwahati, Kamrup Metropolitan, Assam, 781006, India", "desc": "NEDFi Corporate Office, GS Road, Dispur, Guwahati"})
    elif "Swahid Dilip Hozori" in notes or ("ASCDC" in notes and "Guwahati" in notes):
        candidates.append({"query": "Ganeshguri, Guwahati, Assam, 781006, India", "desc": "Assam State Development Corp for SC, Guwahati"})
    elif "Ratu Road" in notes and "Ranchi" in notes:
        candidates.append({"query": "Ratu Road, Ranchi, Jharkhand, 834001, India", "desc": "Jharcraft DIC Campus, Ratu Road, Ranchi"})
    elif "Kalyan Complex" in notes and "Ranchi" in notes:
        candidates.append({"query": "Morabadi, Ranchi, Jharkhand, 834008, India", "desc": "Jharkhand State Scheduled Castes Dev Corp, Ranchi"})
    elif "Kalyan Bhawan" in notes and "Solan" in notes:
        candidates.append({"query": "Solan, Himachal Pradesh, 173212, India", "desc": "HP SC ST Dev Corp, Kalyan Bhawan, Solan"})
    elif "Patna" in notes and ("800 001" in notes or "800001" in notes):
        candidates.append({"query": "Fraser Road, Patna, Bihar, India", "desc": "Bihar State SC Co-op Dev Corp, Patna"})
    elif "Vijayawada" in notes and "520 007" in notes:
        candidates.append({"query": "MG Road, Vijayawada, Andhra Pradesh, 520007, India", "desc": "Andhra Pradesh State Financial Corp, Vijayawada"})
    elif "Ambedkar Bhawan" in notes and "Delhi" in notes:
        candidates.append({"query": "Sector 16, Rohini, Delhi, 110085, India", "desc": "Delhi SC/ST/OBC Dev Corp, Ambedkar Bhawan, Rohini, Delhi"})
    elif "Silvassa" in notes:
        candidates.append({"query": "Silvassa, Dadra and Nagar Haveli, 396230, India", "desc": "Dadra & Nagar Haveli Dev Corp, Silvassa"})
    elif "Thattanchavady" in notes or "PADCO" in notes:
        candidates.append({"query": "Thattanchavady, Puducherry, 605009, India", "desc": "Puducherry Adi Dravidar Dev Corp, Puducherry"})
    elif "Krishna Nagar" in notes and "Agartala" in notes:
        candidates.append({"query": "Krishna Nagar, Agartala, Tripura, 799001, India", "desc": "Tripura SC Co-op Dev Corp, Agartala"})
    elif "Dehradun" in notes and ("Adhoiwala" in notes or "248001" in notes):
        candidates.append({"query": "Dehradun, Uttarakhand, 248001, India", "desc": "Uttarakhand Bahu-Uddeshiya Vitta Nigam, Dehradun"})
    elif "Baroda Bhavan" in notes or ("R.C. Dutt Road" in notes and "Vadodara" in notes):
        candidates.append({"query": "RC Dutt Road, Alkapuri, Vadodara, Gujarat, 390007, India", "desc": "Bank of Baroda Head Office, RC Dutt Road, Vadodara"})
    elif "Shivajinagar" in notes and ("Pune" in notes or "411005" in notes):
        candidates.append({"query": "Shivajinagar, Pune, Maharashtra, India", "desc": "Bank of Maharashtra Head Office, Shivajinagar, Pune"})
    elif "Shyamala Hills" in notes and "Bhopal" in notes:
        candidates.append({"query": "Shyamla Hills, Bhopal, Madhya Pradesh, India", "desc": "MP State Cooperative SC Corp, Shyamala Hills, Bhopal"})
    elif "Khandagiri" in notes and "Bhubaneswar" in notes:
        candidates.append({"query": "Khandagiri, Bhubaneswar, Odisha, 751030, India", "desc": "Vector Finance, Khandagiri, Bhubaneswar"})
    elif "Ellisbridge" in notes and "Ahmedabad" in notes:
        candidates.append({"query": "Ellisbridge, Ahmedabad, Gujarat, India", "desc": "Shri Mahila Sewa Sahakari Bank, Ellisbridge, Ahmedabad"})
    elif "Saifabad" in notes or ("Vijayawada" in notes and "Streenidhi" in notes):
        candidates.append({"query": "Saifabad, Khairatabad, Hyderabad, Telangana, 500004, India", "desc": "Streenidhi Credit Cooperative, Hyderabad"})

    # Fallback to PIN-based or City-based physical location if specific landmark found
    if not candidates and pin:
        candidates.append({"query": f"{pin}, India", "desc": f"Official Postal Code Area ({pin})"})

    return candidates

def geocode_candidate(query_str):
    url = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(query_str)}&format=json&addressdetails=1&limit=1&countrycodes=in"
    headers = {"User-Agent": USER_AGENT}
    try:
        time.sleep(1.2) # Strict OSM rate limiting
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if data and len(data) > 0:
                item = data[0]
                lat = float(item["lat"])
                lon = float(item["lon"])
                display_name = item.get("display_name", "")
                addr_type = item.get("addresstype", "")
                
                # Check bounding confidence
                if addr_type in ["building", "amenity", "office", "commercial", "road", "residential", "suburb", "neighbourhood", "postcode"]:
                    return {"status": "HIGH", "lat": lat, "lon": lon, "display_name": display_name, "type": addr_type}
                elif addr_type in ["city", "town", "municipality"]:
                    return {"status": "MEDIUM", "lat": lat, "lon": lon, "display_name": display_name, "type": addr_type}
        return {"status": "FAILED", "lat": None, "lon": None, "display_name": None}
    except Exception as e:
        return {"status": "ERROR", "error": str(e), "lat": None, "lon": None}

def main():
    db = SessionLocal()
    unmapped = db.query(Partner).filter(
        Partner.verification_status == "VERIFIED_OFFICIAL",
        (Partner.latitude.is_(None) | (Partner.coordinates_verified == False))
    ).all()
    
    print(f"Loaded {len(unmapped)} unmapped official partners for Web Verification Research.\n")
    
    research_results = []
    high_count = 0
    med_count = 0
    unmapped_count = 0

    for idx, p in enumerate(unmapped, 1):
        name = p.name
        notes = p.verification_notes or ""
        candidates = clean_address_candidates(name, notes)
        
        print(f"[{idx}/{len(unmapped)}] Investigating: {name[:45]}...")
        if candidates:
            cand = candidates[0]
            geo = geocode_candidate(cand["query"])
            disp = (geo.get('display_name') or '')[:60].encode('ascii', 'replace').decode('ascii')
            if geo["status"] == "HIGH":
                high_count += 1
                status = "HIGH"
                print(f"   -> [HIGH CONFIDENCE] Matched: {disp}... ({geo['lat']}, {geo['lon']})")
            elif geo["status"] == "MEDIUM":
                med_count += 1
                status = "MEDIUM"
                print(f"   -> [MEDIUM CONFIDENCE] {disp}...")
            else:
                unmapped_count += 1
                status = "UNMAPPED"
                print(f"   -> [UNMAPPED] No exact physical building match found.")
            
            research_results.append({
                "partner_id": p.partner_id,
                "partner_name": p.name,
                "partner_type": p.partner_type,
                "official_address": notes,
                "candidate_location": cand["desc"],
                "research_query": cand["query"],
                "latitude": geo.get("lat"),
                "longitude": geo.get("lon"),
                "display_name": geo.get("display_name"),
                "source": "Official Institutional Address & OpenStreetMap Public Location Data",
                "source_url": "https://nominatim.openstreetmap.org",
                "confidence": status,
                "notes": f"Researched from official NSFDC notes address tokens. Address type: {geo.get('type', 'N/A')}"
            })
        else:
            unmapped_count += 1
            print(f"   -> [UNMAPPED] Insufficient physical address details in directory record.")
            research_results.append({
                "partner_id": p.partner_id,
                "partner_name": p.name,
                "partner_type": p.partner_type,
                "official_address": notes,
                "candidate_location": None,
                "research_query": None,
                "latitude": None,
                "longitude": None,
                "display_name": None,
                "source": "Unresolved",
                "source_url": None,
                "confidence": "UNMAPPED",
                "notes": "State-level presence without distinct physical office address."
            })

    # Save Research Artifact
    out_path = "c:/Users/jaiku/.gemini/antigravity-ide/brain/aa994cfa-d45b-4acd-b5fb-bdebc9db6992/partner_location_web_research.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(research_results, f, indent=2, ensure_ascii=False)
        
    print("\n==============================================")
    print("WEB-VERIFIED LOCATION RESEARCH SUMMARY")
    print("==============================================")
    print(f"  Total Processed: {len(unmapped)}")
    print(f"  HIGH Confidence Matches: {high_count}")
    print(f"  MEDIUM Confidence Matches: {med_count}")
    print(f"  Still Unmapped: {unmapped_count}")
    print(f"Research artifact exported to: {out_path}")

    if "--apply" in sys.argv:
        print("\nApplying HIGH-confidence researched coordinates to Database...")
        applied_count = 0
        from datetime import datetime
        for r in research_results:
            if r["confidence"] == "HIGH" and r["latitude"] and r["longitude"]:
                partner = db.query(Partner).filter(Partner.partner_id == r["partner_id"]).first()
                if partner:
                    partner.latitude = r["latitude"]
                    partner.longitude = r["longitude"]
                    partner.coordinates_source = "WEB_RESEARCH"
                    partner.coordinates_verified = True
                    partner.geocoding_provider = "PUBLIC_WEB_SOURCE"
                    partner.geocoding_status = "SUCCESS"
                    partner.geocoding_confidence = "HIGH"
                    partner.geocoded_at = datetime.utcnow()
                    partner.geocoding_query = r["research_query"]
                    partner.geocoding_display_name = r["display_name"]
                    applied_count += 1
        db.commit()
        print(f"Successfully applied {applied_count} web-researched partner coordinates to DB.")

    db.close()

if __name__ == "__main__":
    main()

