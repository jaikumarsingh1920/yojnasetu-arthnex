import math
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.models.partner import Partner
from app.models.partner_scheme import PartnerSchemeMapping


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
    @staticmethod
    def find_nearest_partners(
        db: Session,
        latitude: float,
        longitude: float,
        radius_km: float = 100.0,
        max_npa: float = 10.0,
        partner_type: Optional[str] = None,
        partner_category: Optional[str] = None,
        district: Optional[str] = None,
        state: Optional[str] = None,
        scheme_id: Optional[str] = None,
        loan_category: Optional[str] = None,
        service_type: Optional[str] = None,
        limit: int = 100
    ) -> List[dict]:
        """
        Finds active, verified official partners within a radius, filtered by NPA.
        If scheme_id is provided, filters strictly for partners with confirmed
        official authorizations in partner_scheme_mappings.
        """
        if scheme_id:
            # Explicit Scheme Mapping Query
            stmt = select(Partner, PartnerSchemeMapping).join(
                PartnerSchemeMapping,
                Partner.partner_id == PartnerSchemeMapping.partner_id
            ).where(
                Partner.is_active == True,
                Partner.is_accepting_applications == True,
                Partner.verification_status == 'VERIFIED_OFFICIAL',
                Partner.coordinates_verified.isnot(False),
                Partner.latitude.isnot(None),
                Partner.longitude.isnot(None),
                PartnerSchemeMapping.scheme_id == scheme_id,
                PartnerSchemeMapping.verification_status == 'VERIFIED_OFFICIAL'
            )
            
            if partner_type:
                stmt = stmt.where(Partner.partner_type == partner_type)
            
            if partner_category:
                stmt = stmt.where(Partner.partner_category == partner_category)

            if district:
                stmt = stmt.where(Partner.district.ilike(f"%{district}%"))

            if state:
                stmt = stmt.where(Partner.state.ilike(f"%{state}%"))

            if service_type:
                stmt = stmt.where(
                    (PartnerSchemeMapping.service_type == service_type) |
                    (Partner.service_type == service_type)
                )
            
            if loan_category:
                stmt = stmt.where(
                    (PartnerSchemeMapping.authorized_category == loan_category) |
                    (PartnerSchemeMapping.authorized_category.is_(None))
                )

            records = db.execute(stmt).all()
            
            results = []
            for p, mapping in records:
                if p.npa_percentage is not None and p.npa_percentage > max_npa:
                    continue

                dist = haversine_distance(latitude, longitude, p.latitude, p.longitude)
                if dist <= radius_km:
                    dist_rounded = round(dist, 2)
                    if p.npa_percentage is not None:
                        lending_status = f"Currently confirmed as available for lending (Verified NPA: {p.npa_percentage}%)"
                        npa_desc = f"Verified low NPA ({p.npa_percentage}%)"
                    else:
                        lending_status = "Current lending capacity/status not available from verified data"
                        npa_desc = "Current lending capacity/status not available from verified data"

                    reasons = [
                        "Officially authorized for this scheme",
                        f"Located {dist_rounded} km away",
                        npa_desc
                    ]

                    supported = [m.scheme_id for m in p.scheme_mappings] if p.scheme_mappings else [scheme_id]

                    results.append({
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
                        "lending_capacity_status": lending_status
                    })

            results.sort(key=lambda x: x["distance_km"])
            return results[:limit]

        else:
            # General Official Directory Query (no scheme filter)
            stmt = select(Partner).where(
                Partner.is_active == True,
                Partner.is_accepting_applications == True,
                Partner.verification_status == 'VERIFIED_OFFICIAL',
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

            if service_type:
                stmt = stmt.where(Partner.service_type == service_type)

            partners = db.execute(stmt).scalars().all()

            results = []
            for p in partners:
                if p.npa_percentage is not None and p.npa_percentage > max_npa:
                    continue

                dist = haversine_distance(latitude, longitude, p.latitude, p.longitude)
                if dist <= radius_km:
                    dist_rounded = round(dist, 2)
                    if p.npa_percentage is not None:
                        lending_status = f"Currently confirmed as available for lending (Verified NPA: {p.npa_percentage}%)"
                        npa_desc = f"Verified low NPA ({p.npa_percentage}%)"
                    else:
                        lending_status = "Current lending capacity/status not available from verified data"
                        npa_desc = "Current lending capacity/status not available from verified data"

                    reasons = [
                        "Official channel partner in government directory",
                        f"Located {dist_rounded} km away",
                        npa_desc
                    ]

                    supported = [m.scheme_id for m in p.scheme_mappings] if p.scheme_mappings else []

                    results.append({
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
                        "lending_capacity_status": lending_status
                    })

            results.sort(key=lambda x: x["distance_km"])
            return results[:limit]
