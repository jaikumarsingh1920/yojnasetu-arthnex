import uuid
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app.models.ingestion import SchemeSource, SourceHealthLog

logger = logging.getLogger("yojnasetu.ingestion.health")


class SourceHealthMonitor:
    """
    Continuous Source Health Monitoring Service.
    Tracks HTTP failures, timeouts, redirects/changed URLs, host unreachability,
    parser failures, and malformed documents per official government source.
    """

    ERROR_CATEGORIES = {
        "HTTP_ERROR": "HTTP 4xx/5xx response from server",
        "TIMEOUT": "Connection or read timeout waiting for response",
        "CHANGED_URL": "Permanent redirect or changed endpoint URL",
        "UNAVAILABLE_SOURCE": "DNS resolution failure or host connection refused",
        "PARSING_FAILURE": "HTML/JSON extractor unable to parse structured scheme fields",
        "MALFORMED_DOCUMENT": "Binary content lacks expected format headers (e.g. invalid PDF header)",
    }

    @classmethod
    def record_event(
        cls,
        db: Session,
        source_id: str,
        status: str,
        error_category: Optional[str] = None,
        http_status_code: Optional[int] = None,
        latency_ms: int = 0,
        error_message: Optional[str] = None,
        run_id: Optional[str] = None
    ) -> SourceHealthLog:
        """Records an immutable health log entry and updates the source's operational status."""
        source = db.query(SchemeSource).filter(SchemeSource.source_id == source_id).first()
        log_id = f"HLOG-{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow()

        log_entry = SourceHealthLog(
            log_id=log_id,
            source_id=source_id,
            run_id=run_id,
            status=status.upper(),
            error_category=error_category.upper() if error_category else None,
            http_status_code=http_status_code,
            latency_ms=latency_ms,
            error_message=error_message,
            recorded_at=now
        )
        db.add(log_entry)

        if source:
            if status.upper() == "HEALTHY":
                source.consecutive_failures = 0
                source.health_status = "HEALTHY"
                source.last_status = "SUCCESS"
            else:
                source.consecutive_failures = getattr(source, "consecutive_failures", 0) + 1
                source.last_status = "FAILED"
                if source.consecutive_failures >= 5:
                    source.health_status = "FAILED"
                elif source.consecutive_failures >= 2:
                    source.health_status = "DEGRADED"
            source.updated_at = now

        db.commit()
        return log_entry

    @classmethod
    def get_source_health_summary(cls, db: Session, source_id: str) -> Dict[str, Any]:
        """Calculates health metrics and failure breakdown for an external source."""
        source = db.query(SchemeSource).filter(SchemeSource.source_id == source_id).first()
        if not source:
            return {"error": f"Source '{source_id}' not found."}

        logs = db.query(SourceHealthLog).filter(
            SourceHealthLog.source_id == source_id
        ).order_by(SourceHealthLog.recorded_at.desc()).limit(50).all()

        total = len(logs)
        failures = [l for l in logs if l.status != "HEALTHY"]
        uptime = ((total - len(failures)) / total * 100.0) if total > 0 else 100.0

        breakdown: Dict[str, int] = {}
        for f in failures:
            cat = f.error_category or "UNKNOWN"
            breakdown[cat] = breakdown.get(cat, 0) + 1

        return {
            "source_id": source_id,
            "source_name": source.source_name,
            "health_status": getattr(source, "health_status", "HEALTHY"),
            "consecutive_failures": getattr(source, "consecutive_failures", 0),
            "recent_events_count": total,
            "recent_uptime_pct": round(uptime, 1),
            "failure_breakdown": breakdown,
            "last_error": failures[0].error_message if failures else None
        }
