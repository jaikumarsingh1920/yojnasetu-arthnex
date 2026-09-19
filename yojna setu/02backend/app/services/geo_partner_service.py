import math
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.models.partner import Partner
from app.models.partner_scheme import PartnerSchemeMapping
from app.engine.prudential_rule_engine import PrudentialRuleEngine


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance in kilometers between two points 
    on the earth (specified in decimal degrees).
    """
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return float('inf')

    # Convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])

    # Haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a)) 
    r = 6371 # Radius of earth in kilometers
    return c * r


class GeoPartnerLocatorService:
    calculate_haversine_distance = staticmethod(haversine_distance)

    @classmethod
    def evaluate_partner_financial_health(cls, db: Session, partner_id: str) -> Optional[Dict[str, Any]]:
        partner = db.execute(select(Partner).where(Partner.partner_id == partner_id)).scalars().first()
        if not partner:
            return None
        return PrudentialRuleEngine.evaluate_partner(db, partner)

    @classmethod
    def find_partners_with_routing_audit(
        cls,
        db: Session,
        latitude: float,
        longitude: float,
        radius_km: float = 100.0,
        max_npa: float = 10.0,
        partner_type: Optional[str] = None,
        partner_category: Optional[str] = None,
        district: Optional[str] = None,
        state: Optional[str] = None,
        pincode: Optional[str] = None,
        scheme_id: Optional[str] = None,
        loan_category: Optional[str] = None,
        service_type: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Comprehensive candidate partner evaluation, hard statutory restriction filtering,
        and smart multi-signal routing with transparent execution audit.
        
        Step 1: Find candidate partners using existing partner data.
        Step 2: Apply existing hard restrictions FIRST (NPA ceiling and statutory rules).
        Step 3: Only then rank remaining candidates by meaningful routing signals:
                - scheme/category compatibility
                - authorization/eligibility
                - verified financial/prudential status
                - geographical distance
        Step 4: Return transparent routing explanations and structured exclusion telemetry.
        """
        recommended_list: List[dict] = []
        excluded_list: List[dict] = []

        if scheme_id:
            # -------------------------------------------------------------
            # Explicit Scheme Mapping Query
            # -------------------------------------------------------------
            stmt = select(Partner, PartnerSchemeMapping).join(
                PartnerSchemeMapping,
                Partner.partner_id == PartnerSchemeMapping.partner_id
            ).where(
                Partner.is_active == True,
                Partner.record_status != "QUARANTINED",
                Partner.is_accepting_applications == True,
                Partner.verification_status.in_(["VERIFIED_OFFICIAL", "VERIFIED"]),
                Partner.coordinates_verified.isnot(False),
                Partner.latitude.isnot(None),
                Partner.longitude.isnot(None),
                PartnerSchemeMapping.scheme_id == scheme_id,
                PartnerSchemeMapping.verification_status.in_(["VERIFIED_OFFICIAL", "VERIFIED"])
            )
            
            if partner_type:
                stmt = stmt.where(Partner.partner_type == partner_type)
            
            if partner_category:
                stmt = stmt.where(Partner.partner_category == partner_category)

            if district:
                stmt = stmt.where(Partner.district.ilike(f"%{district}%"))

            if state:
                stmt = stmt.where(Partner.state.ilike(f"%{state}%"))

            if pincode:
                stmt = stmt.where(Partner.pincode == pincode.strip())

            if service_type:
                stmt = stmt.where(
                    (PartnerSchemeMapping.service_type == service_type) |
                    (Partner.service_type == service_type)
                )
            
            if loan_category:
                clean_cat = loan_category.strip().upper()
                if clean_cat in ("TERM_LOAN", "FINANCING", "CREDIT", "LOAN"):
                    stmt = stmt.where(
                        (PartnerSchemeMapping.authorized_category == clean_cat) |
                        (PartnerSchemeMapping.authorized_category.ilike(f"%{clean_cat}%")) |
                        (PartnerSchemeMapping.authorized_category == "AUTHORIZED_INSTITUTIONAL_CHANNEL") |
                        (PartnerSchemeMapping.service_type == "FINANCING") |
                        (PartnerSchemeMapping.authorized_category.is_(None))
                    )
                else:
                    stmt = stmt.where(
                        (PartnerSchemeMapping.authorized_category == clean_cat) |
                        (PartnerSchemeMapping.authorized_category.ilike(f"%{clean_cat}%")) |
                        (PartnerSchemeMapping.authorized_category.is_(None))
                    )

            records = db.execute(stmt).all()
            
            for p, mapping in records:
                dist = haversine_distance(latitude, longitude, p.latitude, p.longitude)
                if dist > radius_km:
                    continue
                dist_rounded = round(dist, 2)
                maps_url = f"https://www.google.com/maps/dir/?api=1&destination={p.latitude},{p.longitude}" if p.latitude and p.longitude else None

                # Step 2: Apply existing hard restrictions FIRST
                fin_eval = PrudentialRuleEngine.evaluate_partner(db, p)
                is_legacy_npa_restricted = (p.npa_percentage is not None and p.npa_percentage > max_npa)
                is_statutory_restricted = fin_eval.get("is_restricted", False)

                if is_legacy_npa_restricted or is_statutory_restricted:
                    if is_legacy_npa_restricted:
                        exclusion_reason = f"Partner reported Net NPA ({p.npa_percentage:.2f}%) breaches policy ceiling of {max_npa:.2f}%."
                    else:
                        exclusion_reason = fin_eval.get("primary_reason", "Statutory prudential restriction violated.")

                    excluded_list.append({
                        "partner": p,
                        "distance_km": dist_rounded,
                        "is_scheme_matched": True,
                        "partner_category": p.partner_category,
                        "supported_schemes": [mapping.scheme_id],
                        "service_type": mapping.service_type or p.service_type,
                        "authorization_level": mapping.authorization_level or p.scheme_authorization_level,
                        "scheme_authorized_category": mapping.authorized_category,
                        "scheme_mapping_notes": mapping.verification_notes,
                        "suitability_reason": f"Excluded from routing: {exclusion_reason}",
                        "lending_capacity_status": exclusion_reason,
                        "google_maps_url": maps_url,
                        "coordinate_precision": getattr(p, "coordinate_precision", "EXACT_ADDRESS") or "EXACT_ADDRESS",
                        "confidence": getattr(mapping, "confidence", "HIGH") or "HIGH",
                        "application_channel": mapping.service_type or p.service_type,
                        "routing_status": "NOT_ROUTABLE",
                        "institution_name": fin_eval.get("institution_name", p.name),
                        "entity_resolution_status": fin_eval.get("entity_resolution_status", "RESOLVED"),
                        "branch_location": fin_eval.get("branch_location", p.address or p.city or ""),
                        "financial_scope": "INSTITUTION_LEVEL",
                        "financial_intelligence": fin_eval.get("verified_metrics", {}),
                        "rules_evaluated": fin_eval.get("rules_evaluated", []),
                        "routing_reasons": [
                            f"Excluded from routing: {exclusion_reason}",
                            f"Located {dist_rounded} km away from citizen search location."
                        ],
                        "is_restricted": True,
                        "exclusion_reason": exclusion_reason
                    })
                    continue

                # Candidate is eligible for routing: Step 4 explanation synthesis
                routing_status = fin_eval.get("routing_status", "ROUTABLE_WITH_FINANCIAL_DATA_LIMITATION")
                fin_intel = fin_eval.get("verified_metrics", {})
                rules_eval = fin_eval.get("rules_evaluated", [])
                lending_status = fin_eval.get("primary_reason", "Officially authorized and active channel partner.")

                reasons = [
                    f"Officially authorized channel partner for selected scheme ({p.name})",
                    f"Located {dist_rounded} km away with verified branch coordinates ({p.district or p.city or 'branch'})",
                    lending_status
                ]
                if routing_status == "ROUTABLE_WITH_FINANCIAL_DATA_LIMITATION":
                    reasons.append("Partner-level utilization accounts and overdue ledgers are maintained internally in Ministry MIS and are not on open public portals.")

                supported = [m.scheme_id for m in p.scheme_mappings] if p.scheme_mappings else [scheme_id]

                recommended_list.append({
                    "partner": p,
                    "distance_km": dist_rounded,
                    "is_scheme_matched": True,
                    "partner_category": p.partner_category,
                    "supported_schemes": supported,
                    "service_type": mapping.service_type or p.service_type,
                    "authorization_level": mapping.authorization_level or p.scheme_authorization_level,
                    "scheme_authorized_category": mapping.authorized_category,
                    "scheme_mapping_notes": mapping.verification_notes,
                    "suitability_reason": ". ".join(reasons) + ".",
                    "lending_capacity_status": lending_status,
                    "google_maps_url": maps_url,
                    "coordinate_precision": getattr(p, "coordinate_precision", "EXACT_ADDRESS") or "EXACT_ADDRESS",
                    "confidence": getattr(mapping, "confidence", "HIGH") or "HIGH",
                    "application_channel": mapping.service_type or p.service_type,
                    "routing_status": routing_status,
                    "institution_name": fin_eval.get("institution_name", p.name),
                    "entity_resolution_status": fin_eval.get("entity_resolution_status", "RESOLVED"),
                    "branch_location": fin_eval.get("branch_location", p.address or p.city or ""),
                    "financial_scope": "INSTITUTION_LEVEL",
                    "financial_intelligence": fin_intel,
                    "rules_evaluated": rules_eval,
                    "routing_reasons": reasons,
                    "is_restricted": False,
                    "exclusion_reason": None
                })

            # Step 3: Multi-signal ranking for scheme routing
            def scheme_routing_sort_key(item):
                cat = item.get("partner_category") or ""
                cat_order = {
                    "AUTHORIZED_SCHEME_PARTNER": 0,
                    "IMPLEMENTING_ASSISTANCE_CENTRE": 1,
                    "TRAINING_HANDHOLDING_CENTRE": 2,
                    "NEARBY_FINANCIAL_SERVICE_POINT": 3,
                }
                cat_rank = cat_order.get(cat, 4)
                
                # Financial verification status: verified regulatory accounts prioritized
                status_val = item.get("routing_status") or ""
                fin_rank = 0 if status_val == "VERIFIED_ELIGIBLE_FOR_ROUTING" else 1
                
                # Geographical proximity
                dist_val = item.get("distance_km", float('inf'))
                
                # Geocoding precision
                prec = item.get("coordinate_precision") or ""
                prec_rank = 0 if prec == "EXACT_ADDRESS" else (1 if prec == "DISTRICT_HEADQUARTERS" else 2)
                
                return (not item.get("is_scheme_matched", False), cat_rank, fin_rank, dist_val, prec_rank)

            recommended_list.sort(key=scheme_routing_sort_key)

        else:
            # -------------------------------------------------------------
            # General Official Directory Query (no scheme filter)
            # -------------------------------------------------------------
            stmt = select(Partner).where(
                Partner.is_active == True,
                Partner.record_status != "QUARANTINED",
                Partner.is_accepting_applications == True,
                Partner.verification_status.in_(["VERIFIED_OFFICIAL", "VERIFIED"]),
                Partner.coordinates_verified.isnot(False),
                Partner.latitude.isnot(None),
                Partner.longitude.isnot(None)
            )
            if partner_type:
                stmt = stmt.where(Partner.partner_type == partner_type)

            if partner_category:
                stmt = stmt.where(Partner.partner_category == partner_category)

            if district:
                stmt = stmt.where(Partner.district.ilike(f"%{district}%"))

            if state:
                stmt = stmt.where(Partner.state.ilike(f"%{state}%"))

            if pincode:
                stmt = stmt.where(Partner.pincode == pincode.strip())

            if service_type:
                stmt = stmt.where(Partner.service_type == service_type)

            partners = db.execute(stmt).scalars().all()

            for p in partners:
                dist = haversine_distance(latitude, longitude, p.latitude, p.longitude)
                if dist > radius_km:
                    continue
                dist_rounded = round(dist, 2)
                maps_url = f"https://www.google.com/maps/dir/?api=1&destination={p.latitude},{p.longitude}" if p.latitude and p.longitude else None

                # Step 2: Apply existing hard restrictions FIRST
                fin_eval = PrudentialRuleEngine.evaluate_partner(db, p)
                is_legacy_npa_restricted = (p.npa_percentage is not None and p.npa_percentage > max_npa)
                is_statutory_restricted = fin_eval.get("is_restricted", False)

                if is_legacy_npa_restricted or is_statutory_restricted:
                    if is_legacy_npa_restricted:
                        exclusion_reason = f"Partner reported Net NPA ({p.npa_percentage:.2f}%) breaches policy ceiling of {max_npa:.2f}%."
                    else:
                        exclusion_reason = fin_eval.get("primary_reason", "Statutory prudential restriction violated.")

                    excluded_list.append({
                        "partner": p,
                        "distance_km": dist_rounded,
                        "is_scheme_matched": False,
                        "partner_category": p.partner_category,
                        "supported_schemes": [m.scheme_id for m in p.scheme_mappings] if p.scheme_mappings else [],
                        "service_type": p.service_type,
                        "authorization_level": p.scheme_authorization_level,
                        "scheme_authorized_category": None,
                        "scheme_mapping_notes": None,
                        "suitability_reason": f"Excluded from routing: {exclusion_reason}",
                        "lending_capacity_status": exclusion_reason,
                        "google_maps_url": maps_url,
                        "coordinate_precision": getattr(p, "coordinate_precision", "EXACT_ADDRESS") or "EXACT_ADDRESS",
                        "confidence": getattr(p, "geocoding_confidence", "HIGH") or "HIGH",
                        "application_channel": p.service_type,
                        "routing_status": "NOT_ROUTABLE",
                        "institution_name": fin_eval.get("institution_name", p.name),
                        "entity_resolution_status": fin_eval.get("entity_resolution_status", "RESOLVED"),
                        "branch_location": fin_eval.get("branch_location", p.address or p.city or ""),
                        "financial_scope": "INSTITUTION_LEVEL",
                        "financial_intelligence": fin_eval.get("verified_metrics", {}),
                        "rules_evaluated": fin_eval.get("rules_evaluated", []),
                        "routing_reasons": [
                            f"Excluded from routing: {exclusion_reason}",
                            f"Located {dist_rounded} km away from citizen search location."
                        ],
                        "is_restricted": True,
                        "exclusion_reason": exclusion_reason
                    })
                    continue

                # Non-restricted candidate
                routing_status = fin_eval.get("routing_status", "ROUTABLE_WITH_FINANCIAL_DATA_LIMITATION")
                fin_intel = fin_eval.get("verified_metrics", {})
                rules_eval = fin_eval.get("rules_evaluated", [])
                lending_status = fin_eval.get("primary_reason", "Officially authorized channel partner.")

                reasons = [
                    f"Official channel partner in government directory ({p.name})",
                    f"Located {dist_rounded} km away with verified branch coordinates",
                    lending_status
                ]
                if routing_status == "ROUTABLE_WITH_FINANCIAL_DATA_LIMITATION":
                    reasons.append("Current partner-level financial health data is managed internally in Ministry MIS.")

                supported = [m.scheme_id for m in p.scheme_mappings] if p.scheme_mappings else []

                recommended_list.append({
                    "partner": p,
                    "distance_km": dist_rounded,
                    "is_scheme_matched": False,
                    "partner_category": p.partner_category,
                    "supported_schemes": supported,
                    "service_type": p.service_type,
                    "authorization_level": p.scheme_authorization_level,
                    "scheme_authorized_category": None,
                    "scheme_mapping_notes": None,
                    "suitability_reason": ". ".join(reasons) + ".",
                    "lending_capacity_status": lending_status,
                    "google_maps_url": maps_url,
                    "coordinate_precision": getattr(p, "coordinate_precision", "EXACT_ADDRESS") or "EXACT_ADDRESS",
                    "confidence": getattr(p, "geocoding_confidence", "HIGH") or "HIGH",
                    "application_channel": p.service_type,
                    "routing_status": routing_status,
                    "institution_name": fin_eval.get("institution_name", p.name),
                    "entity_resolution_status": fin_eval.get("entity_resolution_status", "RESOLVED"),
                    "branch_location": fin_eval.get("branch_location", p.address or p.city or ""),
                    "financial_scope": "INSTITUTION_LEVEL",
                    "financial_intelligence": fin_intel,
                    "rules_evaluated": rules_eval,
                    "routing_reasons": reasons,
                    "is_restricted": False,
                    "exclusion_reason": None
                })

            # General directory query sorts strictly by distance ascending among routable partners
            recommended_list.sort(key=lambda x: x["distance_km"])

        summary = (
            f"Evaluated {len(recommended_list) + len(excluded_list)} candidate channel partners within {radius_km} km. "
            f"Recommended {len(recommended_list[:limit])} active eligible partners after applying statutory "
            f"prudential restrictions and scheme compatibility rules. "
            f"Excluded {len(excluded_list)} partner(s) due to verified statutory restrictions."
        )

        return {
            "recommended_partners": recommended_list[:limit],
            "excluded_partners": excluded_list,
            "total_evaluated": len(recommended_list) + len(excluded_list),
            "total_recommended": len(recommended_list),
            "total_excluded": len(excluded_list),
            "routing_summary": summary,
            "hard_restrictions_enforced": True
        }

    @classmethod
    def find_nearest_partners(
        cls,
        db: Session,
        latitude: float,
        longitude: float,
        radius_km: float = 100.0,
        max_npa: float = 10.0,
        partner_type: Optional[str] = None,
        partner_category: Optional[str] = None,
        district: Optional[str] = None,
        state: Optional[str] = None,
        pincode: Optional[str] = None,
        scheme_id: Optional[str] = None,
        loan_category: Optional[str] = None,
        service_type: Optional[str] = None,
        limit: int = 100,
        include_excluded: bool = False
    ) -> List[dict]:
        """
        Finds active, eligible channel partners within a radius, applying statutory prudential
        restrictions FIRST and ranking eligible candidates by multi-signal priority.
        If include_excluded is True, appends excluded candidates with structured exclusion reasons.
        """
        audit = cls.find_partners_with_routing_audit(
            db=db,
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            max_npa=max_npa,
            partner_type=partner_type,
            partner_category=partner_category,
            district=district,
            state=state,
            pincode=pincode,
            scheme_id=scheme_id,
            loan_category=loan_category,
            service_type=service_type,
            limit=limit
        )
        if include_excluded:
            return audit["recommended_partners"] + audit["excluded_partners"]
        return audit["recommended_partners"]

