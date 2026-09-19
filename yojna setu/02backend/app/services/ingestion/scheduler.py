"""
Automated Government Scheme Ingestion Scheduler Service for YojnaSetu.
SIH26092 Smart Automation.

Features:
- Configurable scheduling interval (environment / config driven)
- Enable/disable toggle (SCHEME_INGESTION_ENABLED)
- Singleton architecture with strict concurrency locks preventing duplicate workers
- Clean application startup and shutdown lifecycle management (FastAPI lifespan compatible)
- Per-source failure isolation: network/parsing failure on one source does not abort the run
- Exponential backoff & retry tracking for degraded/failing sources
- Machine-readable scheduler telemetry and admin observability
- Safe execution: creates PendingSchemeUpdate proposals; never directly mutates canonical schemes
"""

import asyncio
import logging
import threading
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.ingestion import SchemeSource, IngestionRun, PendingSchemeUpdate, SourceHealthLog
from app.services.ingestion.pipeline import DynamicIngestionPipeline
from app.services.ingestion.health_monitor import SourceHealthMonitor

logger = logging.getLogger("yojnasetu.ingestion.scheduler")


class AutoIngestionScheduler:
    """
    Singleton Background Scheduler for Automatic Scheme Ingestion.
    Monitors registered official government scheme sources at configurable intervals,
    detects changes, isolates errors, and generates staged pending updates for admin review.
    """

    _instance: Optional["AutoIngestionScheduler"] = None
    _singleton_lock: threading.Lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = super(AutoIngestionScheduler, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(
        self,
        interval_minutes: Optional[int] = None,
        interval_hours: Optional[int] = None,
        interval_days: Optional[int] = None,
        enabled: Optional[bool] = None,
        batch_size: Optional[int] = None,
        backoff_hours: Optional[int] = None,
    ):
        if not getattr(self, "_initialized", False):
            # Cadence configuration: 24-hour (1440 minutes) schedule
            if interval_minutes is not None:
                self.interval_minutes = interval_minutes
                self.interval_hours = interval_minutes // 60
                self.interval_days = max(1, interval_minutes // 1440)
            elif interval_hours is not None:
                self.interval_hours = interval_hours
                self.interval_minutes = interval_hours * 60
                self.interval_days = max(1, interval_hours // 24)
            elif interval_days is not None:
                self.interval_days = interval_days
                self.interval_hours = interval_days * 24
                self.interval_minutes = interval_days * 24 * 60
            elif getattr(settings, "SCHEME_INGEST_INTERVAL_HOURS", None) is not None:
                self.interval_hours = settings.SCHEME_INGEST_INTERVAL_HOURS
                self.interval_minutes = self.interval_hours * 60
                self.interval_days = max(1, self.interval_hours // 24)
            elif getattr(settings, "SCHEME_INGEST_INTERVAL_DAYS", None) is not None:
                self.interval_days = settings.SCHEME_INGEST_INTERVAL_DAYS
                self.interval_hours = self.interval_days * 24
                self.interval_minutes = self.interval_days * 24 * 60
            else:
                self.interval_minutes = getattr(settings, "SCHEME_INGESTION_INTERVAL_MINUTES", 1440)
                self.interval_hours = self.interval_minutes // 60
                self.interval_days = max(1, self.interval_minutes // 1440)

            self.enabled = enabled if enabled is not None else settings.SCHEME_INGESTION_ENABLED
            self.batch_size = batch_size if batch_size is not None else settings.SCHEME_INGESTION_BATCH_SIZE
            self.backoff_hours = backoff_hours if backoff_hours is not None else settings.SCHEME_INGESTION_RETRY_BACKOFF_HOURS

            self._lock = threading.Lock()
            self._is_running = False
            self._is_executing_cycle = False
            self._stop_event = threading.Event()
            self._worker_thread: Optional[threading.Thread] = None
            self._async_task: Optional[asyncio.Task] = None

            self._last_run_time: Optional[datetime] = None
            self._last_run_status: str = "IDLE"
            self._next_run_time: Optional[datetime] = None
            self._last_run_id: Optional[str] = None
            self._last_metrics: Dict[str, Any] = {
                "records_seen": 0,
                "records_changed": 0,
                "records_unchanged": 0,
                "records_failed": 0,
                "records_staged": 0,
                "records_needing_review": 0,
                "sources_checked": 0,
                "sources_succeeded": 0,
                "sources_failed": 0,
                "unchanged_sources": 0,
                "changed_sources": 0,
                "new_schemes_detected": 0,
                "modified_schemes_detected": 0,
                "deactivation_candidates": 0,
                "validation_failures": 0,
                "pending_admin_reviews": 0,
            }

            self._initialized = True
            logger.info(
                f"AutoIngestionScheduler initialized: enabled={self.enabled}, cadence={self.interval_hours}h ({self.interval_minutes}m), "
                f"batch_size={self.batch_size}, backoff={self.backoff_hours}h"
            )
        else:
            self.configure(
                interval_minutes=interval_minutes,
                interval_hours=interval_hours,
                interval_days=interval_days,
                enabled=enabled,
                batch_size=batch_size,
                backoff_hours=backoff_hours
            )

    def configure(
        self,
        interval_minutes: Optional[int] = None,
        interval_hours: Optional[int] = None,
        interval_days: Optional[int] = None,
        enabled: Optional[bool] = None,
        batch_size: Optional[int] = None,
        backoff_hours: Optional[int] = None,
    ):
        """Allows dynamic reconfiguration of scheduler parameters."""
        if interval_minutes is not None:
            self.interval_minutes = interval_minutes
            self.interval_hours = interval_minutes // 60
            self.interval_days = max(1, interval_minutes // 1440)
        if interval_hours is not None:
            self.interval_hours = interval_hours
            self.interval_minutes = interval_hours * 60
            self.interval_days = max(1, interval_hours // 24)
        if interval_days is not None:
            self.interval_days = interval_days
            self.interval_hours = interval_days * 24
            self.interval_minutes = interval_days * 24 * 60
        if enabled is not None:
            self.enabled = enabled
        if batch_size is not None:
            self.batch_size = batch_size
        if backoff_hours is not None:
            self.backoff_hours = backoff_hours

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def is_executing_cycle(self) -> bool:
        return self._is_executing_cycle

    def start(self) -> bool:
        """
        Starts the background ingestion scheduler loop.
        Guarantees only a single worker runs; duplicate calls are safely ignored.
        """
        with self._lock:
            if self._is_running:
                logger.warning("AutoIngestionScheduler is already running; duplicate start ignored.")
                return False

            if not self.enabled and settings.SCHEME_INGESTION_ENABLED:
                self.enabled = True

            self._stop_event.clear()
            self._is_running = True
            now = datetime.utcnow()
            self._next_run_time = now + timedelta(minutes=self.interval_minutes)

            # Start background thread worker
            self._worker_thread = threading.Thread(
                target=self._worker_loop,
                name="AutoIngestionSchedulerWorker",
                daemon=True
            )
            self._worker_thread.start()
            logger.info(f"AutoIngestionScheduler started. Next scheduled run at {self._next_run_time.isoformat()}.")
            return True

    def stop(self, timeout: float = 5.0) -> bool:
        """
        Gracefully signals the background scheduler loop to stop and waits for completion.
        """
        with self._lock:
            if not self._is_running:
                return True

            logger.info("Signaling AutoIngestionScheduler to stop...")
            self._stop_event.set()
            self._is_running = False
            self._next_run_time = None

            if self._worker_thread and self._worker_thread.is_alive():
                self._worker_thread.join(timeout=timeout)
                self._worker_thread = None

            logger.info("AutoIngestionScheduler stopped cleanly.")
            return True

    def _worker_loop(self):
        """Internal background loop running at configured intervals."""
        logger.info("AutoIngestionScheduler background worker loop entered.")
        while not self._stop_event.is_set():
            try:
                # Wait for next run interval or stop signal
                # Wait in small 1-second slices so shutdown is instant
                wait_seconds = max(1, self.interval_minutes * 60)
                for _ in range(wait_seconds):
                    if self._stop_event.is_set():
                        break
                    self._stop_event.wait(1.0)

                if self._stop_event.is_set():
                    break

                if self.enabled:
                    logger.info("AutoIngestionScheduler triggering scheduled ingestion cycle...")
                    self.execute_cycle()
                    self._next_run_time = datetime.utcnow() + timedelta(minutes=self.interval_minutes)
                else:
                    logger.debug("AutoIngestionScheduler is disabled; skipping scheduled cycle.")

            except Exception as loop_err:
                logger.error(f"Unexpected error in AutoIngestionScheduler loop: {loop_err}", exc_info=True)
                self._stop_event.wait(5.0)

        logger.info("AutoIngestionScheduler background worker loop exited.")

    def trigger_now(self, db: Optional[Session] = None, force_update: bool = False) -> Dict[str, Any]:
        """
        Triggers an immediate on-demand ingestion cycle.
        Respects concurrency lock: returns message if already executing a cycle.
        """
        if self._is_executing_cycle:
            return {
                "status": "ALREADY_RUNNING",
                "message": "An ingestion cycle is currently in progress. Please wait for completion.",
                "last_run_id": self._last_run_id,
            }

        return self.execute_cycle(db=db, force_update=force_update)

    def execute_cycle(self, db: Optional[Session] = None, force_update: bool = False) -> Dict[str, Any]:
        """
        Executes a complete scheme monitoring cycle across all active official sources:
        1. Queries active sources with failure isolation.
        2. Applies backoff logic for repeatedly failing sources.
        3. Fetches content, hashes, and detects changes.
        4. Creates snapshots ONLY when content has changed or baseline.
        5. Stages PendingSchemeUpdate proposals for admin review.
        6. Records run metrics in IngestionRun.
        """
        with self._lock:
            if self._is_executing_cycle:
                return {
                    "status": "ALREADY_RUNNING",
                    "message": "Ingestion cycle already in progress.",
                    "last_run_id": self._last_run_id
                }
            self._is_executing_cycle = True

        run_id = f"RUN-SCHED-{uuid.uuid4().hex[:10]}"
        self._last_run_id = run_id
        start_time = datetime.utcnow()
        self._last_run_time = start_time
        self._last_run_status = "RUNNING"

        should_close_db = False
        target_db = db
        if not target_db:
            target_db = SessionLocal()
            should_close_db = True

        metrics = {
            "records_seen": 0,
            "records_changed": 0,
            "records_unchanged": 0,
            "records_failed": 0,
            "records_staged": 0,
            "records_needing_review": 0,
            "sources_skipped_backoff": 0,
            "sources_checked": 0,
            "sources_succeeded": 0,
            "sources_failed": 0,
            "unchanged_sources": 0,
            "changed_sources": 0,
            "new_schemes_detected": 0,
            "modified_schemes_detected": 0,
            "deactivation_candidates": 0,
            "validation_failures": 0,
            "pending_admin_reviews": 0,
        }

        try:
            # 1. Create IngestionRun entry
            ingestion_run = IngestionRun(
                run_id=run_id,
                started_at=start_time,
                status="RUNNING",
                records_seen=0,
                records_changed=0,
                records_unchanged=0,
                records_failed=0,
                records_staged=0,
                records_promoted=0,
                records_needing_review=0,
                sources_checked=0,
                sources_succeeded=0,
                sources_failed=0,
                unchanged_sources=0,
                changed_sources=0,
                new_schemes_detected=0,
                modified_schemes_detected=0,
                deactivation_candidates=0,
                validation_failures=0,
                pending_admin_reviews=0,
            )
            target_db.add(ingestion_run)
            target_db.commit()

            # 2. Query active official sources
            active_sources: List[SchemeSource] = (
                target_db.query(SchemeSource)
                .filter(SchemeSource.is_active == True)
                .order_by(SchemeSource.last_fetched_at.asc().nullsfirst())
                .limit(self.batch_size)
                .all()
            )

            logger.info(f"AutoIngestionScheduler cycle '{run_id}' checking {len(active_sources)} active source(s)...")

            pipeline = DynamicIngestionPipeline(target_db)
            now = datetime.utcnow()

            for source in active_sources:
                if self._stop_event.is_set():
                    logger.info(f"Stop signal received; terminating cycle '{run_id}' early.")
                    break

                # Check retry backoff for degraded/failing sources
                if not force_update and source.consecutive_failures >= 5:
                    backoff_limit = timedelta(hours=self.backoff_hours)
                    if source.updated_at and (now - source.updated_at) < backoff_limit:
                        logger.info(
                            f"Skipping source '{source.source_id}' due to consecutive failures ({source.consecutive_failures}) "
                            f"within backoff window ({self.backoff_hours}h)."
                        )
                        metrics["sources_skipped_backoff"] += 1
                        continue

                metrics["records_seen"] += 1
                metrics["sources_checked"] += 1

                # Failure Isolation per source
                try:
                    result = pipeline.run_pipeline(
                        source_id=source.source_id,
                        force_update=force_update,
                        run_id=run_id
                    )

                    status = result.get("change_status")
                    classification = result.get("classification") or result.get("change_classification")
                    proposal_type = result.get("proposal_type")

                    if result.get("fetch_status") == "SUCCESS":
                        metrics["sources_succeeded"] += 1
                    else:
                        metrics["sources_failed"] += 1

                    if classification == "UNCHANGED":
                        metrics["unchanged_sources"] += 1
                    elif classification == "SOURCE_CHANGED_ONLY":
                        metrics["unchanged_sources"] += 1
                    else:
                        metrics["changed_sources"] += 1

                    if proposal_type == "NEW_SCHEME":
                        metrics["new_schemes_detected"] += 1
                    elif proposal_type == "DEACTIVATION":
                        metrics["deactivation_candidates"] += 1
                    elif proposal_type == "MODIFICATION":
                        metrics["modified_schemes_detected"] += 1

                    if result.get("validation_status") in ("INVALID", "REJECTED"):
                        metrics["validation_failures"] += 1

                    if result.get("pending_update_id"):
                        metrics["records_staged"] += 1
                        metrics["pending_admin_reviews"] += 1

                    if status in ("CHANGE_DETECTED", "POSSIBLY_WITHDRAWN", "NEW_SCHEME"):
                        metrics["records_changed"] += 1
                        if result.get("governance_category") == "NEEDS_REVIEW":
                            metrics["records_needing_review"] += 1
                    elif status == "ERROR" or result.get("fetch_status") == "FAILED":
                        metrics["records_failed"] += 1
                    else:
                        metrics["records_unchanged"] += 1

                except Exception as src_err:
                    logger.error(f"Failure isolation: unexpected error on source '{source.source_id}': {src_err}")
                    metrics["records_failed"] += 1
                    metrics["sources_failed"] += 1
                    SourceHealthMonitor.record_event(
                        db=target_db,
                        source_id=source.source_id,
                        status="FAILED",
                        error_category="UNAVAILABLE_SOURCE",
                        error_message=str(src_err),
                        run_id=run_id
                    )

            # Update IngestionRun record
            completed_time = datetime.utcnow()
            ingestion_run.completed_at = completed_time
            ingestion_run.status = "COMPLETED"
            ingestion_run.records_seen = metrics["records_seen"]
            ingestion_run.records_changed = metrics["records_changed"]
            ingestion_run.records_unchanged = metrics["records_unchanged"]
            ingestion_run.records_failed = metrics["records_failed"]
            ingestion_run.records_staged = metrics["records_staged"]
            ingestion_run.records_needing_review = metrics["records_needing_review"]
            ingestion_run.sources_checked = metrics["sources_checked"]
            ingestion_run.sources_succeeded = metrics["sources_succeeded"]
            ingestion_run.sources_failed = metrics["sources_failed"]
            ingestion_run.unchanged_sources = metrics["unchanged_sources"]
            ingestion_run.changed_sources = metrics["changed_sources"]
            ingestion_run.new_schemes_detected = metrics["new_schemes_detected"]
            ingestion_run.modified_schemes_detected = metrics["modified_schemes_detected"]
            ingestion_run.deactivation_candidates = metrics["deactivation_candidates"]
            ingestion_run.validation_failures = metrics["validation_failures"]
            ingestion_run.pending_admin_reviews = metrics["pending_admin_reviews"]
            target_db.commit()

            self._last_run_status = "SUCCESS"
            self._last_metrics = metrics
            logger.info(
                f"AutoIngestionScheduler cycle '{run_id}' completed successfully in "
                f"{(completed_time - start_time).total_seconds():.2f}s: seen={metrics['records_seen']}, "
                f"changed={metrics['records_changed']}, staged={metrics['records_staged']}, "
                f"unchanged={metrics['records_unchanged']}, failed={metrics['records_failed']}"
            )

            return {
                "run_id": run_id,
                "status": "COMPLETED",
                "started_at": start_time.isoformat(),
                "completed_at": completed_time.isoformat(),
                "metrics": metrics
            }

        except Exception as cycle_err:
            logger.error(f"Fatal error during ingestion cycle '{run_id}': {cycle_err}", exc_info=True)
            self._last_run_status = "FAILED"
            try:
                if 'ingestion_run' in locals():
                    ingestion_run.status = "FAILED"
                    ingestion_run.completed_at = datetime.utcnow()
                    target_db.commit()
            except Exception:
                pass
            return {
                "run_id": run_id,
                "status": "FAILED",
                "error": str(cycle_err),
                "metrics": metrics
            }

        finally:
            self._is_executing_cycle = False
            if should_close_db:
                target_db.close()

    def get_status(self, db: Optional[Session] = None) -> Dict[str, Any]:
        """
        Returns comprehensive machine-readable telemetry for administrative dashboards.
        """
        should_close = False
        target_db = db
        if not target_db:
            target_db = SessionLocal()
            should_close = True

        try:
            # Query recent pending updates count
            pending_count = target_db.query(PendingSchemeUpdate).filter(
                PendingSchemeUpdate.status == "PENDING"
            ).count()

            # Query source counts and health breakdown
            total_sources = target_db.query(SchemeSource).count()
            active_sources = target_db.query(SchemeSource).filter(SchemeSource.is_active == True).count()
            healthy_sources = target_db.query(SchemeSource).filter(SchemeSource.health_status == "HEALTHY").count()
            degraded_sources = target_db.query(SchemeSource).filter(SchemeSource.health_status == "DEGRADED").count()
            failed_sources = target_db.query(SchemeSource).filter(SchemeSource.health_status == "FAILED").count()

            # Query last completed ingestion run from DB
            last_db_run = (
                target_db.query(IngestionRun)
                .order_by(IngestionRun.started_at.desc())
                .first()
            )

            last_run_dict = None
            if last_db_run:
                last_run_dict = {
                    "run_id": last_db_run.run_id,
                    "started_at": last_db_run.started_at.isoformat() if last_db_run.started_at else None,
                    "completed_at": last_db_run.completed_at.isoformat() if last_db_run.completed_at else None,
                    "status": last_db_run.status,
                    "records_seen": last_db_run.records_seen,
                    "records_changed": last_db_run.records_changed,
                    "records_unchanged": last_db_run.records_unchanged,
                    "records_failed": last_db_run.records_failed,
                    "records_staged": last_db_run.records_staged,
                    "records_needing_review": last_db_run.records_needing_review,
                    "sources_checked": last_db_run.sources_checked,
                    "sources_succeeded": last_db_run.sources_succeeded,
                    "sources_failed": last_db_run.sources_failed,
                    "unchanged_sources": last_db_run.unchanged_sources,
                    "changed_sources": last_db_run.changed_sources,
                    "new_schemes_detected": last_db_run.new_schemes_detected,
                    "modified_schemes_detected": last_db_run.modified_schemes_detected,
                    "deactivation_candidates": last_db_run.deactivation_candidates,
                    "validation_failures": last_db_run.validation_failures,
                    "pending_admin_reviews": last_db_run.pending_admin_reviews,
                }

            # Query last successful run timestamp
            last_successful_run = (
                target_db.query(IngestionRun)
                .filter(IngestionRun.status == "COMPLETED")
                .order_by(IngestionRun.completed_at.desc())
                .first()
            )

            return {
                "scheduler_enabled": self.enabled,
                "is_running": self._is_running,
                "is_executing_cycle": self._is_executing_cycle,
                "cadence": "24 hours",
                "interval_hours": getattr(self, "interval_hours", 24),
                "interval_days": getattr(self, "interval_days", 1),
                "interval_minutes": self.interval_minutes,
                "last_run_id": self._last_run_id,
                "last_run_status": self._last_run_status,
                "last_run_time": self._last_run_time.isoformat() if self._last_run_time else None,
                "next_scheduled_run": self._next_run_time.isoformat() if self._next_run_time else None,
                "last_successful_run_at": (
                    last_successful_run.completed_at.isoformat() if last_successful_run and last_successful_run.completed_at else None
                ),
                "last_run": last_run_dict,
                "pending_updates_count": pending_count,
                "sources_summary": {
                    "total_sources": total_sources,
                    "active_sources": active_sources,
                    "healthy_sources": healthy_sources,
                    "degraded_sources": degraded_sources,
                    "failed_sources": failed_sources,
                },
                "last_cycle_metrics": self._last_metrics,
            }

        finally:
            if should_close:
                target_db.close()


# Global singleton instance
auto_scheduler = AutoIngestionScheduler()
