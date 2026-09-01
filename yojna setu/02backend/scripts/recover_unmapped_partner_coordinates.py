import os
import sys
import json
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import SessionLocal
from app.models.partner import Partner

MANUAL_DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'manual_partner_coordinate_verification.json'))

def run_recovery():
    print("==========================================================================")
    print("TASK-027: RECOVER UNMAPPED PARTNER COORDINATES (PROVENANCE & INTEGRITY)")
    print("==========================================================================")
    
    db = SessionLocal()
    try:
        # Load manual verification data if present
        manual_records = {}
        if os.path.exists(MANUAL_DATA_PATH):
            with open(MANUAL_DATA_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    manual_records[item['partner_code']] = item
            print(f"Loaded {len(manual_records)} verified curated partner locations.")

        official_partners = db.query(Partner).filter(Partner.verification_status == 'VERIFIED_OFFICIAL').all()
        print(f"Total official partners in DB: {len(official_partners)}")
        
        already_verified = [p for p in official_partners if p.coordinates_verified and p.latitude is not None and p.longitude is not None]
        unmapped = [p for p in official_partners if not (p.coordinates_verified and p.latitude is not None and p.longitude is not None)]
        
        print(f"Already verified: {len(already_verified)}")
        print(f"Unmapped candidates: {len(unmapped)}")
        
        recovered_count = 0
        unresolved_count = 0
        now = datetime.now(timezone.utc)
        
        for p in unmapped:
            # 1. Check if we have curated high/medium confidence physical location
            if p.code in manual_records:
                rec = manual_records[p.code]
                lat = float(rec['latitude'])
                lng = float(rec['longitude'])
                confidence = rec.get('confidence', 'HIGH')
                
                # Check confidence threshold (only HIGH and MEDIUM allowed)
                if confidence in ['HIGH', 'MEDIUM']:
                    p.latitude = lat
                    p.longitude = lng
                    p.coordinates_verified = True
                    p.coordinates_source = 'WEB_RESEARCH'
                    p.geocoding_provider = 'NOMINATIM_OSM'
                    p.geocoding_status = 'SUCCESS'
                    p.geocoding_confidence = confidence
                    p.geocoded_at = now
                    p.geocoding_query = rec.get('partner_name', p.name)
                    p.geocoding_display_name = rec.get('verification_notes')
                    p.verification_notes = rec.get('verification_notes')
                    if rec.get('source_url'):
                        p.source_url = rec['source_url']
                    if rec.get('source_name'):
                        p.source_category = rec['source_name']
                    
                    recovered_count += 1
                    print(f"  [RECOVERED] {p.code} -> ({lat}, {lng}) | {confidence} | {p.name[:45]}")
                    continue
            
            # 2. Record remains unmapped with documented reason
            p.latitude = None
            p.longitude = None
            p.coordinates_verified = False
            p.geocoding_status = 'UNRESOLVED_FRAGMENT_OR_GENERIC'
            p.geocoding_confidence = 'LOW'
            unresolved_count += 1
            print(f"  [REMAINS NULL] {p.code} -> Generic / Fragment record without specific branch address: {p.name[:45]}")

        db.commit()
        
        # Verify final state
        all_official = db.query(Partner).filter(Partner.verification_status == 'VERIFIED_OFFICIAL').all()
        final_mapped = [p for p in all_official if p.coordinates_verified and p.latitude is not None and p.longitude is not None]
        final_unmapped = [p for p in all_official if not (p.coordinates_verified and p.latitude is not None and p.longitude is not None)]
        
        print("\n==========================================================================")
        print("RECOVERY COMPLETE SUMMARY:")
        print(f"  Total official partners: {len(all_official)}")
        print(f"  Initially verified: {len(already_verified)}")
        print(f"  Newly recovered: {recovered_count}")
        print(f"  Final verified & mapped: {len(final_mapped)} / {len(all_official)}")
        print(f"  Legitimately unmapped: {len(final_unmapped)} / {len(all_official)}")
        print("==========================================================================")
        
    finally:
        db.close()

if __name__ == '__main__':
    run_recovery()
