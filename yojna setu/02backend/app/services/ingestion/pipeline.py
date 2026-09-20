import uuid
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.scheme import Scheme
from app.models.candidate import CandidateScheme
from app.models.ingestion import SchemeSource, SourceSnapshot, PendingSchemeUpdate, IngestionRun
from app.services.ingestion.fetcher import BaseFetcher, HTMLFetcher, PDFFetcher, PARSER_VERSION, EXTRACTION_VERSION
from app.services.ingestion.change_detector import DeterministicChangeDetector, ChangeClassification
from app.services.ingestion.extractor import OfficialGovHTMLExtractor
from app.services.ingestion.pdf_extractor import OfficialGovPDFExtractor
from app.services.ingestion.normalizer import SchemeDataNormalizer
from app.services.ingestion.validator import SchemeDataValidator
from app.services.ingestion.health_monitor import SourceHealthMonitor

logger = logging.getLogger("yojnasetu.ingestion.pipeline")


class DynamicIngestionPipeline:
    """
    Orchestrator for the safe, multi-stage Dynamic Scheme Data Ingestion Pipeline.
    Pipeline execution:
    Source Fetch -> Snapshot Recording -> Deterministic Change Detection ->
    Extraction -> Normalization -> Validation -> Field Diffing -> Governance Classification ->
    Pending Scheme Update.

    Features:
    - Failure isolation: broken documents or network errors do not kill the run
    - Resumable batch execution with checkpoint tracking in IngestionRun
    - Idempotent repeated runs preventing duplicate candidates/updates
    - Source health event monitoring (HTTP errors, timeouts, malformed documents)
    - Provenance version stamping and field diff generation
    """

    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def run(
        self,
        source_id: str,
        fetcher: Optional[BaseFetcher] = None,
        force_update: bool = False,
        run_id: Optional[str] = None
    ) -> Dict[str, Any]:
        if not self.db:
            raise ValueError("Database session is required to run pipeline.")
        return self._run(self.db, source_id, fetcher, force_update, run_id)

    def run_pipeline(
        self,
        source_id_or_db: Union[str, Session],
        source_id: Optional[str] = None,
        fetcher: Optional[BaseFetcher] = None,
        force_update: bool = False,
        run_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Supports both instance and classmethod call styles:
        - instance.run_pipeline("SRC-001")
        - DynamicIngestionPipeline.run_pipeline(db, "SRC-001")
        """
        if isinstance(source_id_or_db, Session):
            db = source_id_or_db
            sid = source_id
        else:
            db = self.db
            sid = source_id_or_db

        if not db:
            raise ValueError("Database session is required.")
        if not sid:
            raise ValueError("source_id is required.")

        return self._run(db, sid, fetcher, force_update, run_id)

    @classmethod
    def _run(
        cls,
        db: Session,
        source_id: str,
        fetcher: Optional[BaseFetcher] = None,
        force_update: bool = False,
        run_id: Optional[str] = None
    ) -> Dict[str, Any]:
        start_time = time.time()
        # 1. Resolve registered official source
        source = db.query(SchemeSource).filter(SchemeSource.source_id == source_id).first()
        if not source:
            raise ValueError(f"Scheme source with ID '{source_id}' not found.")

        if not source.is_active and not force_update:
            return {
                "source_id": source.source_id,
                "fetch_status": "INACTIVE",
                "change_status": "NO_CHANGE",
                "governance_category": "AUTO_SAFE",
                "message": f"Source '{source.source_name}' is currently disabled."
            }

        target_scheme = None
        if source.scheme_id:
            target_scheme = db.query(Scheme).filter(Scheme.scheme_id == source.scheme_id).first()

        now = datetime.utcnow()
        active_fetcher = fetcher or (PDFFetcher() if source.source_type == "PDF" else HTMLFetcher())

        # 2. Fetch content with error categorization and failure isolation
        try:
            fetch_res = active_fetcher.fetch(source.source_url)
        except Exception as fetch_err:
            latency_ms = int((time.time() - start_time) * 1000)
            SourceHealthMonitor.record_event(
                db=db,
                source_id=source.source_id,
                status="FAILED",
                error_category="UNAVAILABLE_SOURCE",
                http_status_code=None,
                latency_ms=latency_ms,
                error_message=str(fetch_err),
                run_id=run_id
            )
            return {
                "source_id": source.source_id,
                "fetch_status": "FAILED",
                "change_status": "ERROR",
                "governance_category": "REJECTED",
                "error": str(fetch_err),
                "message": f"Source fetch failed: {str(fetch_err)}"
            }

        latency_ms = int((time.time() - start_time) * 1000)
        snapshot_id = f"SNAP-{uuid.uuid4().hex[:12]}"

        if not fetch_res.success:
            err_msg = fetch_res.error_message or "Unknown fetch error"
            err_cat = "HTTP_ERROR"
            if "timed out" in err_msg.lower():
                err_cat = "TIMEOUT"
            elif "malformed" in err_msg.lower() or "%pdf" in err_msg.lower():
                err_cat = "MALFORMED_DOCUMENT"
            elif "ssrf" in err_msg.lower():
                err_cat = "HTTP_ERROR"

            # Record health failure event
            SourceHealthMonitor.record_event(
                db=db,
                source_id=source.source_id,
                status="FAILED",
                error_category=err_cat,
                http_status_code=fetch_res.status_code,
                latency_ms=latency_ms,
                error_message=err_msg,
                run_id=run_id
            )

            source.last_status = "FAILED"
            source.last_fetched_at = now
            source.last_http_status = fetch_res.status_code
            source.retry_metadata = json.dumps({
                "last_attempt": now.isoformat(),
                "failures": source.consecutive_failures,
                "error": err_msg
            })

            failed_snapshot = SourceSnapshot(
                snapshot_id=snapshot_id,
                source_id=source.source_id,
                fetched_at=now,
                content_hash="FETCH_FAILED",
                content_type=fetch_res.content_type,
                raw_content=None,
                fetch_status="FAILED",
                http_status_code=fetch_res.status_code,
                error_message=err_msg
            )
            db.add(failed_snapshot)
            db.commit()

            return {
                "source_id": source.source_id,
                "fetch_status": "FAILED",
                "change_status": "ERROR",
                "classification": "OUTAGE_UNAVAILABLE",
                "change_classification": "OUTAGE_UNAVAILABLE",
                "governance_category": "REJECTED",
                "error": err_msg,
                "message": f"Source fetch failed: {err_msg}. Canonical scheme preserved without modification or deactivation."
            }

        # Successful fetch: record healthy status
        SourceHealthMonitor.record_event(
            db=db,
            source_id=source.source_id,
            status="HEALTHY",
            latency_ms=latency_ms,
            run_id=run_id
        )

        source.last_status = "SUCCESS"
        source.last_fetched_at = now
        source.last_success_at = now
        source.last_http_status = fetch_res.status_code
        source.consecutive_failures = 0

        # 3. Retrieve prior successful snapshot hash
        prev_snapshot = db.query(SourceSnapshot).filter(
            SourceSnapshot.source_id == source.source_id,
            SourceSnapshot.fetch_status == "SUCCESS"
        ).order_by(SourceSnapshot.fetched_at.desc()).first()

        prev_hash = prev_snapshot.content_hash if prev_snapshot else None

        # 4. Deterministic Change Detection
        raw_text_for_hash = fetch_res.content or (fetch_res.content_bytes.decode('latin1', errors='ignore') if fetch_res.content_bytes else "")
        change_res = DeterministicChangeDetector.detect_change(
            current_raw_content=raw_text_for_hash,
            previous_snapshot_hash=prev_hash
        )

        # If content has not changed compared to latest known snapshot:
        # DO NOT create duplicate snapshot. Update source metadata and exit.
        if prev_hash is not None and change_res.status == "NO_CHANGE" and not force_update:
            source.last_snapshot_hash = change_res.content_hash
            db.commit()
            return {
                "source_id": source.source_id,
                "fetch_status": "SUCCESS",
                "change_status": "NO_CHANGE",
                "classification": ChangeClassification.UNCHANGED,
                "change_classification": ChangeClassification.UNCHANGED,
                "governance_category": "AUTO_SAFE",
                "content_hash": change_res.content_hash,
                "previous_hash": prev_hash,
                "message": "Content hash identical to prior snapshot. No changes detected. Duplicate snapshot skipped."
            }

        # 5. Persist successful snapshot (Only for baseline first fetch or detected changes)
        snapshot = SourceSnapshot(
            snapshot_id=snapshot_id,
            source_id=source.source_id,
            fetched_at=now,
            content_hash=change_res.content_hash,
            content_type=fetch_res.content_type,
            raw_content=fetch_res.content[:50000] if fetch_res.content else None,
            fetch_status="SUCCESS",
            http_status_code=fetch_res.status_code,
            error_message=None
        )
        db.add(snapshot)
        source.last_snapshot_hash = change_res.content_hash

        # First fetch: establish baseline snapshot for existing/monitored sources
        is_new_scheme_source = source.scheme_id is None and (
            source.source_id.startswith("SRC-NEW-SCHEME") or
            source.source_id.startswith("SRC-DEEPTECH") or
            "new-scheme" in source.source_id.lower() or
            "deeptech" in source.source_id.lower()
        )
        if prev_hash is None and not force_update and not is_new_scheme_source:
            db.commit()
            return {
                "source_id": source.source_id,
                "fetch_status": "SUCCESS",
                "change_status": "NO_CHANGE",
                "classification": ChangeClassification.UNCHANGED,
                "change_classification": ChangeClassification.UNCHANGED,
                "governance_category": "AUTO_SAFE",
                "content_hash": change_res.content_hash,
                "previous_hash": None,
                "message": "Baseline snapshot established successfully. No prior snapshot existed."
            }

        # 6. Extraction
        try:
            if source.source_type == "PDF" and fetch_res.content_bytes:
                extractor = OfficialGovPDFExtractor()
                raw_extracted = extractor.extract(fetch_res.content_bytes, source.source_url)
            else:
                extractor = OfficialGovHTMLExtractor()
                raw_extracted = extractor.extract(fetch_res.content or "", source.source_url)
                # Follow linked official PDF guidelines if discovered in HTML portal
                linked_pdfs = raw_extracted.get("linked_pdfs", [])
                if linked_pdfs and isinstance(active_fetcher, HTMLFetcher):
                    try:
                        pdf_fetcher = PDFFetcher()
                        for pdf_url in linked_pdfs[:1]:
                            pdf_res = pdf_fetcher.fetch(pdf_url)
                            if pdf_res.success and pdf_res.content_bytes:
                                pdf_extractor = OfficialGovPDFExtractor()
                                pdf_extracted = pdf_extractor.extract(pdf_res.content_bytes, pdf_url)
                                for pk, pv in pdf_extracted.items():
                                    if pv is not None and (pk not in raw_extracted or raw_extracted[pk] is None):
                                        raw_extracted[pk] = pv
                    except Exception as pdf_err:
                        logger.warning(f"Failed to follow linked PDF for source '{source.source_id}': {pdf_err}")
        except Exception as ext_err:
            SourceHealthMonitor.record_event(
                db=db,
                source_id=source.source_id,
                status="DEGRADED",
                error_category="PARSING_FAILURE",
                latency_ms=latency_ms,
                error_message=str(ext_err),
                run_id=run_id
            )
            db.commit()
            return {
                "source_id": source.source_id,
                "fetch_status": "SUCCESS",
                "change_status": "ERROR",
                "governance_category": "REJECTED",
                "error": f"Extraction failure: {str(ext_err)}"
            }

        # 7. Normalization
        candidate_data = SchemeDataNormalizer.normalize(raw_extracted)

        # 8. Validation
        val_res = SchemeDataValidator.validate(candidate_data)

        # 8b. Deterministic matching if canonical scheme not linked
        if not target_scheme:
            cand_id = candidate_data.get("scheme_id") or candidate_data.get("scheme_code")
            if cand_id:
                target_scheme = db.query(Scheme).filter(
                    (Scheme.scheme_id == cand_id) | (Scheme.scheme_code == cand_id)
                ).first()
            if not target_scheme and candidate_data.get("scheme_name"):
                s_name = candidate_data["scheme_name"].strip().lower()
                target_scheme = db.query(Scheme).filter(
                    func.lower(Scheme.scheme_name) == s_name
                ).first()
            if not target_scheme and source.source_url:
                target_scheme = db.query(Scheme).filter(
                    Scheme.official_source_url == source.source_url
                ).first()
            if target_scheme:
                source.scheme_id = target_scheme.scheme_id

        # 8c. Deactivation evidence check
        is_deactivated, deact_reason = DeterministicChangeDetector.detect_deactivation_evidence(
            raw_text_for_hash, candidate_data
        )

        # 9. Structured Field-level Diffing against Canonical Scheme & Governance
        if target_scheme and is_deactivated:
            proposal_type = "DEACTIVATION"
            change_classification = ChangeClassification.POSSIBLY_WITHDRAWN
            governance_category = "NEEDS_REVIEW"
            detected_changes = [{
                "field": "scheme_status",
                "change_type": "MODIFIED",
                "old_value": target_scheme.scheme_status or "ACTIVE",
                "new_value": "INACTIVE",
                "is_critical": True,
                "diff_text": f"PROPOSED DEACTIVATION: {deact_reason or 'Authoritative closure notice detected'}",
                "source_url": source.source_url,
                "detected_at": now.isoformat(),
                "confidence": 1.0,
                "validation_status": val_res.status
            }]
        elif not target_scheme:
            proposal_type = "NEW_SCHEME"
            change_classification = ChangeClassification.NEW_SCHEME
            detected_changes, governance_category = DeterministicChangeDetector.generate_field_diffs(
                target_scheme=None,
                candidate_data=candidate_data,
                source_url=source.source_url,
                validation_status=val_res.status,
                detected_at=now.isoformat()
            )
        else:
            proposal_type = "MODIFICATION"
            change_classification = ChangeClassification.MODIFIED
            detected_changes, governance_category = DeterministicChangeDetector.generate_field_diffs(
                target_scheme=target_scheme,
                candidate_data=candidate_data,
                source_url=source.source_url,
                validation_status=val_res.status,
                detected_at=now.isoformat()
            )

        if not val_res.is_valid:
            governance_category = "REJECTED"

        # 5-way Classification: If content hash changed, but extracted parameters match canonical scheme:
        if not detected_changes and not force_update and target_scheme:
            db.commit()
            return {
                "source_id": source.source_id,
                "fetch_status": "SUCCESS",
                "change_status": "SOURCE_CHANGED_ONLY",
                "classification": ChangeClassification.SOURCE_CHANGED_ONLY,
                "change_classification": ChangeClassification.SOURCE_CHANGED_ONLY,
                "governance_category": "AUTO_SAFE",
                "content_hash": change_res.content_hash,
                "previous_hash": prev_hash,
                "message": "Source page/PDF changed without meaningful scheme-data change (SOURCE_CHANGED_ONLY)."
            }

        # 10. Create or Update Pending Scheme Update (Idempotent)
        existing_update = db.query(PendingSchemeUpdate).filter(
            PendingSchemeUpdate.source_id == source.source_id,
            PendingSchemeUpdate.status == "PENDING"
        ).first()

        if existing_update:
            existing_update.proposal_type = proposal_type
            existing_update.change_classification = change_classification
            existing_update.extracted_data = json.dumps(candidate_data, default=str)
            existing_update.detected_changes = json.dumps(detected_changes, default=str)
            existing_update.validation_status = val_res.status
            existing_update.governance_category = governance_category
            existing_update.snapshot_id = snapshot.snapshot_id
            update_id = existing_update.update_id
        else:
            update_id = f"UPD-{uuid.uuid4().hex[:12]}"
            pending_update = PendingSchemeUpdate(
                update_id=update_id,
                scheme_id=target_scheme.scheme_id if target_scheme else (source.scheme_id or "NEW_SCHEME"),
                source_id=source.source_id,
                snapshot_id=snapshot.snapshot_id,
                proposal_type=proposal_type,
                change_classification=change_classification,
                old_version=target_scheme.scheme_version if (target_scheme and target_scheme.scheme_version) else "1.0",
                extracted_data=json.dumps(candidate_data, default=str),
                detected_changes=json.dumps(detected_changes, default=str),
                validation_status=val_res.status,
                validation_errors=json.dumps(val_res.errors + val_res.warnings, default=str),
                governance_category=governance_category,
                status="PENDING",
                created_at=now
            )
            db.add(pending_update)

        # If NEW_SCHEME: also stage in CandidateScheme for governance
        if proposal_type == "NEW_SCHEME":
            cand_id = f"CAND-{uuid.uuid4().hex[:10]}"
            cand_existing = db.query(CandidateScheme).filter(
                CandidateScheme.official_source_url == source.source_url
            ).first()
            if not cand_existing:
                db.add(CandidateScheme(
                    candidate_id=cand_id,
                    discovered_name=candidate_data.get("scheme_name") or source.source_name,
                    normalized_name=candidate_data.get("scheme_name") or source.source_name,
                    ministry=candidate_data.get("ministry") or source.authority,
                    official_source_url=source.source_url,
                    source_document=source.source_url,
                    extracted_data=json.dumps(candidate_data, default=str),
                    candidate_status="STAGED",
                    verification_status="OFFICIALLY_VERIFIED",
                    duplicate_status="UNIQUE",
                    validation_status=val_res.status,
                    data_confidence="HIGH" if val_res.is_valid else "MEDIUM",
                    created_at=now
                ))

        db.commit()

        logger.info(
            f"Pipeline completed for source '{source_id}': classification={change_classification}, diffs={len(detected_changes)}, "
            f"changes={[d.get('field') for d in detected_changes]}, governance={governance_category}, run_id={run_id}"
        )

        structured_diff_summary = DeterministicChangeDetector.build_structured_diff_summary(
            diffs=detected_changes,
            source_url=source.source_url,
            validation_status=val_res.status
        )

        change_status_val = "CHANGE_DETECTED"
        if change_classification == ChangeClassification.POSSIBLY_WITHDRAWN:
            change_status_val = "POSSIBLY_WITHDRAWN"
        elif change_classification == ChangeClassification.NEW_SCHEME:
            change_status_val = "NEW_SCHEME"

        return {
            "source_id": source.source_id,
            "fetch_status": "SUCCESS",
            "change_status": change_status_val,
            "classification": change_classification,
            "change_classification": change_classification,
            "proposal_type": proposal_type,
            "governance_category": governance_category,
            "content_hash": change_res.content_hash,
            "previous_hash": prev_hash,
            "pending_update_id": update_id,
            "detected_change_count": len(detected_changes),
            "detected_changes": detected_changes,
            "structured_diff": structured_diff_summary,
            "validation_status": val_res.status,
            "message": f"Change classified as {change_classification}! Generated pending update '{update_id}' with {len(detected_changes)} field diff(s)."
        }

    @classmethod
    def run_resumable_batch(
        cls,
        db: Session,
        source_ids: List[str],
        run_id: Optional[str] = None,
        resume: bool = False,
        force_update: bool = False
    ) -> IngestionRun:
        """
        Executes a batch ingestion run across multiple sources with:
        1. Resumability: saves checkpoints; resumes from last unprocessed index.
        2. Failure isolation: single source failure does not terminate batch.
        3. Metrics tracking: counts seen, changed, unchanged, failed, needing_review.
        """
        now = datetime.utcnow()
        active_run = None

        if resume and run_id:
            active_run = db.query(IngestionRun).filter(IngestionRun.run_id == run_id).first()

        if not active_run:
            actual_run_id = run_id or f"RUN-{uuid.uuid4().hex[:12]}"
            active_run = IngestionRun(
                run_id=actual_run_id,
                started_at=now,
                status="RUNNING",
                records_seen=0,
                records_changed=0,
                records_unchanged=0,
                records_failed=0,
                records_staged=0,
                records_promoted=0,
                records_needing_review=0,
                checkpoint_data=json.dumps({"processed_sources": [], "last_source_id": None}),
                error_summary=json.dumps([])
            )
            db.add(active_run)
            db.commit()

        # Parse checkpoint data
        checkpoint = json.loads(active_run.checkpoint_data or "{}")
        processed_set = set(checkpoint.get("processed_sources", []))

        for sid in source_ids:
            if sid in processed_set and not force_update:
                logger.info(f"Skipping already processed source '{sid}' in resumed run '{active_run.run_id}'.")
                continue

            active_run.records_seen += 1
            try:
                result = cls._run(db, sid, force_update=force_update, run_id=active_run.run_id)

                if result.get("fetch_status") == "FAILED" or result.get("change_status") == "ERROR":
                    active_run.records_failed += 1
                elif result.get("change_status") == "CHANGE_DETECTED":
                    active_run.records_changed += 1
                    if result.get("governance_category") == "NEEDS_REVIEW":
                        active_run.records_needing_review += 1
                else:
                    active_run.records_unchanged += 1

            except Exception as item_err:
                logger.error(f"Failure isolation: error processing source '{sid}': {item_err}")
                active_run.records_failed += 1
                SourceHealthMonitor.record_event(
                    db=db,
                    source_id=sid,
                    status="FAILED",
                    error_category="UNAVAILABLE_SOURCE",
                    error_message=str(item_err),
                    run_id=active_run.run_id
                )

            # Update checkpoint after each source
            processed_set.add(sid)
            active_run.checkpoint_data = json.dumps({
                "processed_sources": list(processed_set),
                "last_source_id": sid,
                "updated_at": datetime.utcnow().isoformat()
            })
            db.commit()

        active_run.status = "COMPLETED"
        active_run.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(active_run)
        return active_run
