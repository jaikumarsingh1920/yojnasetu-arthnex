import ipaddress
import logging
import socket
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Tuple
from urllib.parse import urlparse
import httpx

logger = logging.getLogger("yojnasetu.ingestion.fetcher")

USER_AGENT = "YojnaSetu-GovDataSync/2.1 (+https://yojnasetu.gov.in; SIH-SmartAutomation)"
PARSER_VERSION = "2.1.0"
EXTRACTION_VERSION = "2.1.0"

# Approved official government and development agency domains
ALLOWED_GOV_DOMAINS = (
    ".gov.in",
    ".nic.in",
    "myscheme.gov.in",
    "sidbi.in",
    "nabard.org",
    "standupmitra.in",
    "cgtmse.in",
    "mudra.org.in",
    "rbi.org.in",
    "nhb.org.in",
    "coirboard.gov.in",
    "kvic.gov.in",
    "msme.gov.in",
    "pmegp.gov.in",
    "nsfdc.nic.in",
    "nbcfdc.gov.in",
    "nskfdc.nic.in",
    "tribal.nic.in",
    "socialjustice.gov.in",
    "digitalindia.gov.in",
    "india.gov.in",
    "startupindia.gov.in",
    "testserver.gov.in",
)

BLOCKED_IP_PREFIXES = (
    "127.",
    "10.",
    "172.16.",
    "172.17.",
    "172.18.",
    "172.19.",
    "172.20.",
    "172.21.",
    "172.22.",
    "172.23.",
    "172.24.",
    "172.25.",
    "172.26.",
    "172.27.",
    "172.28.",
    "172.29.",
    "172.30.",
    "172.31.",
    "192.168.",
    "169.254.",
    "0.0.0.0",
)


class URLSecurityValidator:
    """
    Validates URLs for Server-Side Request Forgery (SSRF) and security compliance.
    Rejects private networks, loopbacks, cloud metadata endpoints (169.254.169.254),
    and enforces an approved official government domain whitelist.
    """

    @classmethod
    def validate_url(cls, url: str, allow_custom_domain: bool = False) -> Tuple[bool, Optional[str]]:
        if not url or not isinstance(url, str):
            return False, "URL cannot be empty."

        clean_url = url.strip()
        try:
            parsed = urlparse(clean_url)
            if parsed.scheme.lower() not in ("http", "https"):
                return False, f"Unsupported protocol '{parsed.scheme}'. Only HTTP and HTTPS are permitted."

            host = parsed.hostname
            if not host:
                return False, "Invalid host format in URL."

            host_lower = host.lower()
            if host_lower in ("localhost", "127.0.0.1", "::1", "metadata.google.internal", "169.254.169.254"):
                return False, f"Access to private/loopback/cloud metadata host '{host}' is strictly prohibited."

            # Check IP prefixes
            for prefix in BLOCKED_IP_PREFIXES:
                if host_lower.startswith(prefix):
                    return False, f"Access to private/local IP range '{host}' is strictly prohibited."

            # Check if host is an IP address
            try:
                ip = ipaddress.ip_address(host)
                if ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local:
                    return False, f"Access to private IP '{host}' is strictly prohibited."
            except ValueError:
                pass  # Hostname, not IP

            # Check approved government domains unless explicitly overridden for controlled tests
            if not allow_custom_domain:
                is_allowed = any(host_lower == d or host_lower.endswith(d) for d in ALLOWED_GOV_DOMAINS)
                if not is_allowed:
                    return False, f"Domain '{host}' is not in the approved official government domain registry."

            return True, None

        except Exception as e:
            return False, f"URL security validation error: {str(e)}"


class DomainRateLimiter:
    """
    Per-domain rate limiter ensuring polite, non-disruptive access to official government servers.
    """
    _last_request_times: Dict[str, float] = {}

    @classmethod
    def throttle(cls, url: str, min_interval_seconds: float = 0.5) -> None:
        try:
            domain = urlparse(url).netloc.lower()
            now = time.time()
            last_time = cls._last_request_times.get(domain, 0.0)
            elapsed = now - last_time
            if elapsed < min_interval_seconds:
                sleep_needed = min_interval_seconds - elapsed
                time.sleep(sleep_needed)
            cls._last_request_times[domain] = time.time()
        except Exception:
            pass


