"""
Dynamic Scheme Ingestion Pipeline Package.
Orchestrates:
Official Gov Source -> Fetcher -> Snapshot -> Change Detection -> Extraction ->
Normalization -> Validation -> Pending Update Proposal -> Admin Approval ->
Canonical Scheme DB Update -> Eligibility Rules & RAG Sync.
"""

from app.services.ingestion.fetcher import BaseFetcher, FetchResult, HTMLFetcher
from app.services.ingestion.change_detector import DeterministicChangeDetector
from app.services.ingestion.extractor import OfficialGovHTMLExtractor
from app.services.ingestion.normalizer import SchemeDataNormalizer
from app.services.ingestion.validator import SchemeDataValidator
from app.services.ingestion.sync_service import IngestionSyncService
from app.services.ingestion.approval_service import PendingUpdateApprovalService
from app.services.ingestion.pipeline import DynamicIngestionPipeline

__all__ = [
    "BaseFetcher",
    "FetchResult",
    "HTMLFetcher",
    "DeterministicChangeDetector",
    "OfficialGovHTMLExtractor",
    "SchemeDataNormalizer",
    "SchemeDataValidator",
    "IngestionSyncService",
    "PendingUpdateApprovalService",
    "DynamicIngestionPipeline",
]
