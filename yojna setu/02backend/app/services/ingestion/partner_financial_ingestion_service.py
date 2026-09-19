"""
Partner Financial Intelligence Ingestion Service for YojnaSetu (SIH26092).

Implements the statutory data ingestion pipeline:
OFFICIAL GOVERNMENT SOURCE
  ↓
SAFE FETCH (SSRF protected, Domain Allowlist, Size/Timeout limits)
  ↓
RAW SNAPSHOT & SHA-256 HASH
  ↓
CHANGE DETECTION (Compare snapshot hash against previous baseline)
  ↓
PARSE & NORMALIZE
  ↓
ENTITY RESOLUTION (5-Tier matching: canonical name, alias, brand, state)
  ↓
MULTI-DIMENSIONAL OBSERVATION STORAGE (Strict provenance, no pseudo-aggregate scores)
  ↓
STALENESS & PRUDENTIAL VALIDATION
  ↓
CACHE INVALIDATION & ROUTING UPDATE

Failure Invariant:
If an external government source fails to fetch or return valid data:
- DO NOT wipe or delete existing verified observations.
- DO NOT automatically convert verified data to UNKNOWN.
- Retain last_verified_value and last_verified_as_of.
- Mark ingestion status as FETCH_FAILED.
"""

import hashlib
import ipaddress
import logging
import re
import urllib.parse
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc

from app.models.financial_intelligence import (
    InstitutionEntity,
    InstitutionAlias,
    PartnerFinancialObservation,
    PrudentialRule
)
from app.models.partner import Partner
from app.engine.entity_resolution import EntityResolutionEngine
from app.engine.prudential_rule_engine import PrudentialRuleEngine

logger = logging.getLogger("yojnasetu.services.ingestion.partner_financial")