@dataclass
class FetchResult:
    success: bool
    status_code: Optional[int]
    content: Optional[str]
    content_type: str
    content_bytes: Optional[bytes] = None
    error_message: Optional[str] = None
    parser_version: str = PARSER_VERSION
    extraction_version: str = EXTRACTION_VERSION
    fetch_timestamp: Optional[str] = None
    retries_attempted: int = 0


class BaseFetcher(ABC):
    @abstractmethod
    def fetch(self, url: str) -> FetchResult:
        """Fetches raw content from an external official government source."""
        pass


class HTMLFetcher(BaseFetcher):
    """
    HTTP Fetcher for official government HTML portals and guideline pages.
    Enforces SSRF validation, exponential backoff retries on transient errors,
    timeouts, user-agent identification, and rate limiting.
    """

    def __init__(
        self,
        timeout_seconds: float = 15.0,
        min_interval_seconds: float = 0.5,
        max_retries: int = 3,
        allow_custom_domain: bool = False
    ):
        self.timeout = timeout_seconds
        self.min_interval = min_interval_seconds
        self.max_retries = max_retries
        self.allow_custom_domain = allow_custom_domain

    def fetch(self, url: str) -> FetchResult:
        fetch_ts = datetime.utcnow().isoformat()
        is_safe, sec_err = URLSecurityValidator.validate_url(url, allow_custom_domain=self.allow_custom_domain)
        if not is_safe:
            logger.warning(f"SSRF violation rejected for URL: {url} - {sec_err}")
            return FetchResult(
                success=False,
                status_code=400,
                content=None,
                content_type="text/plain",
                error_message=f"SSRF Security Violation: {sec_err}",
                fetch_timestamp=fetch_ts
            )

        DomainRateLimiter.throttle(url, min_interval_seconds=self.min_interval)

        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
        }

        retries = 0
        backoff_delay = 0.5

        while retries <= self.max_retries:
            try:
                with httpx.Client(timeout=self.timeout, follow_redirects=True, headers=headers) as client:
                    response = client.get(url)
                    status_code = response.status_code
                    content_type = response.headers.get("content-type", "text/html")

                    if response.is_success:
                        return FetchResult(
                            success=True,
                            status_code=status_code,
                            content=response.text,
                            content_type=content_type,
                            content_bytes=response.content,
                            error_message=None,
                            fetch_timestamp=fetch_ts,
                            retries_attempted=retries
                        )

                    # Check for retryable transient server errors
                    if status_code in (408, 429, 500, 502, 503, 504) and retries < self.max_retries:
                        retries += 1
                        time.sleep(backoff_delay)
                        backoff_delay *= 2.0
                        continue

                    return FetchResult(
                        success=False,
                        status_code=status_code,
                        content=None,
                        content_type=content_type,
                        error_message=f"HTTP {status_code}: {response.reason_phrase}",
                        fetch_timestamp=fetch_ts,
                        retries_attempted=retries
                    )

            except httpx.TimeoutException as te:
                if retries < self.max_retries:
                    retries += 1
                    time.sleep(backoff_delay)
                    backoff_delay *= 2.0
                    continue
                return FetchResult(
                    success=False,
                    status_code=None,
                    content=None,
                    content_type="text/plain",
                    error_message=f"Connection timed out after {self.timeout}s: {str(te)}",
                    fetch_timestamp=fetch_ts,
                    retries_attempted=retries
                )

            except httpx.ConnectError as ce:
                if retries < self.max_retries:
                    retries += 1
                    time.sleep(backoff_delay)
                    backoff_delay *= 2.0
                    continue
                return FetchResult(
                    success=False,
                    status_code=None,
                    content=None,
                    content_type="text/plain",
                    error_message=f"Failed to establish connection: {str(ce)}",
                    fetch_timestamp=fetch_ts,
                    retries_attempted=retries
                )

            except Exception as exc:
                return FetchResult(
                    success=False,
                    status_code=None,
                    content=None,
                    content_type="text/plain",
                    error_message=f"Fetch execution failed: {str(exc)}",
                    fetch_timestamp=fetch_ts,
                    retries_attempted=retries
                )

        return FetchResult(
            success=False,
            status_code=None,
            content=None,
            content_type="text/plain",
            error_message="Maximum retry attempts exhausted.",
            fetch_timestamp=fetch_ts,
            retries_attempted=retries
        )


