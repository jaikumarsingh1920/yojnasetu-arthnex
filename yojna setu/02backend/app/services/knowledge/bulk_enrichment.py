"""
Repeatable, Batched Scheme Knowledge Bulk Enrichment Runner for YojnaSetu.
SIH26092 Smart Automation.

Features:
- Batched processing (configurable batch size)
- State persistence & restartability via checkpoint file
- Strict idempotency (updates existing knowledge profiles and FAQs in-place)
- Preserves existing good data (SchemeRules, detailed_descriptions, documents)
- Error isolation per scheme (prevents single-scheme failure from halting batch)
- Incremental RAG synchronization
- Comprehensive statistics and audit reporting
"""

import os
import sys

_backend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _backend_root not in sys.path:
    sys.path.insert(0, _backend_root)

import json
import logging
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import SessionLocal
from app.models.scheme import Scheme
from app.models.document import SchemeDocument
from app.models.knowledge import SchemeFAQ, SchemeKnowledgeProfile
from app.services.knowledge.enrichment_service import SchemeKnowledgeEnrichmentService

logger = logging.getLogger("yojnasetu.knowledge.bulk_enrichment")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

CHECKPOINT_DEFAULT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "scratch",
    "bulk_enrichment_checkpoint.json"
)


class SchemeBulkEnrichmentRunner:
    """
    Batched, idempotent, restartable bulk enrichment runner for the YojnaSetu scheme corpus.
    """

    def __init__(
        self,
        db: Optional[Session] = None,
        checkpoint_path: Optional[str] = None,
        batch_size: int = 50
    ):
        self._external_db = db is not None
        self.db = db or SessionLocal()
        self.checkpoint_path = checkpoint_path or CHECKPOINT_DEFAULT_PATH
        self.batch_size = batch_size
        self._ensure_checkpoint_dir()

    def _ensure_checkpoint_dir(self):
        cdir = os.path.dirname(self.checkpoint_path)
        if cdir and not os.path.exists(cdir):
            os.makedirs(cdir, exist_ok=True)

    def load_checkpoint(self) -> Dict[str, Any]:
        """Loads existing checkpoint from file or returns clean state."""
        if os.path.exists(self.checkpoint_path):
            try:
                with open(self.checkpoint_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return {
                        "completed_ids": set(data.get("completed_ids", [])),
                        "failed_ids": data.get("failed_ids", {}),
                        "total_processed": data.get("total_processed", 0),
                        "started_at": data.get("started_at"),
                        "last_updated": data.get("last_updated"),
                        "last_processed_id": data.get("last_processed_id")
                    }
            except Exception as e:
                logger.warning("Could not read checkpoint from %s: %s. Starting fresh.", self.checkpoint_path, e)
        
        return {
            "completed_ids": set(),
            "failed_ids": {},
            "total_processed": 0,
            "started_at": datetime.utcnow().isoformat(),
            "last_updated": datetime.utcnow().isoformat(),
            "last_processed_id": None
        }

    def save_checkpoint(self, checkpoint: Dict[str, Any]):
        """Persists checkpoint state atomically."""
        try:
            temp_path = f"{self.checkpoint_path}.tmp"
            payload = {
                "completed_ids": sorted(list(checkpoint["completed_ids"])),
                "failed_ids": checkpoint["failed_ids"],
                "total_processed": len(checkpoint["completed_ids"]),
                "started_at": checkpoint.get("started_at"),
                "last_updated": datetime.utcnow().isoformat(),
                "last_processed_id": checkpoint.get("last_processed_id")
            }
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            if os.path.exists(self.checkpoint_path):
                os.replace(temp_path, self.checkpoint_path)
            else:
                os.rename(temp_path, self.checkpoint_path)
        except Exception as e:
            logger.error("Failed to persist checkpoint: %s", e)

    def reset_checkpoint(self):
        """Removes the checkpoint file to permit a full clean run."""
        if os.path.exists(self.checkpoint_path):
            try:
                os.remove(self.checkpoint_path)
                logger.info("Reset checkpoint file at %s", self.checkpoint_path)
            except Exception as e:
                logger.error("Error resetting checkpoint: %s", e)

    def run(
        self,
        limit: Optional[int] = None,
        force_reprocess: bool = False,
        sync_rag: bool = False,
        vector_store: Any = None
    ) -> Dict[str, Any]:
        """
        Executes bulk enrichment on the scheme corpus.
        Args:
            limit: Maximum number of schemes to process (for testing/incremental runs).
            force_reprocess: If True, ignores completed checkpoint entries and re-enriches all.
            sync_rag: If True, invokes RAG incremental update or reindexing.
            vector_store: Optional SchemeVectorStore instance to update incrementally.
        """
        checkpoint = self.load_checkpoint()
        if force_reprocess:
            checkpoint["completed_ids"] = set()
            checkpoint["failed_ids"] = {}

        query = self.db.query(Scheme).order_by(Scheme.scheme_id.asc())
        all_schemes: List[Scheme] = query.all()
        total_in_db = len(all_schemes)

        target_schemes = [
            s for s in all_schemes
            if force_reprocess or s.scheme_id not in checkpoint["completed_ids"]
        ]

        if limit is not None:
            target_schemes = target_schemes[:limit]

        logger.info(
            "Starting Bulk Knowledge Enrichment. Total schemes in DB: %d | Already completed: %d | Targets to process: %d",
            total_in_db, len(checkpoint["completed_ids"]), len(target_schemes)
        )

        batch_counter = 0
        enriched_this_run = 0
        failed_this_run = 0

        for i in range(0, len(target_schemes), self.batch_size):
            batch = target_schemes[i:i + self.batch_size]
            batch_counter += 1
            logger.info("Processing Batch %d/%d (%d schemes)...", batch_counter, (len(target_schemes) + self.batch_size - 1) // self.batch_size, len(batch))

            for sch in batch:
                try:
                    res = SchemeKnowledgeEnrichmentService.enrich_scheme(self.db, sch, commit=False)
                    checkpoint["completed_ids"].add(sch.scheme_id)
                    checkpoint["failed_ids"].pop(sch.scheme_id, None)
                    checkpoint["last_processed_id"] = sch.scheme_id
                    enriched_this_run += 1

                    # Incremental RAG synchronization if vector store provided
                    if vector_store:
                        try:
                            vector_store.update_scheme_chunks(sch)
                        except Exception as ve:
                            logger.warning("RAG incremental update warning for %s: %s", sch.scheme_id, ve)

                except Exception as ex:
                    logger.error("Error enriching scheme %s: %s", sch.scheme_id, ex, exc_info=True)
                    checkpoint["failed_ids"][sch.scheme_id] = str(ex)
                    failed_this_run += 1

            # Commit batch to database
            try:
                self.db.commit()
                self.save_checkpoint(checkpoint)
                logger.info(
                    "Batch %d committed successfully. Total completed so far: %d (Enriched this run: %d, Failed: %d)",
                    batch_counter, len(checkpoint["completed_ids"]), enriched_this_run, failed_this_run
                )
            except Exception as ce:
                self.db.rollback()
                logger.error("Failed to commit batch %d: %s", batch_counter, ce)

        # Full RAG reindex if requested and no vector store was provided
        rag_chunks_count = None
        if sync_rag:
            try:
                from app.ai.rag import SchemeVectorStore
                vs = vector_store or SchemeVectorStore(self.db)
                rag_chunks_count = vs.reindex(self.db)
                logger.info("RAG Vector Store synchronized. Total chunks: %d", rag_chunks_count)
            except Exception as re:
                logger.error("Failed to synchronize RAG index: %s", re)

        # Compute comprehensive statistics
        summary = self.generate_summary_report(checkpoint, rag_chunks_count=rag_chunks_count)
        return summary

    def generate_summary_report(
        self,
        checkpoint: Optional[Dict[str, Any]] = None,
        rag_chunks_count: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generates a deep statistical report of the knowledge base."""
        if checkpoint is None:
            checkpoint = self.load_checkpoint()

        total_schemes = self.db.query(func.count(Scheme.scheme_id)).scalar() or 0
        total_faqs = self.db.query(func.count(SchemeFAQ.faq_id)).scalar() or 0
        total_docs = self.db.query(func.count(SchemeDocument.document_id)).scalar() or 0
        total_profiles = self.db.query(func.count(SchemeKnowledgeProfile.profile_id)).scalar() or 0

        # Quality score statistics
        quality_scores = [
            p.quality_score for p in self.db.query(SchemeKnowledgeProfile.quality_score).all()
            if p.quality_score is not None
        ]
        avg_quality = round(sum(quality_scores) / len(quality_scores), 2) if quality_scores else 0.0

        q_high = sum(1 for q in quality_scores if q >= 80.0)
        q_medium = sum(1 for q in quality_scores if 60.0 <= q < 80.0)
        q_low = sum(1 for q in quality_scores if q < 60.0)

        # Dimension presence counts
        schemes_with_faqs = self.db.query(func.count(func.distinct(SchemeFAQ.scheme_id))).scalar() or 0
        schemes_with_eligibility = self.db.query(func.count(SchemeKnowledgeProfile.profile_id)).filter(
            SchemeKnowledgeProfile.applicant_category_summary.isnot(None)
        ).scalar() or 0
        schemes_with_financial = self.db.query(func.count(SchemeKnowledgeProfile.profile_id)).filter(
            SchemeKnowledgeProfile.financial_summary.isnot(None)
        ).scalar() or 0
        schemes_with_application = self.db.query(func.count(SchemeKnowledgeProfile.profile_id)).filter(
            SchemeKnowledgeProfile.application_summary.isnot(None)
        ).scalar() or 0
        schemes_with_docs = self.db.query(func.count(func.distinct(SchemeDocument.scheme_id))).scalar() or 0

        return {
            "total_canonical_schemes": total_schemes,
            "completed_schemes": len(checkpoint["completed_ids"]),
            "failed_schemes": len(checkpoint["failed_ids"]),
            "total_knowledge_profiles": total_profiles,
            "total_faqs_stored": total_faqs,
            "total_documents_stored": total_docs,
            "schemes_with_faq_knowledge": schemes_with_faqs,
            "schemes_with_rich_eligibility": schemes_with_eligibility,
            "schemes_with_financial_metadata": schemes_with_financial,
            "schemes_with_application_info": schemes_with_application,
            "schemes_with_documents": schemes_with_docs,
            "average_quality_score": avg_quality,
            "quality_distribution": {
                "high_quality_80_plus": q_high,
                "medium_quality_60_to_79": q_medium,
                "needs_official_source_below_60": q_low
            },
            "rag_chunks_total": rag_chunks_count,
            "last_updated": checkpoint.get("last_updated")
        }

    def close(self):
        """Closes the DB session if owned."""
        if not self._external_db and self.db:
            self.db.close()


def main():
    parser = argparse.ArgumentParser(description="Bulk Scheme Knowledge Enrichment for YojnaSetu.")
    parser.add_argument("--batch-size", type=int, default=50, help="Batch size for DB transactions.")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of schemes to process.")
    parser.add_argument("--force", action="store_true", help="Force re-enrichment of all schemes.")
    parser.add_argument("--reset-checkpoint", action="store_true", help="Reset checkpoint file.")
    parser.add_argument("--sync-rag", action="store_true", default=True, help="Synchronize RAG vector store after enrichment.")
    parser.add_argument("--report-only", action="store_true", help="Only print statistics report without processing.")

    args = parser.parse_args()

    runner = SchemeBulkEnrichmentRunner(batch_size=args.batch_size)
    try:
        if args.reset_checkpoint:
            runner.reset_checkpoint()

        if args.report_only:
            summary = runner.generate_summary_report()
            print("\n=== YOJNASETU SCHEME KNOWLEDGE REPORT ===")
            print(json.dumps(summary, indent=2))
            return

        summary = runner.run(
            limit=args.limit,
            force_reprocess=args.force,
            sync_rag=args.sync_rag
        )

        print("\n=== BULK ENRICHMENT SUMMARY REPORT ===")
        print(json.dumps(summary, indent=2))

    finally:
        runner.close()


if __name__ == "__main__":
    main()
