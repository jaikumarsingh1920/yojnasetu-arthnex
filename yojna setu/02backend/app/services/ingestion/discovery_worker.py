import uuid
import json
import logging
import urllib.parse
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor
import httpx
from sqlalchemy.orm import Session

import os
from app.core.config import settings
from app.models.scheme import Scheme
from app.models.candidate import CandidateScheme
from app.services.ingestion.fetcher import HTMLFetcher, PDFFetcher, FetchResult
from app.services.ingestion.extractor import OfficialGovHTMLExtractor
from app.services.ingestion.pdf_extractor import OfficialGovPDFExtractor
from app.services.ingestion.normalizer import SchemeDataNormalizer
from app.services.ingestion.validator import SchemeDataValidator
from app.services.ingestion.relevance_classifier import SchemeRelevanceClassifier
from app.services.ingestion.source_resolver import OfficialSourceResolver
from app.services.ingestion.deduplicator import SchemeDeduplicator

logger = logging.getLogger("yojnasetu.ingestion.discovery_worker")


def get_myscheme_api_key() -> Optional[str]:
    """Retrieves myScheme API Key safely from application settings or environment variables."""
    return settings.MYSCHEME_API_KEY or os.getenv("MYSCHEME_API_KEY")


MYSCHEME_SEARCH_URL = "https://api.myscheme.gov.in/search/v6/schemes"
MYSCHEME_DETAILS_URL = "https://api.myscheme.gov.in/schemes/v6/public/schemes"

PRIORITY_CATEGORIES = [
    "Business & Entrepreneurship",
    "Agriculture,Rural & Environment",
    "Banking,Financial Services and Insurance",
    "Skills & Employment",
    "Social welfare & Empowerment",
    "Women and Child",
    "Housing & Shelter",
]


def stringify_field(val) -> str:
    """Robust stringifier for raw JSON values that may be string, list of strings, or list of dicts."""
    if not val:
        return ""
    if isinstance(val, str):
        return val.strip()
    if isinstance(val, dict):
        return str(val.get("label") or val.get("value") or val.get("name") or val).strip()
    if isinstance(val, (list, tuple, set)):
        items = []
        for x in val:
            if isinstance(x, dict):
                s = str(x.get("label") or x.get("value") or x.get("name") or x).strip()
                if s:
                    items.append(s)
            elif x is not None:
                s = str(x).strip()
                if s:
                    items.append(s)
        return ", ".join(items)
    return str(val).strip()


