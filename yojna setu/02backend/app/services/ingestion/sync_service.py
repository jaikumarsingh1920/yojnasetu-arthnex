import logging
from typing import Dict, Any, List, Optional, Union
from sqlalchemy.orm import Session
from app.models.scheme import Scheme
from app.models.rule import SchemeRule
from app.ai.rag import SchemeVectorStore

logger = logging.getLogger("yojnasetu.ingestion.sync")


class IngestionSyncService:
    """
    Synchronization Service executed upon approval of a dynamic scheme update.
    Maintains synchronization between Canonical Scheme DB and:
    1. Statutory SchemeRule condition entries (Eligibility Engine)
    2. SchemeVectorStore context chunks (RAG Knowledge Engine)
    Supports both instance and classmethod invocation patterns.
    """

    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def sync(self, scheme_id: str, updated_fields: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.db:
            raise ValueError("Database session is required.")
        scheme = self.db.query(Scheme).filter(Scheme.scheme_id == scheme_id).first()
        if not scheme:
            raise ValueError(f"Scheme '{scheme_id}' not found.")
        return self.sync_after_approval(self.db, scheme, updated_fields or {})

    @classmethod
    def sync_eligibility_rules(
        cls,
        db: Session,
        scheme: Scheme,
        candidate_data: Dict[str, Any]
    ) -> List[str]:
        """
        Synchronizes condition rules in scheme_rules when master scheme eligibility
        parameters (age_min, age_max, income_limit) are updated.
        """
        synced_notes: List[str] = []

        # 1. Sync minimum age rule
        if scheme.age_min is not None:
            age_min_rule = db.query(SchemeRule).filter(
                SchemeRule.scheme_id == scheme.scheme_id,
                SchemeRule.field == "age",
                SchemeRule.operator.in_([">=", ">"])
            ).first()
            if age_min_rule and str(age_min_rule.value) != str(scheme.age_min):
                old_v = age_min_rule.value
                age_min_rule.value = str(scheme.age_min)
                age_min_rule.error_message = f"Applicant must be at least {scheme.age_min} years of age."
                synced_notes.append(f"Synced rule '{age_min_rule.rule_id}' (age min: {old_v} -> {scheme.age_min})")

        # 2. Sync maximum age rule
        if scheme.age_max is not None:
            age_max_rule = db.query(SchemeRule).filter(
                SchemeRule.scheme_id == scheme.scheme_id,
                SchemeRule.field == "age",
                SchemeRule.operator.in_(["<=", "<"])
            ).first()
            if age_max_rule and str(age_max_rule.value) != str(scheme.age_max):
                old_v = age_max_rule.value
                age_max_rule.value = str(scheme.age_max)
                age_max_rule.error_message = f"Applicant age cannot exceed {scheme.age_max} years."
                synced_notes.append(f"Synced rule '{age_max_rule.rule_id}' (age max: {old_v} -> {scheme.age_max})")

        # 3. Sync income limit rule
        if scheme.income_limit is not None:
            income_rule = db.query(SchemeRule).filter(
                SchemeRule.scheme_id == scheme.scheme_id,
                SchemeRule.field.in_(["annual_income", "income_limit", "income"])
            ).first()
            if income_rule and str(income_rule.value) != str(scheme.income_limit):
                old_v = income_rule.value
                income_rule.value = str(scheme.income_limit)
                income_rule.error_message = f"Annual family income must not exceed ₹{scheme.income_limit:,.2f}."
                synced_notes.append(f"Synced rule '{income_rule.rule_id}' (income: {old_v} -> {scheme.income_limit})")

        logger.info(f"Synchronized {len(synced_notes)} eligibility rules for scheme {scheme.scheme_id}")
        return synced_notes

    @classmethod
    def sync_rag_knowledge(cls, db: Session, scheme: Scheme) -> bool:
        """
        Triggers incremental update of RAG knowledge chunks for the updated scheme.
        Ensures AI Copilot reflects newly approved data without rebuilding the entire index.
        """
        try:
            rag_store = SchemeVectorStore(db)
            if hasattr(rag_store, "update_scheme_chunks"):
                synced_cnt = rag_store.update_scheme_chunks(scheme)
                logger.info(f"RAG SchemeVectorStore incrementally updated {synced_cnt} context chunks for scheme {scheme.scheme_id}.")
            else:
                reindexed_cnt = rag_store.reindex(db)
                logger.info(f"RAG SchemeVectorStore re-indexed {reindexed_cnt} context chunks after scheme {scheme.scheme_id} update.")
            return True
        except Exception as e:
            logger.error(f"Failed to incrementally sync RAG vector store for scheme {scheme.scheme_id}: {e}")
            return False


    @classmethod
    def sync_after_approval(
        cls,
        db_or_self: Union[Session, "IngestionSyncService", Any],
        scheme_or_id: Union[Scheme, str] = None,
        candidate_data: Optional[Dict[str, Any]] = None,
        updated_fields: Optional[Dict[str, Any]] = None,
        scheme_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Unified post-approval synchronization hook.
        Handles both:
        - IngestionSyncService(db).sync_after_approval(scheme_id="...", updated_fields={...})
        - IngestionSyncService.sync_after_approval(db, scheme, candidate_data)
        """
        if isinstance(db_or_self, IngestionSyncService):
            db = db_or_self.db
        elif isinstance(db_or_self, Session):
            db = db_or_self
        else:
            db = getattr(db_or_self, "db", None)

        if not db:
            raise ValueError("Database session is required.")

        target_sid = scheme_id or (scheme_or_id if isinstance(scheme_or_id, str) else None)
        if isinstance(scheme_or_id, Scheme):
            scheme = scheme_or_id
        elif target_sid:
            scheme = db.query(Scheme).filter(Scheme.scheme_id == target_sid).first()
            if not scheme:
                raise ValueError(f"Scheme '{target_sid}' not found.")
        else:
            raise ValueError("Scheme or scheme_id must be provided.")

        data = candidate_data or updated_fields or {}

        rules_synced = cls.sync_eligibility_rules(db, scheme, data)
        rag_synced = cls.sync_rag_knowledge(db, scheme)

        return {
            "scheme_id": scheme.scheme_id,
            "rules_synced": rules_synced,
            "rag_synced": rag_synced
        }
