import threading
import time
from typing import Dict, Any, Optional


class RAGObservabilityTracker:
    """
    Thread-safe in-memory operational metrics tracker for YojnaSetu AI & RAG systems.
    Captures operational health without recording any sensitive user PII or API tokens.
    """

    _lock = threading.Lock()
    _total_queries: int = 0
    _retrieval_success_count: int = 0
    _no_result_count: int = 0
    _total_chunks_retrieved: int = 0
    _gemini_success_count: int = 0
    _gemini_failure_count: int = 0
    _timeout_count: int = 0
    _fallback_count: int = 0
    _malformed_output_count: int = 0
    _citations_generated_count: int = 0
    _prompt_injection_blocked_count: int = 0
    _deterministic_engine_calls: int = 0
    _unauthorized_claims_intercepted: int = 0
    _start_time: float = time.time()

    @classmethod
    def record_query(cls, intent: str, deterministic_used: bool = False) -> None:
        with cls._lock:
            cls._total_queries += 1
            if deterministic_used:
                cls._deterministic_engine_calls += 1

    @classmethod
    def record_retrieval(cls, chunks_count: int) -> None:
        with cls._lock:
            if chunks_count > 0:
                cls._retrieval_success_count += 1
                cls._total_chunks_retrieved += chunks_count
            else:
                cls._no_result_count += 1

    @classmethod
    def record_citations(cls, citations_count: int) -> None:
        with cls._lock:
            cls._citations_generated_count += citations_count

    @classmethod
    def record_gemini_success(cls) -> None:
        with cls._lock:
            cls._gemini_success_count += 1

    @classmethod
    def record_gemini_failure(cls, is_timeout: bool = False) -> None:
        with cls._lock:
            cls._gemini_failure_count += 1
            if is_timeout:
                cls._timeout_count += 1

    @classmethod
    def record_fallback(cls) -> None:
        with cls._lock:
            cls._fallback_count += 1

    @classmethod
    def record_malformed_output(cls) -> None:
        with cls._lock:
            cls._malformed_output_count += 1

    @classmethod
    def record_prompt_injection_blocked(cls) -> None:
        with cls._lock:
            cls._prompt_injection_blocked_count += 1

    @classmethod
    def record_unauthorized_claim_intercepted(cls) -> None:
        with cls._lock:
            cls._unauthorized_claims_intercepted += 1

    @classmethod
    def get_metrics_summary(cls) -> Dict[str, Any]:
        """Returns safe, aggregated metrics dictionary for health diagnostics."""
        with cls._lock:
            uptime_seconds = round(time.time() - cls._start_time, 1)
            total_retrievals = cls._retrieval_success_count + cls._no_result_count
            retrieval_success_rate = (
                round((cls._retrieval_success_count / total_retrievals) * 100.0, 1)
                if total_retrievals > 0 else 100.0
            )
            avg_chunks = (
                round(cls._total_chunks_retrieved / cls._retrieval_success_count, 2)
                if cls._retrieval_success_count > 0 else 0.0
            )
            total_gemini = cls._gemini_success_count + cls._gemini_failure_count
            gemini_success_rate = (
                round((cls._gemini_success_count / total_gemini) * 100.0, 1)
                if total_gemini > 0 else 100.0
            )

            return {
                "uptime_seconds": uptime_seconds,
                "total_queries_processed": cls._total_queries,
                "retrieval_metrics": {
                    "success_count": cls._retrieval_success_count,
                    "no_result_count": cls._no_result_count,
                    "success_rate_percent": retrieval_success_rate,
                    "average_chunks_per_hit": avg_chunks,
                    "total_citations_generated": cls._citations_generated_count,
                },
                "provider_metrics": {
                    "gemini_successes": cls._gemini_success_count,
                    "gemini_failures": cls._gemini_failure_count,
                    "timeouts": cls._timeout_count,
                    "success_rate_percent": gemini_success_rate,
                    "fallbacks_served": cls._fallback_count,
                    "malformed_outputs_caught": cls._malformed_output_count,
                },
                "safety_and_rules": {
                    "prompt_injections_blocked": cls._prompt_injection_blocked_count,
                    "unauthorized_claims_intercepted": cls._unauthorized_claims_intercepted,
                    "deterministic_engine_invocations": cls._deterministic_engine_calls,
                },
                "status": "HEALTHY" if cls._gemini_failure_count <= cls._gemini_success_count else "DEGRADED"
            }

    @classmethod
    def reset_metrics_for_tests(cls) -> None:
        """Helper for test suites to reset counters cleanly."""
        with cls._lock:
            cls._total_queries = 0
            cls._retrieval_success_count = 0
            cls._no_result_count = 0
            cls._total_chunks_retrieved = 0
            cls._gemini_success_count = 0
            cls._gemini_failure_count = 0
            cls._timeout_count = 0
            cls._fallback_count = 0
            cls._malformed_output_count = 0
            cls._citations_generated_count = 0
            cls._prompt_injection_blocked_count = 0
            cls._deterministic_engine_calls = 0
            cls._unauthorized_claims_intercepted = 0
            cls._start_time = time.time()
