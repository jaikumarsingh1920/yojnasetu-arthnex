import re
import logging
from typing import Tuple

from app.ai.observability import RAGObservabilityTracker

logger = logging.getLogger("yojnasetu.ai.security")


class AISecurityGuard:
    """Security, Prompt Injection Resistance & Safety Layer for YojnaSetu AI components."""

    INJECTION_PATTERNS = [
        r"ignore\s+(?:all\s+)?(?:previous|prior|system)\s+instructions",
        r"disregard\s+(?:all\s+)?(?:prior|previous|system|safety|guardrail\s+)?rules",
        r"override\s+(?:system\s+|statutory\s+|eligibility\s+)?rules",
        r"you\s+are\s+now\s+(?:a|an|in)\s+(?:developer|dan|jailbreak|unrestricted|god|admin|root)",
        r"pretend\s+(?:i\s+am|to\s+be)\s+(?:an?\s+)?(?:admin|administrator|system\s+admin|root|superuser)",
        r"(?:print|reveal|show|dump|repeat|what\s+is)\s+(?:your\s+)?(?:system\s+)?(?:prompt|instructions|rules|guidelines)",
        r"(?:what\s+are\s+your\s+(?:system\s+)?instructions)",
        r"system\s*:\s*",
        r"grant\s+(?:instant\s+|automatic\s+)?approval",
        r"bypass\s+(?:statutory\s+|hard\s+)?eligibility",
        r"make\s+me\s+(?:statutorily\s+|legally\s+)?eligible",
        r"(?:change|modify|update|delete|drop)\s+(?:this\s+)?(?:scheme|database|table)",
        r"(?:tell\s+me|show\s+me|reveal)\s+(?:a\s+)?(?:hidden|internal|confidential)\s+(?:scheme|data|record)",
        r"use\s+(?:your\s+own|generic)\s+knowledge\s+instead\s+of\s+sources",
        r"(?:reveal|show|print|give|tell\s+me)(?:\s+(?:about|the|your))*\s+(?:api[\s_-]?key|secret|password|token)",
        r"(?:drop\s+table|delete\s+from|select\s+\*\s+from\s+users)",
    ]

    UNGROUNDED_ELIGIBILITY_PATTERNS = [
        r"\b(?:you\s+are\s+legally\s+eligible)\b",
        r"\b(?:you\s+are\s+definitively\s+eligible)\b",
        r"\b(?:i\s+declare\s+you\s+eligible)\b",
        r"\b(?:guaranteed\s+statutory\s+eligibility)\b",
        r"\b(?:you\s+are\s+100%\s+statutorily\s+eligible)\b",
    ]

    @classmethod
    def is_prompt_injection(cls, user_text: str) -> bool:
        """Returns True if the user input contains high-risk prompt injection attempts."""
        if not user_text:
            return False
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, user_text, re.IGNORECASE):
                RAGObservabilityTracker.record_prompt_injection_blocked()
                return True
        return False

    @classmethod
    def sanitize_user_input(cls, user_text: str) -> str:
        """Sanitizes user input by neutralizing injection attempts and wrapping in safety boundaries."""
        clean_text = user_text.strip() if user_text else ""

        # Check for known prompt injection attempts
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, clean_text, re.IGNORECASE):
                logger.warning("Prompt injection pattern detected and neutralized: %s", pattern)
                clean_text = re.sub(
                    pattern, "[NEUTRALIZED_PROMPT_INJECTION]", clean_text, flags=re.IGNORECASE
                )

        # Wrap in untrusted content boundary tags
        return f"<untrusted_content>{clean_text}</untrusted_content>"

    @classmethod
    def validate_factual_claims(cls, text: str, deterministic_used: bool = False) -> Tuple[str, bool]:
        """
        Validates post-generation model text against statutory eligibility hallucination.
        Ensures the AI never makes definitive statutory proclamations unless backed by deterministic engine.
        Returns: (sanitized_text, was_intercepted)
        """
        if not text:
            return text, False

        intercepted = False
        sanitized = text

        for pattern in cls.UNGROUNDED_ELIGIBILITY_PATTERNS:
            if re.search(pattern, sanitized, re.IGNORECASE):
                intercepted = True
                RAGObservabilityTracker.record_unauthorized_claim_intercepted()
                if not deterministic_used:
                    replacement = (
                        "You appear to match some preliminary criteria based on listed guidelines. "
                        "Please run YojnaSetu's deterministic eligibility check for statutory evaluation"
                    )
                else:
                    replacement = "Based on YojnaSetu's deterministic rule evaluation, you meet the listed criteria"
                sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)

        return sanitized, intercepted

    @classmethod
    def scrub_sensitive_logs(cls, text: str) -> str:
        """Scrubs API keys, passwords, and tokens from log messages."""
        text = re.sub(
            r"(api[_-]?key|password|token|secret)\s*[:=]\s*['\"][^'\"]+['\"]",
            r"\1=[REDACTED]",
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(r"Bearer\s+[A-Za-z0-9\-\._~\+\/]+=*", "Bearer [REDACTED]", text)
        return text

    @classmethod
    def scrub_output(cls, text: str) -> str:
        """Scrubs potential internal secrets or system prompt leaks from AI responses."""
        if not text:
            return ""
        scrubbed = str(text)
        # Redact any accidental API key or secret token matches
        scrubbed = re.sub(r"AIza[0-9A-Za-z-_]{35}", "[REDACTED_API_KEY]", scrubbed)
        scrubbed = re.sub(r"sk-[a-zA-Z0-9]{20,}", "[REDACTED_API_KEY]", scrubbed)
        # Redact database connection strings
        scrubbed = re.sub(r"postgresql://[^\s]+", "[REDACTED_DATABASE_URL]", scrubbed)
        scrubbed = re.sub(r"sqlite:///[^\s]+", "[REDACTED_DATABASE_URL]", scrubbed)
        return scrubbed