# Statutory official domains permitted for government partner financial data ingestion
OFFICIAL_GOV_DOMAIN_ALLOWLIST = {
    "nsfdc.nic.in",
    "socialjustice.gov.in",
    "rbi.org.in",
    "dbie.rbi.org.in",
    "nabard.org",
    "financialservices.gov.in",
    "sidbi.in",
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SecurityValidationError(ValueError):
    """Raised when URL violates SSRF or domain allowlist policies."""
    pass


class PartnerFinancialIngestionService:
    """
    Production-grade, evidence-grounded ingestion pipeline for channel partner financial health.
    """

    @classmethod
    def validate_source_url(cls, url: str) -> str:
        """
        Validates the URL against strict SSRF protection and the official government domain allowlist.
        """
        if not url:
            raise SecurityValidationError("Source URL cannot be empty")

        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise SecurityValidationError(f"Invalid URL scheme '{parsed.scheme}'; only HTTP/HTTPS allowed")

        hostname = (parsed.hostname or "").lower().strip()
        if not hostname:
            raise SecurityValidationError("Invalid hostname in source URL")

        # SSRF checks: reject localhost, private IP spaces, link-local, loopbacks
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                raise SecurityValidationError(f"Access to private/internal IP address {hostname} is blocked (SSRF protection)")
        except ValueError:
            # Hostname is a domain name, not an IP address
            pass

        if hostname in ("localhost", "127.0.0.1", "0.0.0.0", "::1"):
            raise SecurityValidationError("Access to localhost is strictly prohibited")

        # Check domain allowlist
        allowed = any(hostname == domain or hostname.endswith("." + domain) for domain in OFFICIAL_GOV_DOMAIN_ALLOWLIST)
        if not allowed:
            raise SecurityValidationError(
                f"Domain '{hostname}' is not in the official government allowlist. "
                f"Permitted domains: {', '.join(sorted(OFFICIAL_GOV_DOMAIN_ALLOWLIST))}"
            )

        return url

    @classmethod
    def compute_content_hash(cls, content: str) -> str:
        """Computes deterministic SHA-256 hash of raw source content."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @classmethod
    def ingest_observation(
        cls,
        db: Session,
        partner_id: str,
        metric_name: str,
        metric_value: Optional[float],
        metric_status_value: Optional[str],
        metric_unit: str,
        source_authority: str,
        source_url: str,
        source_document: str,
        period_start: Optional[str] = None,
        period_end: Optional[str] = None,
        data_as_of: Optional[str] = None,
        publication_date: Optional[str] = None,
        verification_status: str = "VERIFIED_OFFICIAL",
        match_confidence: str = "EXACT",
        institution_entity_id: Optional[str] = None,
        financial_scope: str = "INSTITUTION_LEVEL",
        raw_snapshot_id: Optional[str] = None
    ) -> Tuple[PartnerFinancialObservation, bool]:
        """
        Ingests a financial observation for a partner with strict audit provenance.
        Detects if value changed vs previous observation.
        If changed, marks previous observation `is_latest = False` and records new observation.
        If unchanged, updates `retrieved_at` timestamp.
        Returns (observation, is_changed: bool).
        """
        # Anti-fabrication check: Sector-level indicators must not be recorded as partner-level observations
        if source_authority == "SIDBI" and "SECTOR" in metric_name.upper():
            raise ValueError("Sector-level context cannot be attached as an individual partner financial observation")

        # Anti-fabrication check: Branch-level financial claim is rejected unless branch-level source exists
        if financial_scope == "BRANCH_LEVEL" and ("RBI" in source_authority or "NABARD" in source_authority):
            raise ValueError("Branch-level financial claim is rejected: statutory banking regulators (RBI/NABARD) publish institution-level accounts only, not branch-level balance sheets")

        # Look up existing latest observation for this partner and metric
        existing_stmt = select(PartnerFinancialObservation).where(
            and_(
                PartnerFinancialObservation.partner_id == partner_id,
                PartnerFinancialObservation.metric_name == metric_name,
                PartnerFinancialObservation.is_latest == True
            )
        )
        existing = db.execute(existing_stmt).scalars().first()

        # Check for change
        is_changed = True
        if existing:
            val_same = (existing.metric_value == metric_value)
            status_same = (existing.metric_status_value == metric_status_value)
            as_of_same = (existing.data_as_of == data_as_of)

            if val_same and status_same and as_of_same:
                # Unchanged: update retrieved_at and return
                existing.retrieved_at = utc_now()
                db.commit()
                return existing, False
            else:
                # Value changed: archive previous observation
                existing.is_latest = False
                db.add(existing)

        # Create new latest observation
        new_obs = PartnerFinancialObservation(
            partner_id=partner_id,
            institution_entity_id=institution_entity_id,
            metric_name=metric_name,
            metric_value=metric_value,
            metric_status_value=metric_status_value,
            metric_unit=metric_unit,
            financial_scope=financial_scope,
            raw_snapshot_id=raw_snapshot_id,
            source_authority=source_authority,
            source_url=source_url,
            source_document=source_document,
            period_start=period_start,
            period_end=period_end,
            data_as_of=data_as_of,
            publication_date=publication_date,
            retrieved_at=utc_now(),
            verification_status=verification_status,
            match_confidence=match_confidence,
            is_latest=True
        )
        db.add(new_obs)
        db.commit()
        db.refresh(new_obs)

        # Invalidate cached rule evaluation for this partner
        PrudentialRuleEngine.invalidate_cache()

        logger.info(
            f"Financial observation recorded: partner={partner_id}, metric={metric_name}, "
            f"value={metric_value or metric_status_value}, source={source_authority}, changed={is_changed}"
        )
        return new_obs, is_changed

    @classmethod
    def handle_source_failure(
        cls,
        db: Session,
        source_id: str,
        source_url: str,
        error_message: str
    ) -> Dict[str, Any]:
        """
        Handles failure when fetching from an official government source.
        STRICT BEHAVIOR:
        - NEVER wipes or nullifies previously verified observations.
        - Retains last_verified_value and last_verified_as_of intact.
        - Returns failure status report.
        """
        logger.warning(
            f"Official financial source fetch failed for '{source_id}' ({source_url}): {error_message}. "
            f"Existing verified observations retained without modification."
        )
        return {
            "source_id": source_id,
            "source_url": source_url,
            "status": "FETCH_FAILED",
            "error": error_message,
            "action": "RETAINED_PREVIOUS_VERIFIED_OBSERVATIONS",
            "timestamp": utc_now().isoformat()
        }

    @classmethod
    def check_observation_staleness(
        cls,
        db: Session,
        max_stale_months: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Checks all latest observations against reporting period policy.
        Annual reports are generally valid for up to 24 months before being flagged STALE.
        """
        stmt = select(PartnerFinancialObservation).where(PartnerFinancialObservation.is_latest == True)
        obs_list = db.execute(stmt).scalars().all()

        stale_records = []
        now = datetime.now()

        for obs in obs_list:
            if not obs.period_end:
                continue
            try:
                # Match YYYY-MM or YYYY
                parts = obs.period_end.split("-")
                year = int(parts[0])
                month = int(parts[1]) if len(parts) > 1 else 3  # default March (FY end in India)
                obs_date = datetime(year, month, 31)

                diff_months = (now.year - obs_date.year) * 12 + (now.month - obs_date.month)
                if diff_months > max_stale_months:
                    obs.verification_status = "STALE"
                    stale_records.append({
                        "observation_id": obs.id,
                        "partner_id": obs.partner_id,
                        "metric_name": obs.metric_name,
                        "period_end": obs.period_end,
                        "age_months": diff_months,
                        "status": "STALE"
                    })
            except Exception:
                pass

        if stale_records:
            db.commit()
            logger.info(f"Marked {len(stale_records)} observations as STALE based on statutory freshness policy.")

        return stale_records