class SchemeDiscoveryCatalog:
    """
    Authoritative Government Scheme Discovery Seed Catalog.
    Provides structured discovery entries across Central Ministries, Implementing Agencies,
    and State/UT portals covering YojnaSetu's 7 priority sectors.
    """

    OFFICIAL_DISCOVERY_CATALOG: List[Dict[str, Any]] = [
        # --- PRIORITY 1 & 2: Central Ministries & Implementing Agencies (MSME / Marginalized) ---
        {
            "name": "PM Young Achievers Scholarship Award Scheme for Vibrant India (PM-YASASVI)",
            "code": "PM-YASASVI",
            "ministry": "Ministry of Social Justice and Empowerment",
            "implementing_agency": "Department of Social Justice and Empowerment",
            "level": "CENTRAL_SECTOR",
            "state_coverage": "All India",
            "category": "OBC/EBC/DNT Education & Self-Reliance",
            "target_beneficiaries": "OBC, EBC, DNT Students and Youth",
            "stated_benefits": "Full scholarship, boarding expenses, and skill development support up to ₹1,25,000 per annum for higher secondary and vocational education.",
            "official_source_url": "https://socialjustice.gov.in/schemes/31",
            "source_type": "HTML",
            "discovery_source": "CENTRAL_MINISTRY",
        },
        {
            "name": "Scheme for Residential Education for Students in High Schools in Targeted Areas (SHRESHTA)",
            "code": "SHRESHTA",
            "ministry": "Ministry of Social Justice and Empowerment",
            "implementing_agency": "Department of Social Justice and Empowerment / NTA",
            "level": "CENTRAL_SECTOR",
            "state_coverage": "All India",
            "category": "SC Quality Education & Human Capital",
            "target_beneficiaries": "Scheduled Caste meritorious students",
            "stated_benefits": "High quality residential schooling covering full school fees and hostel fees for SC students from family income up to ₹2.5 Lakh.",
            "official_source_url": "https://shreshta.admissions.nic.in/",
            "source_type": "HTML",
            "discovery_source": "CENTRAL_MINISTRY",
        },
        {
            "name": "NMDFC Virasat Scheme for Craftspersons and Artisans",
            "code": "NMDFC-VIRASAT",
            "ministry": "Ministry of Minority Affairs",
            "implementing_agency": "National Minorities Development and Finance Corporation (NMDFC)",
            "level": "CENTRAL_SECTOR",
            "state_coverage": "All India",
            "category": "Minority Artisan Credit",
            "target_beneficiaries": "Minority artisans, craftspersons, weavers",
            "stated_benefits": "Concessional credit up to ₹10 Lakh for male craftspersons and ₹10 Lakh for female craftspersons at 5% interest rate p.a.",
            "official_source_url": "https://www.nmdfc.org/schemes/virasat",
            "source_type": "HTML",
            "discovery_source": "IMPLEMENTING_AGENCY",
        },
        {
            "name": "Divyangjan Swavalamban Yojana (NDFDC Concessional Loan)",
            "code": "NDFDC-SWAVALAMBAN",
            "ministry": "Ministry of Social Justice and Empowerment",
            "implementing_agency": "National Divyangjan Finance and Development Corporation (NDFDC)",
            "level": "CENTRAL_SECTOR",
            "state_coverage": "All India",
            "category": "PwD Self-Employment",
            "target_beneficiaries": "Persons with Disabilities (PwD) with >= 40% disability",
            "stated_benefits": "Concessional loans up to ₹50 Lakh at low interest rates (5% to 8% p.a.) for self-employment, small business, and commercial transport.",
            "official_source_url": "https://ndfdc.nic.in/divyangjan-swavalamban-yojana",
            "source_type": "HTML",
            "discovery_source": "IMPLEMENTING_AGENCY",
        },
        {
            "name": "SAMARTH — Scheme for Capacity Building in Textile Sector",
            "code": "SAMARTH-TEXTILE",
            "ministry": "Ministry of Textiles",
            "implementing_agency": "Ministry of Textiles / Implementing Partners",
            "level": "CENTRAL_SECTOR",
            "state_coverage": "All India",
            "category": "Textile Skilling & Employment",
            "target_beneficiaries": "Traditional handloom weavers, garment workers, youth",
            "stated_benefits": "Demand-driven, placement-oriented National Skills Qualifications Framework (NSQF) compliant skilling programme with wage employment linkage.",
            "official_source_url": "https://samarth-textiles.gov.in/",
            "source_type": "HTML",
            "discovery_source": "CENTRAL_MINISTRY",
        },
        {
            "name": "Animal Husbandry Infrastructure Development Fund (AHIDF)",
            "code": "AHIDF",
            "ministry": "Ministry of Fisheries, Animal Husbandry and Dairying",
            "implementing_agency": "Department of Animal Husbandry and Dairying / SIDBI",
            "level": "CENTRAL_SECTOR",
            "state_coverage": "All India",
            "category": "Livestock / Dairy Infrastructure",
            "target_beneficiaries": "Farmer Producer Organizations (FPOs), MSMEs, Section 8 companies, private entrepreneurs",
            "stated_benefits": "3% interest subvention on term loans up to 90% project cost from scheduled banks with credit guarantee cover up to 25% of borrowing.",
            "official_source_url": "https://ahidf.udyamimitra.in/",
            "source_type": "HTML",
            "discovery_source": "CENTRAL_MINISTRY",
        },
        {
            "name": "Special Credit Linked Capital Subsidy Scheme for SC/ST (SCLCSS under NSSH)",
            "code": "SCLCSS-NSSH",
            "ministry": "Ministry of Micro, Small and Medium Enterprises",
            "implementing_agency": "National Small Industries Corporation (NSIC) / SIDBI",
            "level": "CENTRAL_SECTOR",
            "state_coverage": "All India",
            "category": "SC/ST Enterprise Technology Upgradation",
            "target_beneficiaries": "SC/ST MSE entrepreneurs with valid UDYAM",
            "stated_benefits": "25% upfront capital subsidy on institutional finance up to ₹1 Crore for technology upgradation and modern machinery purchase.",
            "official_source_url": "https://www.scsthub.in/sclcss",
            "source_type": "HTML",
            "discovery_source": "IMPLEMENTING_AGENCY",
        },
        {
            "name": "NSKFDC Sanitary Marts Scheme",
            "code": "NSKFDC-SANITARY-MARTS",
            "ministry": "Ministry of Social Justice and Empowerment",
            "implementing_agency": "National Safai Karamcharis Finance and Development Corporation (NSKFDC)",
            "level": "CENTRAL_SECTOR",
            "state_coverage": "All India",
            "category": "Sanitation Worker Livelihood Rehabilitation",
            "target_beneficiaries": "Safai Karamcharis, manual scavengers, and their dependents",
            "stated_benefits": "Concessional project loan up to ₹15 Lakh for setting up sanitary retail marts, equipment rental services, and desludging units at 4% interest rate.",
            "official_source_url": "https://www.nskfdc.nic.in/en/sanitary-marts-scheme",
            "source_type": "HTML",
            "discovery_source": "IMPLEMENTING_AGENCY",
        },
        {
            "name": "NBCFDC Krishi Sampada Scheme",
            "code": "NBCFDC-KRISHI-SAMPADA",
            "ministry": "Ministry of Social Justice and Empowerment",
            "implementing_agency": "National Backward Classes Finance and Development Corporation (NBCFDC)",
            "level": "CENTRAL_SECTOR",
            "state_coverage": "All India",
            "category": "OBC Small Farmer Seasonal Credit",
            "target_beneficiaries": "OBC small and marginal farmers, vegetable and fruit growers",
            "stated_benefits": "Concessional seasonal loan up to ₹50,000 per beneficiary at 4% interest rate per annum to eliminate dependency on local moneylenders.",
            "official_source_url": "https://nbcfdc.nic.in/krishi-sampada-scheme",
            "source_type": "HTML",
            "discovery_source": "IMPLEMENTING_AGENCY",
        },
        {
            "name": "Pradhan Mantri Janjati Adivasi Nyaya Maha Abhiyan (PM-JANMAN)",
            "code": "PM-JANMAN",
            "ministry": "Ministry of Tribal Affairs",
            "implementing_agency": "Ministry of Tribal Affairs / State Tribal Welfare Departments",
            "level": "CENTRAL_SECTOR",
            "state_coverage": "All India",
            "category": "PVTG Tribal Livelihood & Saturation Mission",
            "target_beneficiaries": "Particularly Vulnerable Tribal Groups (PVTGs) across 18 States and UT of A&N Islands",
            "stated_benefits": "Comprehensive housing, clean water, electricity, road connectivity, mobile medical units, and livelihood multi-purpose centers for 75 PVTG communities.",
            "official_source_url": "https://tribal.nic.in/pm-janman.aspx",
            "source_type": "HTML",
            "discovery_source": "CENTRAL_MINISTRY",
        },

        # --- PRIORITY 7: State Government MSME & Welfare Schemes ---
        {
            "name": "Mukhyamantri Yuva Swavalamban Yojana (MYSY Gujarat)",
            "code": "MYSY-GUJARAT",
            "ministry": "Department of Higher and Technical Education, Government of Gujarat",
            "implementing_agency": "Knowledge Consortium of Gujarat",
            "level": "STATE",
            "state_coverage": "Gujarat",
            "category": "State Youth Self-Reliance & Higher Education",
            "target_beneficiaries": "Meritorious youth of Gujarat with annual family income up to ₹6 Lakh",
            "stated_benefits": "50% tuition fee subsidy up to ₹2,00,000 for medical and ₹50,000 for engineering and professional degrees plus monthly boarding stipend.",
            "official_source_url": "https://mysy.guj.nic.in/",
            "source_type": "HTML",
            "discovery_source": "STATE_PORTAL",
        },
        {
            "name": "Chief Minister's Employment Generation Programme (CMEGP Maharashtra)",
            "code": "CMEGP-MAHARASHTRA",
            "ministry": "Industries Department, Government of Maharashtra",
            "implementing_agency": "Directorate of Industries, Maharashtra / KVIB",
            "level": "STATE",
            "state_coverage": "Maharashtra",
            "category": "State Micro-Enterprise Credit Subsidy",
            "target_beneficiaries": "Youth and entrepreneurs aged 18 to 45 residing in Maharashtra",
            "stated_benefits": "Capital subsidy of 15% to 35% on project loans up to ₹50 Lakh for manufacturing and ₹10 Lakh for service enterprises.",
            "official_source_url": "https://maha-cmegp.gov.in/",
            "source_type": "HTML",
            "discovery_source": "STATE_PORTAL",
        },
        {
            "name": "Unemployed Youth Employment Generation Programme (UYEGP Tamil Nadu)",
            "code": "UYEGP-TAMILNADU",
            "ministry": "Micro, Small and Medium Enterprises Department, Government of Tamil Nadu",
            "implementing_agency": "District Industries Centres (DICs), Tamil Nadu",
            "level": "STATE",
            "state_coverage": "Tamil Nadu",
            "category": "State MSME Self-Employment",
            "target_beneficiaries": "Unemployed youth aged 18 to 35 (up to 45 for special categories) in Tamil Nadu",
            "stated_benefits": "25% government subsidy up to ₹1,25,000 on bank loans for manufacturing (up to ₹15 Lakh) and service/business (up to ₹5 Lakh).",
            "official_source_url": "https://www.msmeonline.tn.gov.in/uyegp/",
            "source_type": "HTML",
            "discovery_source": "STATE_PORTAL",
        },
        {
            "name": "Mukhyamantri Yuva Swarozgar Yojana (MMYSY Uttar Pradesh)",
            "code": "MMYSY-UP",
            "ministry": "Department of Micro, Small and Medium Enterprises, Government of Uttar Pradesh",
            "implementing_agency": "Directorate of Industries, Uttar Pradesh",
            "level": "STATE",
            "state_coverage": "Uttar Pradesh",
            "category": "State Youth Self-Employment Loan",
            "target_beneficiaries": "Educated unemployed youth of Uttar Pradesh aged 18 to 40",
            "stated_benefits": "25% margin money subsidy on project cost up to ₹25 Lakh for industrial units and ₹5 Lakh for service sector with bank tie-ups.",
            "official_source_url": "https://msme.up.gov.in/en/page/mukhyamantri-yuva-swarozgar-yojana",
            "source_type": "HTML",
            "discovery_source": "STATE_PORTAL",
        },
        {
            "name": "Mukhyamantri Udyami Yojana (Bihar)",
            "code": "MMUY-BIHAR",
            "ministry": "Department of Industries, Government of Bihar",
            "implementing_agency": "Directorate of Industries, Bihar",
            "level": "STATE",
            "state_coverage": "Bihar",
            "category": "State Entrepreneurship Financing",
            "target_beneficiaries": "SC, ST, EBC, Women, and Young entrepreneurs resident in Bihar",
            "stated_benefits": "Financial assistance up to ₹10 Lakh (50% grant up to ₹5 Lakh + 50% interest-free/1% loan) for setting up micro-industrial units.",
            "official_source_url": "https://udyami.bihar.gov.in/",
            "source_type": "HTML",
            "discovery_source": "STATE_PORTAL",
        }
    ]


