import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any
import jwt
from jwt import PyJWKClient, PyJWTError
import httpx
from fastapi import HTTPException, status
from app.core.config import settings

logger = logging.getLogger("yojnasetu.google_auth")

GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
GOOGLE_VALID_ISSUERS = ["accounts.google.com", "https://accounts.google.com"]

# Initialize cached JWKS client
_jwk_client: Optional[PyJWKClient] = None

def get_jwk_client() -> PyJWKClient:
    global _jwk_client
    if _jwk_client is None:
        _jwk_client = PyJWKClient(GOOGLE_JWKS_URL, cache_keys=True, max_cached_keys=10)
    return _jwk_client


@dataclass
class GoogleUserInfo:
    google_id: str
    email: str
    email_verified: bool
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None


def verify_google_id_token(id_token: str, client_id: Optional[str] = None) -> GoogleUserInfo:
    """
    Cryptographically verifies a Google ID token (JWT) using Google's public JWKS.
    Falls back to Google's tokeninfo endpoint if JWKS signature resolution encounters issues.
    Validates issuer, audience, expiration, and verified email status.
    """
    if not id_token or not isinstance(id_token, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google ID token is required."
        )

    id_token = id_token.strip()
    target_aud = client_id or settings.GOOGLE_CLIENT_ID
    payload: Optional[Dict[str, Any]] = None

    # 1. Primary Strategy: Fast, Local Cryptographic Verification via PyJWKClient (RS256)
    try:
        jwks_client = get_jwk_client()
        signing_key = jwks_client.get_signing_key_from_jwt(id_token)
        
        decode_kwargs = {
            "algorithms": ["RS256"],
            "options": {"verify_exp": True, "verify_iss": True},
        }
        if target_aud:
            decode_kwargs["audience"] = target_aud
        else:
            decode_kwargs["options"]["verify_aud"] = False

        payload = jwt.decode(
            id_token,
            signing_key.key,
            **decode_kwargs
        )

        # Validate issuer
        issuer = payload.get("iss", "")
        if issuer not in GOOGLE_VALID_ISSUERS:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google token issuer."
            )

    except PyJWTError as jwt_err:
        logger.warning(f"Local JWKS verification failed ({jwt_err}), falling back to tokeninfo verification.")
        payload = None
    except Exception as e:
        logger.warning(f"Local JWKS check error: {e}")
        payload = None

    # 2. Fallback / Secondary Verification Strategy: Google tokeninfo endpoint
    if payload is None:
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(GOOGLE_TOKENINFO_URL, params={"id_token": id_token})
                if resp.status_code == 200:
                    payload = resp.json()
                else:
                    error_detail = resp.json().get("error_description", "Invalid token")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=f"Google authentication failed: {error_detail}"
                    )
        except HTTPException:
            raise
        except Exception as net_err:
            logger.error(f"Failed to verify Google token via tokeninfo: {net_err}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to verify Google credentials with Google Identity Services."
            )

    # 3. Claims Validation & Policy Enforcement
    # Audience verification
    if target_aud and payload.get("aud") != target_aud:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google token audience does not match application client ID."
        )

    # Issuer verification
    if payload.get("iss") not in GOOGLE_VALID_ISSUERS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token issuer."
        )

    google_id = payload.get("sub")
    email = payload.get("email")
    email_verified = payload.get("email_verified")

    if not google_id or not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google ID token missing essential identity claims (sub, email)."
        )

    # Convert string email_verified if returned by tokeninfo as "true"
    if isinstance(email_verified, str):
        email_verified = email_verified.lower() == "true"

    if not email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your Google account email is not verified. Please verify your Google email first."
        )

    full_name = payload.get("name")
    avatar_url = payload.get("picture")

    return GoogleUserInfo(
        google_id=str(google_id),
        email=str(email).lower().strip(),
        email_verified=bool(email_verified),
        full_name=full_name,
        avatar_url=avatar_url
    )
