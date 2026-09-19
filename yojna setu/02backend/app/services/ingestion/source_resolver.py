from urllib.parse import urlparse
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class SourceAuthorityResolution:
    is_authoritative: bool
    authority_level: str  # LEVEL_1_PRIMARY, LEVEL_2_AGENCY, LEVEL_3_DISCOVERY, UNVERIFIED_THIRD_PARTY
    domain: str
    official_organization: Optional[str]
    notes: str


class OfficialSourceResolver:
    """
    Validates and classifies source URLs according to YojnaSetu's strict Source Hierarchy:
    LEVEL 1 — PRIMARY AUTHORITY (*.gov.in, *.nic.in, official ministry and state portals)
    LEVEL 2 — IMPLEMENTING AGENCIES (KVIC, SIDBI, NABARD, NSFDC, etc.)
    LEVEL 3 — DISCOVERY SOURCES (myScheme, India.gov.in)
    UNVERIFIED — Commercial aggregators, SEO blogs, private loan sites (REJECTED for legal truth)
    """

    KNOWN_IMPLEMENTING_AGENCIES = {
        "sidbi.in": "Small Industries Development Bank of India (SIDBI)",
        "nabard.org": "National Bank for Agriculture and Rural Development (NABARD)",
        "scsthub.in": "National SC-ST Hub (NSIC / Ministry of MSME)",
        "udyamimitra.in": "Udyamimitra (SIDBI / MSME)",
        "standupmitra.in": "Stand-Up Mitra (SIDBI / DFS)",
        "cgtmse.in": "Credit Guarantee Fund Trust for Micro and Small Enterprises",
        "mudra.org.in": "Micro Units Development & Refinance Agency (MUDRA)",
        "nmdfc.org": "National Minorities Development and Finance Corporation (NMDFC)",
    }

    DISALLOWED_THIRD_PARTY_DOMAINS = {
        "bankbazaar.com", "paisabazaar.com", "cleartax.in", "indiafilings.com",
        "policybazaar.com", "bajajfinserv.in", "tata-capital.com", "wikipedia.org",
        "quora.com", "blogspot.com", "wordpress.com", "medium.com"
    }

    @classmethod
    def resolve(cls, url: str) -> SourceAuthorityResolution:
        if not url or not (url.startswith("http://") or url.startswith("https://")):
            return SourceAuthorityResolution(
                is_authoritative=False,
                authority_level="UNVERIFIED_THIRD_PARTY",
                domain="invalid",
                official_organization=None,
                notes="URL does not use a valid HTTP/HTTPS protocol."
            )

        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if ":" in domain:
                domain = domain.split(":")[0]

            # 1. Check Explicit Disallowed Commercial Aggregators
            for dis in cls.DISALLOWED_THIRD_PARTY_DOMAINS:
                if domain == dis or domain.endswith("." + dis):
                    return SourceAuthorityResolution(
                        is_authoritative=False,
                        authority_level="UNVERIFIED_THIRD_PARTY",
                        domain=domain,
                        official_organization=None,
                        notes=f"Domain '{domain}' is an unverified commercial/third-party aggregator. Prohibited as a statutory authority."
                    )

            # 2. Check Level 3 Discovery Sources
            if "myscheme.gov.in" in domain or "india.gov.in" in domain:
                return SourceAuthorityResolution(
                    is_authoritative=True,
                    authority_level="LEVEL_3_DISCOVERY",
                    domain=domain,
                    official_organization="National Government Scheme Discovery Directory",
                    notes="Approved for scheme discovery and metadata, but statutory parameters require Level 1/2 verification."
                )

            # 3. Check Level 1 Primary Authority (*.gov.in, *.nic.in)
            if domain.endswith(".gov.in") or domain.endswith(".nic.in"):
                return SourceAuthorityResolution(
                    is_authoritative=True,
                    authority_level="LEVEL_1_PRIMARY",
                    domain=domain,
                    official_organization="Official Government of India / State Government Domain",
                    notes=f"Authoritative Level 1 government domain ({domain})."
                )

            # 4. Check Level 2 Implementing Agencies
            for agency_domain, agency_name in cls.KNOWN_IMPLEMENTING_AGENCIES.items():
                if domain == agency_domain or domain.endswith("." + agency_domain):
                    return SourceAuthorityResolution(
                        is_authoritative=True,
                        authority_level="LEVEL_2_AGENCY",
                        domain=domain,
                        official_organization=agency_name,
                        notes=f"Recognized Level 2 implementing agency statutory authority: {agency_name}."
                    )

            # 5. Unrecognized domain
            return SourceAuthorityResolution(
                is_authoritative=False,
                authority_level="UNVERIFIED_THIRD_PARTY",
                domain=domain,
                official_organization=None,
                notes=f"Domain '{domain}' is not on the recognized government/statutory agency allowlist."
            )

        except Exception as e:
            return SourceAuthorityResolution(
                is_authoritative=False,
                authority_level="UNVERIFIED_THIRD_PARTY",
                domain="error",
                official_organization=None,
                notes=f"Failed to parse source domain: {str(e)}"
            )