class SchemeDiscoveryWorker:
    """
    Automated Batch Discovery and Staging Worker.
    Executes discovery runs across central ministries, state portals, and implementing agencies.
    Applies relevance classification, authoritative source resolution, layered deduplication,
    extraction, normalization, and stages candidate schemes for human-in-the-loop review.
    """

    def __init__(self, db: Session):
        self.db = db

    def run_discovery_batch(
        self,
        target_source: Optional[str] = None,
        max_candidates: int = 50,
        mock_fetch: bool = False
    ) -> Dict[str, Any]:
        run_id = f"RUN-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}"
        now = datetime.utcnow()

        logger.info(f"Starting discovery batch run '{run_id}' (target: {target_source or 'ALL'})")

        catalog = SchemeDiscoveryCatalog.OFFICIAL_DISCOVERY_CATALOG
        if target_source and target_source.upper() != "ALL":
            catalog = [e for e in catalog if e.get("discovery_source") == target_source.upper()]

        catalog = catalog[:max_candidates]

        stats = {
            "run_id": run_id,
            "total_discovered": len(catalog),
            "relevant_count": 0,
            "low_priority_or_irrelevant": 0,
            "officially_verified": 0,
            "duplicate_candidates": 0,
            "staged_for_review": 0,
            "failed_count": 0,
            "candidates_created": []
        }

        # Load canonical schemes for deduplication checking
        canonical_schemes = self.db.query(Scheme).all()

        if (target_source in ["LIVE", "MYSCHEME"] or (target_source in [None, "ALL"] and max_candidates > len(SchemeDiscoveryCatalog.OFFICIAL_DISCOVERY_CATALOG))) and not mock_fetch:
            return self.run_live_discovery(target_staged=max_candidates)

        for entry in catalog:
            try:
                name = entry["name"]
                code = entry.get("code", "UNKNOWN")
                source_url = entry["official_source_url"]
                ministry = entry.get("ministry")
                desc = entry.get("stated_benefits", "")
                cat = entry.get("category", "")

                # 1. Relevance Classification (7 Priorities)
                rel_res = SchemeRelevanceClassifier.classify(name, desc, cat)
                if rel_res.status in ["IRRELEVANT"]:
                    stats["low_priority_or_irrelevant"] += 1
                    continue
                elif rel_res.status in ["HIGH_PRIORITY", "RELEVANT"]:
                    stats["relevant_count"] += 1
                else:
                    stats["low_priority_or_irrelevant"] += 1

                # 2. Authoritative Source Resolution
                auth_res = OfficialSourceResolver.resolve(source_url)
                if not auth_res.is_authoritative:
                    verif_status = "UNVERIFIED"
                elif auth_res.authority_level in ["LEVEL_1_PRIMARY", "LEVEL_2_AGENCY"]:
                    verif_status = "OFFICIALLY_VERIFIED"
                    stats["officially_verified"] += 1
                else:
                    verif_status = "NEEDS_REVIEW"

                # 3. 7-Stage Layered Deduplication
                dedup_res = SchemeDeduplicator.check_duplicate(
                    candidate_name=name,
                    candidate_code=code,
                    candidate_source_url=source_url,
                    candidate_ministry=ministry,
                    existing_schemes=canonical_schemes
                )

                dup_status = dedup_res.action_recommended
                dup_of = dedup_res.matched_scheme_id
                if dedup_res.is_duplicate:
                    stats["duplicate_candidates"] += 1

                # 4. Extraction & Normalization
                extracted_data: Dict[str, Any] = {
                    "scheme_name": name,
                    "scheme_code": code,
                    "ministry": ministry,
                    "implementing_agency": entry.get("implementing_agency"),
                    "level": entry.get("level", "CENTRAL_SECTOR"),
                    "state_coverage": entry.get("state_coverage", "All India"),
                    "category": cat,
                    "target_beneficiaries": entry.get("target_beneficiaries"),
                    "stated_benefits": desc,
                    "official_source_url": source_url,
                    "source_type": entry.get("source_type", "HTML")
                }

                evidence: Dict[str, Any] = {
                    "scheme_name": {"text": name, "source_page": "Official Directory", "source_section": "Portal Title"},
                    "authority": {"text": ministry or "Government Authority", "source_page": "Directory", "source_section": "Ministry Registry"},
                    "stated_benefits": {"text": desc, "source_page": "Directory", "source_section": "Benefit Description"},
                }

                # Extract financial limits if present in stated benefits text
                html_extractor = OfficialGovHTMLExtractor()
                text_extracted = html_extractor.extract(f"<h1>{name}</h1><p>{desc}</p>", source_url)
                for k, v in text_extracted.items():
                    if k not in ["source_url", "evidence"]:
                        extracted_data[k] = v
                if "evidence" in text_extracted:
                    for ek, ev in text_extracted["evidence"].items():
                        evidence[ek] = {"text": ev, "source_page": "Overview Text", "source_section": "Extracted Benefit Text"}

                # Normalization
                norm_data = SchemeDataNormalizer.normalize(extracted_data)

                # Validation
                val_res = SchemeDataValidator.validate(norm_data)

                # 5. Check if Candidate Already Staged
                existing_cand = self.db.query(CandidateScheme).filter(
                    (CandidateScheme.normalized_name == name) |
                    (CandidateScheme.official_source_url == source_url)
                ).first()

                if existing_cand:
                    existing_cand.run_id = run_id
                    existing_cand.updated_at = now
                    stats["duplicate_candidates"] += 1
                    continue

                # 6. Stage New CandidateScheme
                cand_id = f"CAND-{uuid.uuid4().hex[:10]}"
                candidate = CandidateScheme(
                    candidate_id=cand_id,
                    run_id=run_id,
                    discovered_name=name,
                    normalized_name=name,
                    scheme_code=code,
                    discovery_source=entry.get("discovery_source", "CENTRAL_MINISTRY"),
                    discovery_url=source_url,
                    official_source_url=source_url,
                    source_document=entry.get("source_document") or f"{name} Guidelines",
                    source_type=entry.get("source_type", "HTML"),
                    ministry=ministry,
                    implementing_agency=entry.get("implementing_agency"),
                    level=entry.get("level", "CENTRAL_SECTOR"),
                    state_coverage=entry.get("state_coverage", "All India"),
                    district_coverage="All Districts",
                    sector=norm_data.get("sector", "GENERAL_BUSINESS"),
                    scheme_category=cat,
                    target_beneficiaries=entry.get("target_beneficiaries"),
                    stated_benefits=desc,
                    relevance_status=rel_res.status,
                    relevance_reason=rel_res.reason,
                    extraction_status="EXTRACTED",
                    verification_status=verif_status,
                    duplicate_status=dup_status,
                    duplicate_of_scheme_id=dup_of,
                    data_confidence="HIGH" if verif_status == "OFFICIALLY_VERIFIED" else "MEDIUM",
                    extracted_data=json.dumps(norm_data, default=str),
                    missing_fields=json.dumps(["repayment_period_max_months", "moratorium_max_months"]),
                    evidence=json.dumps(evidence, default=str),
                    validation_status=val_res.status,
                    validation_errors=json.dumps(val_res.errors + val_res.warnings, default=str),
                    candidate_status="STAGED",
                    created_at=now,
                    updated_at=now
                )
                self.db.add(candidate)
                stats["staged_for_review"] += 1
                stats["candidates_created"].append(cand_id)

            except Exception as e:
                logger.error(f"Failed to process candidate entry '{entry.get('name')}': {e}")
                stats["failed_count"] += 1

        self.db.commit()
        logger.info(f"Discovery batch '{run_id}' complete: staged {stats['staged_for_review']} candidate schemes.")
        return stats

    def run_live_discovery(
        self,
        target_staged: int = 265,
        categories: Optional[List[str]] = None,
        max_workers: int = 4
    ) -> Dict[str, Any]:
        """
        Discovers, extracts, resolves, deduplicates, and stages real government schemes
        from live public directories across central ministries and states.
        """
        run_id = f"RUN-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}"
        now = datetime.utcnow()
        logger.info(f"=== Starting live public scheme discovery run '{run_id}' (target: {target_staged}) ===")

        stats: Dict[str, Any] = {
            "run_id": run_id,
            "total_discovered": 0,
            "relevant_count": 0,
            "officially_verified": 0,
            "unverified_count": 0,
            "needs_review_count": 0,
            "duplicate_candidates": 0,
            "duplicate_canonical_matched": 0,
            "rejected_count": 0,
            "staged_for_review": 0,
            "failed_count": 0,
            "pdf_processed_count": 0,
            "by_level": {"Central": 0, "State": 0, "UT": 0},
            "by_state": {},
            "by_ministry": {},
            "by_category": {},
            "candidates_created": []
        }

        canonical_schemes = self.db.query(Scheme).all()
        existing_candidates = self.db.query(CandidateScheme).all()
        seen_slugs = set()
        seen_names = set(c.normalized_name for c in existing_candidates)
        stats["staged_for_review"] = len(existing_candidates)

        api_key = get_myscheme_api_key()
        if not api_key:
            raise ValueError(
                "CRITICAL CONFIGURATION ERROR: MYSCHEME_API_KEY is not configured. "
                "Please provide a valid MYSCHEME_API_KEY in application settings or environment variables."
            )

        client = httpx.Client(timeout=15.0, verify=False)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "x-api-key": api_key,
        }

        active_cats = categories or PRIORITY_CATEGORIES
        cat_idx = 0

        while stats["staged_for_review"] < target_staged:
            current_cat = active_cats[cat_idx % len(active_cats)]
            cat_page = (cat_idx // len(active_cats))
            q_filter = [{"identifier": "schemeCategory", "value": current_cat}]
            q_enc = urllib.parse.quote(json.dumps(q_filter))
            search_url = f"{MYSCHEME_SEARCH_URL}?lang=en&page={cat_page}&size=50&q={q_enc}"

            try:
                r = client.get(search_url, headers=headers)
                if r.status_code != 200:
                    time.sleep(1.5)
                    cat_idx += 1
                    continue
                data = r.json()
                items = data.get("data", {}).get("hits", {}).get("items", [])
                if not items:
                    cat_idx += 1
                    if cat_idx >= len(active_cats) * 15:
                        break
                    continue
            except Exception as e:
                logger.error(f"Directory search error: {e}")
                time.sleep(1.0)
                cat_idx += 1
                continue

            batch_slugs = []
            batch_items = {}
            for item in items:
                f = item.get("fields", {})
                slug = f.get("slug")
                if slug and slug not in seen_slugs:
                    seen_slugs.add(slug)
                    batch_slugs.append(slug)
                    batch_items[slug] = f

            stats["total_discovered"] += len(batch_slugs)

            def _fetch_one(s: str):
                url = f"{MYSCHEME_DETAILS_URL}?slug={s}&lang=en"
                for att in range(3):
                    try:
                        res = client.get(url, headers=headers, timeout=12.0)
                        if res.status_code == 200:
                            return s, res.json().get("data", {}).get("en", {})
                        elif res.status_code == 429:
                            time.sleep(1.0 * (att + 1))
                    except Exception:
                        time.sleep(0.4)
                return s, None

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                details_results = list(executor.map(_fetch_one, batch_slugs))

            for slug, d in details_results:
                if stats["staged_for_review"] >= target_staged:
                    break
                if not d:
                    stats["failed_count"] += 1
                    continue

                try:
                    basic = d.get("basicDetails", {})
                    content = d.get("schemeContent", {})
                    eligibility = d.get("eligibilityCriteria", {})
                    app_proc = d.get("applicationProcess", [])

                    name = stringify_field(basic.get("schemeName") or batch_items.get(slug, {}).get("schemeName"))
                    if not name or name in seen_names:
                        if name in seen_names:
                            stats["duplicate_candidates"] += 1
                        continue

                    code = stringify_field(basic.get("schemeShortTitle") or batch_items.get(slug, {}).get("schemeShortTitle") or slug.upper())
                    raw_min = basic.get("nodalMinistryName") or basic.get("nodalDepartmentName") or batch_items.get(slug, {}).get("nodalMinistryName")
                    ministry = stringify_field(raw_min) or "Government Department / Statutory Authority"
                    implementing_agency = stringify_field(basic.get("implementingAgency"))

                    raw_lvl = basic.get("level") or batch_items.get(slug, {}).get("level")
                    raw_lvl_str = stringify_field(raw_lvl)
                    if "cent" in raw_lvl_str.lower():
                        lvl = "CENTRAL_SECTOR"
                        lvl_label = "Central"
                    elif "ut" in raw_lvl_str.lower():
                        lvl = "UT"
                        lvl_label = "UT"
                    else:
                        lvl = "STATE"
                        lvl_label = "State"

                    raw_states = basic.get("beneficiaryState") or batch_items.get(slug, {}).get("beneficiaryState", [])
                    state_cov = stringify_field(raw_states)
                    if not state_cov or "All" in state_cov:
                        state_cov = "All India"

                    raw_cats = basic.get("schemeCategory") or batch_items.get(slug, {}).get("schemeCategory", [])
                    cat_str = stringify_field(raw_cats) or current_cat

                    target_b = basic.get("targetBeneficiaries") or basic.get("schemeFor")
                    target_b_str = stringify_field(target_b) or "Eligible Citizens / Enterprises"

                    brief_desc = stringify_field(content.get("briefDescription") or batch_items.get(slug, {}).get("briefDescription", ""))
                    detailed_desc = stringify_field(content.get("detailedDescription_md") or brief_desc)
                    benefits = stringify_field(content.get("benefits_md") or content.get("benefits") or "")
                    elig_desc = stringify_field(eligibility.get("eligibilityDescription_md") or "")

                    stated_benefits = (detailed_desc + "\n\n" + benefits).strip() or brief_desc or name

                    refs = content.get("references", [])
                    app_url = None
                    if app_proc and isinstance(app_proc, list):
                        for ap in app_proc:
                            if isinstance(ap, dict) and ap.get("url"):
                                app_url = stringify_field(ap.get("url"))
                                break

                    discovery_url = f"https://www.myscheme.gov.in/schemes/{slug}"
                    official_source_url = None
                    source_doc_title = None
                    source_type = "HTML"

                    if refs and isinstance(refs, list):
                        for ref in refs:
                            if isinstance(ref, dict):
                                ref_url = str(ref.get("url") or "").strip()
                                ref_title = str(ref.get("title") or f"{name} Guidelines").strip()
                                if ref_url and (ref_url.startswith("http://") or ref_url.startswith("https://")):
                                    if any(dom in ref_url.lower() for dom in [".gov.in", ".nic.in", "sidbi.in", "nabard.org", "standupmitra.in", "cgtmse.in", "mudra.org.in"]):
                                        official_source_url = ref_url
                                        source_doc_title = ref_title
                                        if ".pdf" in ref_url.lower():
                                            source_type = "PDF"
                                        break

                    if not official_source_url and app_url:
                        clean_app = app_url.strip()
                        if not clean_app.startswith("http"):
                            clean_app = "https://" + clean_app
                        if any(dom in clean_app.lower() for dom in [".gov.in", ".nic.in", "sidbi.in", "nabard.org", "standupmitra.in", "cgtmse.in"]):
                            official_source_url = clean_app
                            source_doc_title = f"{name} Official Application Portal"
                            source_type = "HTML"

                    if not official_source_url and refs and isinstance(refs, list):
                        for ref in refs:
                            if isinstance(ref, dict):
                                ref_url = str(ref.get("url") or "").strip()
                                if ".pdf" in ref_url.lower() and ref_url.startswith("http"):
                                    official_source_url = ref_url
                                    source_doc_title = str(ref.get("title") or f"{name} Guidelines PDF")
                                    source_type = "PDF"
                                    break

                    if not official_source_url:
                        official_source_url = discovery_url
                        source_doc_title = f"{name} Official Government Scheme Profile"
                        source_type = "HTML"

                    if source_type == "PDF":
                        stats["pdf_processed_count"] += 1

                    # 1. Relevance
                    rel_res = SchemeRelevanceClassifier.classify(name, f"{brief_desc} {stated_benefits} {elig_desc}", cat_str)
                    if rel_res.status == "IRRELEVANT":
                        stats["rejected_count"] += 1
                        continue
                    elif rel_res.status in ["HIGH_PRIORITY", "RELEVANT"]:
                        stats["relevant_count"] += 1
                    else:
                        stats["needs_review_count"] += 1

                    # 2. Source Resolution
                    auth_res = OfficialSourceResolver.resolve(official_source_url)
                    if auth_res.authority_level in ["LEVEL_1_PRIMARY", "LEVEL_2_AGENCY"]:
                        verif_status = "OFFICIALLY_VERIFIED"
                        stats["officially_verified"] += 1
                        confidence = "HIGH"
                    elif auth_res.authority_level == "LEVEL_3_DISCOVERY":
                        verif_status = "NEEDS_REVIEW"
                        stats["needs_review_count"] += 1
                        confidence = "MEDIUM"
                    else:
                        verif_status = "UNVERIFIED"
                        stats["unverified_count"] += 1
                        confidence = "LOW"

                    # 3. Deduplication
                    dedup_res = SchemeDeduplicator.check_duplicate(
                        candidate_name=name,
                        candidate_code=code,
                        candidate_source_url=official_source_url,
                        candidate_app_url=app_url,
                        candidate_ministry=ministry,
                        existing_schemes=canonical_schemes
                    )
                    dup_status = dedup_res.action_recommended
                    dup_of = dedup_res.matched_scheme_id
                    if dedup_res.is_duplicate:
                        stats["duplicate_canonical_matched"] += 1

                    # 4. Normalization & Validation
                    extracted_data = {
                        "scheme_name": name,
                        "scheme_code": code,
                        "ministry": ministry,
                        "implementing_agency": implementing_agency,
                        "level": lvl,
                        "state_coverage": state_cov,
                        "category": cat_str,
                        "target_beneficiaries": target_b_str,
                        "stated_benefits": stated_benefits[:2000],
                        "official_source_url": official_source_url,
                        "source_type": source_type
                    }
                    norm_data = SchemeDataNormalizer.normalize(extracted_data)
                    val_res = SchemeDataValidator.validate(norm_data)

                    evidence = {
                        "scheme_name": {"text": name, "source_page": "myScheme Directory", "source_section": "Scheme Header"},
                        "authority": {"text": ministry, "source_page": "Official Record", "source_section": "Nodal Ministry"},
                        "stated_benefits": {"text": brief_desc or stated_benefits[:300], "source_page": "Overview", "source_section": "Benefit Summary"},
                        "official_source": {"text": official_source_url, "source_page": "References", "source_section": "Primary Source"},
                    }

                    cand_id = f"CAND-{uuid.uuid4().hex[:10]}"
                    candidate = CandidateScheme(
                        candidate_id=cand_id,
                        run_id=run_id,
                        discovered_name=name[:255],
                        normalized_name=name[:255],
                        scheme_code=code[:50],
                        discovery_source="MYSCHEME_DISCOVERY",
                        discovery_url=discovery_url,
                        official_source_url=official_source_url,
                        source_document=source_doc_title[:255] if source_doc_title else f"{name} Guidelines",
                        source_type=source_type,
                        ministry=ministry[:255] if ministry else None,
                        implementing_agency=implementing_agency[:255] if implementing_agency else None,
                        level=lvl[:50],
                        state_coverage=state_cov,
                        district_coverage="All Districts",
                        sector=norm_data.get("sector", "GENERAL_BUSINESS"),
                        scheme_category=cat_str[:100] if cat_str else None,
                        target_beneficiaries=target_b_str,
                        stated_benefits=stated_benefits[:2000],
                        relevance_status=rel_res.status,
                        relevance_reason=rel_res.reason,
                        extraction_status="EXTRACTED",
                        verification_status=verif_status,
                        duplicate_status=dup_status,
                        duplicate_of_scheme_id=dup_of,
                        data_confidence=confidence,
                        extracted_data=json.dumps(norm_data, default=str),
                        missing_fields=json.dumps(["repayment_period_max_months", "moratorium_max_months"]),
                        evidence=json.dumps(evidence, default=str),
                        validation_status=val_res.status,
                        validation_errors=json.dumps(val_res.errors + val_res.warnings, default=str),
                        candidate_status="STAGED",
                        created_at=now,
                        updated_at=now
                    )
                    self.db.add(candidate)
                    seen_names.add(name)
                    stats["staged_for_review"] += 1
                    stats["candidates_created"].append(cand_id)

                    stats["by_level"][lvl_label] = stats["by_level"].get(lvl_label, 0) + 1
                    st_key = state_cov if state_cov != "All India" else "Central / All India"
                    stats["by_state"][st_key] = stats["by_state"].get(st_key, 0) + 1
                    if ministry:
                        stats["by_ministry"][ministry] = stats["by_ministry"].get(ministry, 0) + 1
                    if cat_str:
                        for c_part in [c.strip() for c in cat_str.split(",")]:
                            if c_part:
                                stats["by_category"][c_part] = stats["by_category"].get(c_part, 0) + 1

                except Exception as e:
                    logger.error(f"Error processing scheme candidate '{slug}': {e}")
                    stats["failed_count"] += 1

            self.db.commit()
            cat_idx += 1
            time.sleep(0.3)

        client.close()
        logger.info(f"=== Live discovery run '{run_id}' finished: staged {stats['staged_for_review']} candidate schemes ===")
        return stats

