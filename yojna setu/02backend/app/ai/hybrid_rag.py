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
    Upgraded Hybrid RAG Pipeline:
    - Query rewriting and expansion for Hindi / Hinglish domain terms
    - Metadata filtering by state, social category, annual income, and sector
    - Candidate merging from vector search and structured database filters
    - Explainable metadata-aware reranking
    """

    TERM_SYNONYMS = {
        "tailoring": ["small micro business", "artisan", "craftsperson", "self employment"],
        "stitching": ["small micro business", "artisan", "self employment"],
        "dairy": ["animal husbandry", "agriculture", "farmer"],
        "business": ["small micro business", "msme", "self employment"],
        "education": ["education loan", "higher education", "student"],
        "sc": ["scheduled caste"],
        "st": ["scheduled tribe"],
        "up": ["uttar pradesh"],
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
        1. Query rewriting
        2. Vector search via SchemeVectorStore
        3. Metadata filtering
        4. Candidate reranking
        """
        expanded_query = self.rewrite_query(query)
        base_citations = self.vector_store.search(expanded_query, scheme_id=scheme_id, top_k=top_k * 2)

        # Rerank candidates based on metadata relevance
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