class PDFFetcher(BaseFetcher):
    """
    Binary PDF Fetcher for official government scheme guideline documents,
    gazette notifications, and operational circulars.
    Enforces SSRF validation, binary validation, and retry with exponential backoff.
    """

    def __init__(
        self,
        timeout_seconds: float = 30.0,
        min_interval_seconds: float = 0.5,
        max_retries: int = 3,
        allow_custom_domain: bool = False
    ):
        self.timeout = timeout_seconds
        self.min_interval = min_interval_seconds
        self.max_retries = max_retries
        self.allow_custom_domain = allow_custom_domain

    def fetch(self, url: str) -> FetchResult:
        fetch_ts = datetime.utcnow().isoformat()
        is_safe, sec_err = URLSecurityValidator.validate_url(url, allow_custom_domain=self.allow_custom_domain)
        if not is_safe:
            logger.warning(f"SSRF violation rejected for PDF URL: {url} - {sec_err}")
            return FetchResult(
                success=False,
                status_code=400,
                content=None,
                content_type="application/pdf",
                error_message=f"SSRF Security Violation: {sec_err}",
                fetch_timestamp=fetch_ts
            )

        DomainRateLimiter.throttle(url, min_interval_seconds=self.min_interval)

        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/pdf,*/*",
        }

        retries = 0
        backoff_delay = 0.5

        while retries <= self.max_retries:
            try:
                with httpx.Client(timeout=self.timeout, follow_redirects=True, headers=headers) as client:
                    response = client.get(url)
                    status_code = response.status_code
                    content_type = response.headers.get("content-type", "application/pdf")

                    if response.is_success:
                        raw_bytes = response.content
                        if not raw_bytes.startswith(b"%PDF"):
                            return FetchResult(
                                success=False,
                                status_code=status_code,
                                content=None,
                                content_type=content_type,
                                content_bytes=raw_bytes,
                                error_message="Malformed Document: Resource response does not contain valid %PDF magic header.",
                                fetch_timestamp=fetch_ts,
                                retries_attempted=retries
                            )

                        return FetchResult(
                            success=True,
                            status_code=status_code,
                            content=None,
                            content_type="application/pdf",
                            content_bytes=raw_bytes,
                            error_message=None,
                            fetch_timestamp=fetch_ts,
                            retries_attempted=retries
                        )

                    if status_code in (408, 429, 500, 502, 503, 504) and retries < self.max_retries:
                        retries += 1
                        time.sleep(backoff_delay)
                        backoff_delay *= 2.0
                        continue

                    return FetchResult(
                        success=False,
                        status_code=status_code,
                        content=None,
                        content_type=content_type,
                        error_message=f"HTTP {status_code}: {response.reason_phrase}",
                        fetch_timestamp=fetch_ts,
                        retries_attempted=retries
                    )

            except httpx.TimeoutException as te:
                if retries < self.max_retries:
                    retries += 1
                    time.sleep(backoff_delay)
                    backoff_delay *= 2.0
                    continue
                return FetchResult(
                    success=False,
                    status_code=None,
                    content=None,
                    content_type="application/pdf",
                    error_message=f"PDF download timed out after {self.timeout}s: {str(te)}",
                    fetch_timestamp=fetch_ts,
                    retries_attempted=retries
                )

            except Exception as exc:
                return FetchResult(
                    success=False,
                    status_code=None,
                    content=None,
                    content_type="application/pdf",
                    error_message=f"PDF download failed: {str(exc)}",
                    fetch_timestamp=fetch_ts,
                    retries_attempted=retries
                )

        return FetchResult(
            success=False,
            status_code=None,
            content=None,
            content_type="application/pdf",
            error_message="Maximum retry attempts exhausted.",
            fetch_timestamp=fetch_ts,
            retries_attempted=retries
        )
