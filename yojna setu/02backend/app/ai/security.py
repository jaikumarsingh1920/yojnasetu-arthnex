import re
import logging

logger = logging.getLogger("yojnasetu.ai.security")


class AISecurityGuard:
  """Security & Prompt Injection Resistance Layer for YojnaSetu AI components."""

  INJECTION_PATTERNS = [
      r"ignore\s+(?:all\s+)?previous\s+instructions",
      r"override\s+(?:system\s+)?rules",
      r"you\s+are\s+now\s+a",
      r"system\s*:\s*",
      r"grant\s+(?:instant\s+)?approval",
      r"bypass\s+eligibility",
      r"make\s+me\s+eligible",
  ]

  @classmethod
  def sanitize_user_input(cls, user_text: str) -> str:
    """Sanitizes user input by wrapping untrusted text and neutralizing injection attempts."""
    clean_text = user_text.strip()

    # Check for known prompt injection attempts
    for pattern in cls.INJECTION_PATTERNS:
      if re.search(pattern, clean_text, re.IGNORECASE):
        logger.warning(
            "Prompt injection pattern detected and neutralized: %s", pattern
        )
        clean_text = re.sub(
            pattern, "[NEUTRALIZED_PROMPT_INJECTION]", clean_text, flags=re.IGNORECASE
        )

    # Wrap in untrusted content boundary tags
    return f"<untrusted_content>{clean_text}</untrusted_content>"

  @classmethod
  def scrub_sensitive_logs(cls, text: str) -> str:
    """Scrubs API keys, passwords, and tokens from log messages."""
    text = re.sub(
        r"(api[_-]?key|password|token)\s*=\s*['\"][^'\"]+['\"]",
        r"\1=[REDACTED]",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"Bearer\s+[A-Za-z0-9\-\._~\+\/]+=*", "Bearer [REDACTED]", text)
    return text
