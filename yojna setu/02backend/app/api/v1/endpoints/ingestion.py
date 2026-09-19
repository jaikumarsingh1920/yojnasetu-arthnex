"""
Endpoints for Dynamic Scheme Data Ingestion Pipeline.
Provides administrative endpoints for:
- Registering official government sources
- Viewing historical snapshots
- Triggering pipeline runs (Fetch -> Change Detect -> Extract -> Normalize -> Validate -> Pending Update)
- Listing and reviewing pending scheme updates (Admin Approval / Rejection)
- Syncing canonical data, rules, and RAG vector store
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

logger = logging.getLogger("yojnasetu.api.ingestion")

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.ingestion import SchemeSource, SourceSnapshot, PendingSchemeUpdate
from app.models.scheme import Scheme
from app.schemas.ingestion import (
    SourceCreateInput,
    SourceUpdateInput,
    SourceResponse,
    SnapshotResponse,
    PendingUpdateResponse,
    PendingUpdateReviewInput,
    PipelineRunResponse,
)
from app.services.ingestion.pipeline import DynamicIngestionPipeline
from app.services.ingestion.approval_service import PendingUpdateApprovalService
from app.services.ingestion.scheduler import auto_scheduler

router = APIRouter()


# ---------------------------------------------------------------------------
# Source Registry Endpoints
# ---------------------------------------------------------------------------

@router.get("/sources", response_model=List[SourceResponse], summary="List registered scheme sources")
def list_sources(
    active_only: bool = Query(False, description="Filter only active sources"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SYSTEM_ADMIN)),
):
    """List all registered external scheme sources with health and fetch status."""
    query = db.query(SchemeSource)
    if active_only:
        query = query.filter(SchemeSource.is_active == True)
    return query.order_by(SchemeSource.created_at.desc()).all()


@router.post("/sources", response_model=SourceResponse, status_code=status.HTTP_201_CREATED, summary="Register an official scheme source")
def register_source(
    payload: SourceCreateInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SYSTEM_ADMIN)),
):
    """Register a new official government scheme source."""
    existing = db.query(SchemeSource).filter(SchemeSource.source_id == payload.source_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Source with ID '{payload.source_id}' is already registered."
        )

    # If scheme_id is provided, verify scheme exists
    if payload.scheme_id:
        scheme = db.query(Scheme).filter(Scheme.id == payload.scheme_id).first()
        if not scheme:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Canonical scheme '{payload.scheme_id}' not found."
            )

    source = SchemeSource(
        source_id=payload.source_id,
        scheme_id=payload.scheme_id,
        source_name=payload.source_name,
        source_url=payload.source_url,
        authority=payload.authority,
        source_type=payload.source_type,
        fetch_frequency_hours=payload.fetch_frequency_hours,
        is_active=True,
        last_status="UNFETCHED"
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@router.post("/sources/seed-poc", response_model=List[SourceResponse], summary="Seed initial official POC sources")
def seed_poc_sources(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SYSTEM_ADMIN)),
):
    """
    Seeds initial safe official government sources for the POC:
    1. PMEGP (Prime Minister's Employment Generation Programme) - KVIC / MSME
    2. PM SVANidhi (PM Street Vendor's AtmaNirbhar Nidhi) - MoHUA
    """
    poc_sources = [
        {
            "source_id": "SRC-PMEGP-001",
            "scheme_id": "SIH26092-001",
            "source_name": "KVIC Official Portal - Prime Minister's Employment Generation Programme",
            "source_url": "https://www.kviconline.gov.in/pmegpeportal/pmegphome/index.jsp",
            "authority": "Ministry of Micro, Small and Medium Enterprises (MSME) & KVIC",
            "source_type": "HTML",
            "fetch_frequency_hours": 24,
        },
        {
            "source_id": "SRC-PMSVANIDHI-001",
            "scheme_id": "SIH26092-004",
            "source_name": "PM SVANidhi Official Portal - MoHUA",
            "source_url": "https://pmsvanidhi.mohua.gov.in/",
            "authority": "Ministry of Housing and Urban Affairs (MoHUA)",
            "source_type": "HTML",
            "fetch_frequency_hours": 24,
        },
    ]

    seeded = []
    for data in poc_sources:
        existing = db.query(SchemeSource).filter(SchemeSource.source_id == data["source_id"]).first()
        if not existing:
            source = SchemeSource(
                source_id=data["source_id"],
                scheme_id=data["scheme_id"],
                source_name=data["source_name"],
                source_url=data["source_url"],
                authority=data["authority"],
                source_type=data["source_type"],
                fetch_frequency_hours=data["fetch_frequency_hours"],
                is_active=True,
                last_status="UNFETCHED"
            )
            db.add(source)
            seeded.append(source)
        else:
            seeded.append(existing)

    db.commit()
    for s in seeded:
        db.refresh(s)
    return seeded


@router.get("/sources/{source_id}/snapshots", response_model=List[SnapshotResponse], summary="List snapshots for a source")
def list_source_snapshots(
    source_id: str,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SYSTEM_ADMIN)),
):
    """Retrieve historical raw snapshots captured for an official source."""
    source = db.query(SchemeSource).filter(SchemeSource.source_id == source_id).first()
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source '{source_id}' not found."
        )

    snapshots = (
        db.query(SourceSnapshot)
        .filter(SourceSnapshot.source_id == source_id)
        .order_by(SourceSnapshot.fetched_at.desc())
        .limit(limit)
        .all()
    )
    return snapshots


# ---------------------------------------------------------------------------
# Pipeline Execution
# ---------------------------------------------------------------------------

@router.post("/sources/{source_id}/run", response_model=PipelineRunResponse, summary="Run ingestion pipeline on a source")
def run_source_pipeline(
    source_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SYSTEM_ADMIN)),
):
    """
    Executes the ingestion pipeline on the specified source:
    1. Fetches official government source content
    2. Stores immutable timestamped snapshot with SHA-256 hash
    3. Performs deterministic change detection against previous snapshot
    4. If change detected: extracts, normalizes, validates candidate data
    5. If candidate data has diffs: creates a PendingSchemeUpdate proposal for admin review
    6. Does NOT mutate canonical scheme data until approved
    """
    pipeline = DynamicIngestionPipeline(db)
    result = pipeline.run_pipeline(source_id)

    if result.get("change_status") == "ERROR":
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=result.get("message", "Pipeline execution failed.")
        )

    return PipelineRunResponse(**result)


# ---------------------------------------------------------------------------
# Background Scheduler Endpoints
# ---------------------------------------------------------------------------

@router.get("/scheduler/status", summary="Get background scheduler status and telemetry")
def get_scheduler_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SYSTEM_ADMIN)),
):
    """
    Returns administrative status and telemetry of the automatic government scheme ingestion scheduler:
    - scheduler_enabled (bool)
    - is_running (bool)
    - is_executing_cycle (bool)
    - interval_minutes (int)
    - last_run (records seen, changed, staged, failed, etc.)
    - last_successful_run_at (ISO timestamp)
    - next_scheduled_run (ISO timestamp)
    - pending_updates_count (int)
    - sources_summary (total, active, healthy, degraded, failed)
    """
    return auto_scheduler.get_status(db=db)


@router.post("/scheduler/trigger", summary="Trigger an immediate on-demand ingestion run")
def trigger_scheduler_run(
    force_update: bool = Query(False, description="Force re-fetch and evaluation regardless of interval/backoff"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SYSTEM_ADMIN)),
):
    """
    Manually triggers an on-demand ingestion run across all active government sources.
    Respects concurrency lock: if a cycle is already executing, returns ALREADY_RUNNING status.
    """
    return auto_scheduler.trigger_now(db=db, force_update=force_update)


# ---------------------------------------------------------------------------
# Pending Scheme Updates & Admin Approval
# ---------------------------------------------------------------------------

@router.get("/pending-updates", response_model=List[PendingUpdateResponse], summary="List pending scheme updates")
def list_pending_updates(
    status_filter: Optional[str] = Query(None, description="Filter by status: PENDING, APPROVED, REJECTED"),
    scheme_id: Optional[str] = Query(None, description="Filter by canonical scheme ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SYSTEM_ADMIN)),
):
    """List pending update proposals awaiting admin review."""
    query = db.query(PendingSchemeUpdate)
    if status_filter:
        query = query.filter(PendingSchemeUpdate.status == status_filter.upper())
    if scheme_id:
        query = query.filter(PendingSchemeUpdate.scheme_id == scheme_id)

    return query.order_by(PendingSchemeUpdate.created_at.desc()).all()


@router.get("/pending-updates/{update_id}", response_model=PendingUpdateResponse, summary="Get pending update details")
def get_pending_update(
    update_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SYSTEM_ADMIN)),
):
    """Get full details of a pending update proposal, including field diffs and validation results."""
    update = db.query(PendingSchemeUpdate).filter(PendingSchemeUpdate.update_id == update_id).first()
    if not update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pending update '{update_id}' not found."
        )
    return update


@router.post("/pending-updates/{update_id}/review", response_model=PendingUpdateResponse, summary="Approve or reject pending update")
def review_pending_update(
    update_id: str,
    review_input: PendingUpdateReviewInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SYSTEM_ADMIN)),
):
    """
    Human-in-the-Loop Admin Review Decision:
    - APPROVE: Updates canonical Scheme record in DB, increments version, logs audit entry in SchemeChangelog, syncs SchemeRule records, and triggers RAG index refresh.
    - REJECT: Leaves canonical scheme completely unchanged. Marks proposal as REJECTED with provided reason.
    """
    approval_service = PendingUpdateApprovalService(db)
    reviewer_identity = current_user.email or current_user.user_id

    try:
        updated = approval_service.process_review(
            update_id=update_id,
            action=review_input.action,
            reviewer_id=reviewer_identity,
            reason=review_input.reason
        )
        return updated
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ---------------------------------------------------------------------------
# Large-Scale Scheme Discovery, Staging & Candidate Governance Endpoints
# ---------------------------------------------------------------------------

from app.models.candidate import CandidateScheme
from app.models.rule import SchemeRule
from app.models.document import SchemeDocument
from app.models.verification import SchemeVerification
from app.schemas.candidate import (
    CandidateSchemeResponse,
    CandidateReviewInput,
    CandidateReviewResponse,
    DiscoveryBatchRunInput,
    DiscoveryBatchRunResponse,
    IngestionQualityMetricsResponse,
)
from app.services.ingestion.discovery_worker import SchemeDiscoveryWorker
from app.services.ingestion.promotion_service import CandidatePromotionService
import json


def _serialize_candidate(c: CandidateScheme) -> Dict[str, Any]:
    try:
        ext = json.loads(c.extracted_data) if c.extracted_data else {}
    except Exception:
        ext = {}
    try:
        miss = json.loads(c.missing_fields) if c.missing_fields else []
    except Exception:
        miss = []
    try:
        evi = json.loads(c.evidence) if c.evidence else {}
    except Exception:
        evi = {}
    try:
        val_err = json.loads(c.validation_errors) if c.validation_errors else []
    except Exception:
        val_err = []

    return {
        "candidate_id": c.candidate_id,
        "run_id": c.run_id,
        "discovered_name": c.discovered_name,
        "normalized_name": c.normalized_name,
        "scheme_code": c.scheme_code,
        "discovery_source": c.discovery_source,
        "discovery_url": c.discovery_url,
        "official_source_url": c.official_source_url,
        "source_document": c.source_document,
        "source_type": c.source_type,
        "ministry": c.ministry,
        "implementing_agency": c.implementing_agency,
        "level": c.level,
        "state_coverage": c.state_coverage,
        "district_coverage": c.district_coverage,
        "sector": c.sector,
        "scheme_category": c.scheme_category,
        "target_beneficiaries": c.target_beneficiaries,
        "stated_benefits": c.stated_benefits,
        "relevance_status": c.relevance_status,
        "relevance_reason": c.relevance_reason,
        "extraction_status": c.extraction_status,
        "verification_status": c.verification_status,
        "duplicate_status": c.duplicate_status,
        "duplicate_of_scheme_id": c.duplicate_of_scheme_id,
        "data_confidence": c.data_confidence,
        "extracted_data": ext,
        "missing_fields": miss,
        "evidence": evi,
        "validation_status": c.validation_status,
        "validation_errors": val_err,
        "candidate_status": c.candidate_status,
        "admin_notes": c.admin_notes,
        "rejection_reason": c.rejection_reason,
        "created_at": c.created_at,
        "updated_at": c.updated_at,
        "reviewed_at": c.reviewed_at,
        "reviewed_by": c.reviewed_by,
    }


@router.post("/discovery/run", response_model=DiscoveryBatchRunResponse, summary="Execute automated scheme discovery batch")
def run_discovery_batch(
    payload: DiscoveryBatchRunInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SYSTEM_ADMIN)),
):
    """
    Automated discovery worker execution across central ministries, state portals,
    and implementing agency directories. Discovers, classifies relevance, resolves
    authoritative sources, checks duplicates, and stages candidates without manual data entry.
    """
    worker = SchemeDiscoveryWorker(db)
    result = worker.run_discovery_batch(
        target_source=payload.target_source,
        max_candidates=payload.max_candidates
    )
    result["message"] = f"Batch discovery run completed successfully with {result['staged_for_review']} candidates staged."
    return DiscoveryBatchRunResponse(**result)


@router.get("/candidates", response_model=List[CandidateSchemeResponse], summary="List staged candidate schemes")
def list_candidates(
    status_filter: Optional[str] = Query(None, description="Filter by candidate status: DISCOVERED, STAGED, APPROVED, REJECTED, ARCHIVED"),
    relevance_filter: Optional[str] = Query(None, description="Filter by relevance: HIGH_PRIORITY, RELEVANT, LOW_PRIORITY, IRRELEVANT"),
    ministry_filter: Optional[str] = Query(None, description="Filter by ministry"),
    duplicate_filter: Optional[str] = Query(None, description="Filter by duplicate status: UNIQUE, DUPLICATE_CANDIDATE, MERGED"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SYSTEM_ADMIN)),
):
    """List staged candidate schemes awaiting human-in-the-loop review."""
    query = db.query(CandidateScheme)
    if status_filter:
        query = query.filter(CandidateScheme.candidate_status == status_filter.upper())
    if relevance_filter:
        query = query.filter(CandidateScheme.relevance_status == relevance_filter.upper())
    if ministry_filter:
        query = query.filter(CandidateScheme.ministry.ilike(f"%{ministry_filter}%"))
    if duplicate_filter:
        query = query.filter(CandidateScheme.duplicate_status == duplicate_filter.upper())

    candidates = query.order_by(CandidateScheme.created_at.desc()).limit(limit).all()
    return [_serialize_candidate(c) for c in candidates]


@router.get("/candidates/{candidate_id}", response_model=CandidateSchemeResponse, summary="Get candidate scheme details")
def get_candidate_detail(
    candidate_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SYSTEM_ADMIN)),
):
    """Get full details of a staged candidate scheme including extracted parameters, evidence, and validation notes."""
    candidate = db.query(CandidateScheme).filter(CandidateScheme.candidate_id == candidate_id).first()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CandidateScheme '{candidate_id}' not found."
        )
    return _serialize_candidate(candidate)


@router.post("/candidates/{candidate_id}/review", response_model=CandidateReviewResponse, summary="Admin review of candidate scheme")
def review_candidate(
    candidate_id: str,
    payload: CandidateReviewInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SYSTEM_ADMIN)),
):
    """
    Human-in-the-loop review decision for a staged candidate:
    - APPROVE: Promotes candidate to canonical Scheme DB, generates statutory rules & documents, writes changelog, and triggers RAG index sync.
    - REJECT: Leaves canonical DB untouched, marks candidate as REJECTED with reason.
    - NEEDS_REVIEW: Flags candidate for manual triage or additional official documentation.
    """
    candidate = db.query(CandidateScheme).filter(CandidateScheme.candidate_id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"CandidateScheme '{candidate_id}' not found.")

    act = payload.action.strip().upper()
    admin_id = current_user.email or current_user.user_id
    now = datetime.utcnow()

    if act == "APPROVE":
        try:
            promoted = CandidatePromotionService.promote_candidate(
                db=db,
                candidate_id=candidate_id,
                reviewer_id=admin_id,
                notes=payload.notes
            )
            return CandidateReviewResponse(
                candidate_id=candidate.candidate_id,
                candidate_status="APPROVED",
                canonical_scheme_id=promoted.scheme_id,
                message=f"Candidate successfully approved and promoted to canonical scheme '{promoted.scheme_id}'."
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(f"Failed to promote candidate {candidate_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Promotion failed: {str(e)}"
            )

    elif act == "REJECT":
        candidate.candidate_status = "REJECTED"
        candidate.rejection_reason = payload.rejection_reason or payload.notes or "Rejected by administrative reviewer"
        candidate.reviewed_at = now
        candidate.reviewed_by = admin_id
        db.commit()
        return CandidateReviewResponse(
            candidate_id=candidate.candidate_id,
            candidate_status="REJECTED",
            canonical_scheme_id=None,
            message=f"Candidate '{candidate_id}' marked as REJECTED. Canonical DB untouched."
        )

    elif act == "NEEDS_REVIEW":
        candidate.candidate_status = "NEEDS_REVIEW"
        candidate.admin_notes = payload.notes
        candidate.reviewed_at = now
        candidate.reviewed_by = admin_id
        db.commit()
        return CandidateReviewResponse(
            candidate_id=candidate.candidate_id,
            candidate_status="NEEDS_REVIEW",
            canonical_scheme_id=None,
            message=f"Candidate '{candidate_id}' flagged for further review."
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid review action '{payload.action}'. Must be APPROVE, REJECT, or NEEDS_REVIEW."
        )


@router.get("/metrics", response_model=IngestionQualityMetricsResponse, summary="Ingestion data quality & pipeline metrics")
def get_ingestion_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SYSTEM_ADMIN)),
):
    """
    Returns end-to-end data quality, coverage, and intelligence metrics for the YojnaSetu
    Smart Automation scheme acquisition pipeline.
    """
    total_canonical = db.query(Scheme).count()
    total_candidates = db.query(CandidateScheme).count()
    staged = db.query(CandidateScheme).filter(CandidateScheme.candidate_status == "STAGED").count()
    approved = db.query(CandidateScheme).filter(CandidateScheme.candidate_status == "APPROVED").count()
    rejected = db.query(CandidateScheme).filter(CandidateScheme.candidate_status == "REJECTED").count()
    verified = db.query(CandidateScheme).filter(CandidateScheme.verification_status == "OFFICIALLY_VERIFIED").count()
    dups = db.query(CandidateScheme).filter(CandidateScheme.duplicate_status == "DUPLICATE_CANDIDATE").count()

    schemes_with_rules = db.query(SchemeRule.scheme_id).distinct().count()
    schemes_with_docs = db.query(SchemeDocument.scheme_id).distinct().count()
    schemes_with_evidence = db.query(SchemeVerification.scheme_id).filter(SchemeVerification.verification_status == "VERIFIED").distinct().count()

    # Coverage by level
    levels = {}
    for (lvl, count) in db.query(Scheme.scheme_type, func.count(Scheme.scheme_id)).group_by(Scheme.scheme_type).all():
        levels[lvl or "UNKNOWN"] = count

    # Top ministries
    ministries = {}
    for (min_name, count) in (
        db.query(Scheme.ministry, func.count(Scheme.scheme_id))
        .filter(Scheme.ministry.isnot(None))
        .group_by(Scheme.ministry)
        .order_by(func.count(Scheme.scheme_id).desc())
        .limit(10)
        .all()
    ):
        ministries[min_name] = count

    # Top categories / sectors
    categories = {}
    for (sec, count) in (
        db.query(Scheme.sector, func.count(Scheme.scheme_id))
        .filter(Scheme.sector.isnot(None))
        .group_by(Scheme.sector)
        .order_by(func.count(Scheme.scheme_id).desc())
        .limit(8)
        .all()
    ):
        categories[sec] = count

    # State coverage count
    states = db.query(Scheme.state_coverage).filter(Scheme.state_coverage != "All India").distinct().count()

    return IngestionQualityMetricsResponse(
        total_canonical_schemes=total_canonical,
        total_candidates_discovered=total_candidates,
        candidates_staged_for_review=staged,
        candidates_approved=approved,
        candidates_rejected=rejected,
        candidates_officially_verified=verified,
        candidates_duplicate_flagged=dups,
        canonical_schemes_with_rules=schemes_with_rules,
        canonical_schemes_with_documents=schemes_with_docs,
        canonical_schemes_with_official_evidence=schemes_with_evidence,
        coverage_by_level=levels,
        top_ministries=ministries,
        top_categories=categories,
        state_coverage_count=states
    )

