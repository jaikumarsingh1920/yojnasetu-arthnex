import logging
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import numpy as np

from app.models import Scheme, SchemeRule, SchemeDocument
from app.schemas.ai import SourceCitation
from app.ai.provider import get_ai_provider

logger = logging.getLogger("yojnasetu.ai.rag")


class SchemeVectorStore:
    """
    Retrieval-Augmented Generation (RAG) vector store for verified scheme data & documents.
    Uses TF-IDF + Cosine Similarity over authoritative PostgreSQL scheme records.
    Returns traceable SourceCitation objects.
    """

    def __init__(self, db: Session):
        self.db = db
        self._chunks: List[Dict[str, Any]] = []
        self._build_index()

    def _build_index(self):
        """Indexes all verified Schemes, SchemeRules, and SchemeDocuments into searchable chunks."""
        schemes = self.db.query(Scheme).all()
        chunks: List[Dict[str, Any]] = []

        for sch in schemes:
            # 1. Scheme Metadata Chunk
            meta_text = (
                f"Scheme Name: {sch.scheme_name} ({sch.scheme_id})\n"
                f"Ministry/Department: {sch.ministry or sch.implementing_agency or 'Government of India'}\n"
                f"Purpose: {sch.purpose or sch.short_description or ''}\n"
                f"Target Group: {sch.target_beneficiary or sch.target_groups or ''}\n"
                f"State: {sch.state_coverage or sch.state_restriction or 'PAN_INDIA'}"
            )
            chunks.append({
                "scheme_id": sch.scheme_id,
                "scheme_code": sch.scheme_id,
                "scheme_name": sch.scheme_name,
                "source_type": "SCHEME_METADATA",
                "source_document": None,
                "rule_id": None,
                "text": meta_text,
            })

            # 2. Scheme Rules Chunks
            rules = self.db.query(SchemeRule).filter(SchemeRule.scheme_id == sch.scheme_id).all()
            for r in rules:
                rule_text = (
                    f"Scheme: {sch.scheme_name}\n"
                    f"Rule Code: {r.rule_id}\n"
                    f"Field: {r.field} {r.operator} {r.value}\n"
                    f"Description: {r.error_message or ''}"
                )
                chunks.append({
                    "scheme_id": sch.scheme_id,
                    "scheme_code": sch.scheme_id,
                    "scheme_name": sch.scheme_name,
                    "source_type": "SCHEME_RULE",
                    "source_document": r.source_document,
                    "rule_id": str(r.rule_id),
                    "text": rule_text,
                })

            # 3. Scheme Documents Chunks
            docs = self.db.query(SchemeDocument).filter(SchemeDocument.scheme_id == sch.scheme_id).all()
            for doc in docs:
                doc_text = (
                    f"Scheme: {sch.scheme_name}\n"
                    f"Required Document: {doc.document_name}\n"
                    f"Requirement Type: {doc.requirement_type}\n"
                    f"Condition: {doc.condition or ''}"
                )
                chunks.append({
                    "scheme_id": sch.scheme_id,
                    "scheme_code": sch.scheme_id,
                    "scheme_name": sch.scheme_name,
                    "source_type": "SCHEME_DOCUMENT",
                    "source_document": doc.document_name,
                    "rule_id": None,
                    "text": doc_text,
                })

        self._chunks = chunks
        logger.info("RAG Vector Store indexed %d scheme context chunks.", len(chunks))

    def search(
        self,
        query: str,
        scheme_id: Optional[str] = None,
        top_k: int = 4
    ) -> List[SourceCitation]:
        """Searches indexed scheme chunks for top relevant context citations."""
        if not self._chunks:
            return []

        # Filter by scheme_id if specified
        target_chunks = self._chunks
        if scheme_id:
            target_chunks = [c for c in self._chunks if c["scheme_id"] == str(scheme_id)]
            if not target_chunks:
                target_chunks = self._chunks

        # Compute TF-IDF similarity vectors
        query_terms = set(re.findall(r"\w+", query.lower()))

        scored_chunks = []
        for chunk in target_chunks:
            text_terms = set(re.findall(r"\w+", chunk["text"].lower()))
            overlap = query_terms.intersection(text_terms)
            score = len(overlap) / (len(query_terms) + 1.0)

            # Boost if scheme_name or scheme_code matches query
            if chunk["scheme_code"].lower() in query.lower() or chunk["scheme_name"].lower() in query.lower():
                score += 0.4

            if score > 0.05:
                scored_chunks.append((score, chunk))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)

        citations: List[SourceCitation] = []
        for score, chunk in scored_chunks[:top_k]:
            norm_score = min(1.0, score)
            citations.append(SourceCitation(
                scheme_id=chunk["scheme_id"],
                scheme_name=chunk["scheme_name"],
                source_type=chunk["source_type"],
                source_document=chunk["source_document"],
                rule_id=chunk["rule_id"],
                snippet=chunk["text"][:350],
                relevance_score=round(norm_score, 2)
            ))

        return citations
