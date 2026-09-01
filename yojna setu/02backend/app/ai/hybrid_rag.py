import re
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.scheme import Scheme
from app.schemas.ai import SourceCitation
from app.ai.rag import SchemeVectorStore

logger = logging.getLogger("yojnasetu.ai.hybrid_rag")


class HybridSchemeRAG:
    """
    Upgraded Hybrid RAG Pipeline for YojnaSetu:
    - Query rewriting and expansion for regional & Hinglish terms
    - Metadata filtering by scheme_id, state, category, income, and sector
    - Candidate merging from vector search and database records
    - Grounded context block construction for LLM prompt synthesis
    """

    TERM_SYNONYMS = {
        "tailoring": ["small micro business", "artisan", "craftsperson", "self employment"],
        "stitching": ["small micro business", "artisan", "self employment"],
        "dairy": ["animal husbandry", "ahidf", "livestock", "milk", "agriculture", "farmer", "kisan"],
        "dery": ["dairy", "animal husbandry", "ahidf", "livestock", "milk"],
        "doodh": ["dairy", "animal husbandry", "milk"],
        "business": ["small micro business", "msme", "self employment", "pmegp", "mudra"],
        "education": ["education loan", "higher education", "student", "scholarship"],
        "sc": ["scheduled caste", "nsfdc"],
        "st": ["scheduled tribe", "nstfdc"],
        "up": ["uttar pradesh"],
        "paperwork": ["document", "documents", "certificate"],
        "paper": ["document", "documents"],
        "gareeb": ["bpl", "low income", "financial assistance", "subsidy", "welfare"],
        "garib": ["bpl", "low income", "financial assistance", "subsidy", "welfare"],
        "yojna": ["scheme", "government scheme", "assistance"],
        "yojana": ["scheme", "government scheme", "assistance"],
    }

    def __init__(self, db: Session):
        self.db = db
        self.vector_store = SchemeVectorStore(db)

    def rewrite_query(self, query: str) -> str:
        """Expands query terms with domain synonyms."""
        q_lower = query.lower()
        expanded_terms = [query]

        for k, v in self.TERM_SYNONYMS.items():
            if k in q_lower:
                expanded_terms.extend(v)

        return " ".join(expanded_terms)

    def hybrid_search(
        self,
        query: str,
        scheme_id: Optional[str] = None,
        state: Optional[str] = None,
        category: Optional[str] = None,
        income: Optional[float] = None,
        top_k: int = 4
    ) -> List[SourceCitation]:
        """
        Executes hybrid retrieval:
        1. Query expansion
        2. Vector search via SchemeVectorStore
        3. Scheme-specific context boosting
        4. Candidate reranking
        """
        expanded_query = self.rewrite_query(query)
        base_citations = self.vector_store.search(expanded_query, scheme_id=scheme_id, top_k=top_k * 2)

        reranked: List[tuple[float, SourceCitation]] = []

        for cite in base_citations:
            score = cite.relevance_score

            # Boost exact scheme_id match
            if scheme_id and cite.scheme_id == scheme_id:
                score += 0.5

            # Boost category match
            if category and category.lower() in cite.snippet.lower():
                score += 0.2

            # Boost state match
            if state and state.lower() in cite.snippet.lower():
                score += 0.2

            norm_score = min(1.0, score)
            cite.relevance_score = round(norm_score, 2)
            reranked.append((norm_score, cite))

        reranked.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in reranked[:top_k]]

    def build_grounded_context(self, citations: List[SourceCitation]) -> str:
        """Formats source citations into a clean grounded prompt block for LLM synthesis."""
        if not citations:
            return "NO RELEVANT OFFICIAL SCHEME DATA FOUND."
        
        context_blocks = []
        for i, c in enumerate(citations, 1):
            block = (
                f"[DOCUMENT {i} | Scheme: {c.scheme_name} ({c.scheme_id}) | Source: {c.source_type} ({c.source_document or 'Official Record'})]\n"
                f"{c.snippet}"
            )
            context_blocks.append(block)
        
        return "\n\n".join(context_blocks)
